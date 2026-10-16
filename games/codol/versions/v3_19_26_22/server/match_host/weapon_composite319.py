"""Composite weapon strings for a loadout gun, as the 3.19 client builds them (0061A2C0):

    ** <base weapon> <camo> 0 <part> <part> ...

For each of the 15 part slots the client takes the part item fitted in that slot (the loadout's
attachment) or else the weapon item's default part (item extension entry +0x26..+0x42), turns
the part item's name into a part number (0042F650: slot of the name in the part hash table at
0x1978640) and appends them in slot order; with no scope but an iron-sight slot it adds sco_none.
The client then builds the model from mp/coWeapModels/<base>.csv (00431810 -> 00430F40).

Data: ../weapon-parts319.txt (proxy DUMPPARTS: "part <number> <name>", "item <id> <name> <ext>
<15 default part item ids>") and ../item-ids319.txt ("<id> <index> <name>").
"""
import os
from pathlib import Path

ROOT = Path(os.environ['CODOL319_SERVER_ROOT'])
SCOPE_SLOT = 2          # empty by default; the client's sco_none rule tests this slot (record +0x28)
IRON_SLOT = 9           # iro_default; with no scope fitted the client adds sco_none
_cache = {}


def _load():
    if _cache:
        return _cache
    parts, items, names = {}, {}, {}
    for line in (ROOT / 'weapon-parts319.txt').read_text(encoding='latin-1').splitlines():
        f = line.split()
        if f[0] == 'part' and len(f) >= 3:
            parts.setdefault(f[2], int(f[1]))
        elif f[0] == 'item' and len(f) >= 19:
            items[int(f[1])] = (f[2], [int(v) for v in f[4:19]])
    for line in (ROOT / 'item-ids319.txt').read_text(encoding='latin-1').splitlines()[1:]:
        f = line.split()
        if len(f) >= 3 and f[0].isdigit():
            names[int(f[0])] = f[2]
    # Part-name prefix -> slot, learned from every weapon's default parts (sto_ 0, rai_ 1, ...).
    prefix_slot = {}
    for _, defaults in items.values():
        for slot, item in enumerate(defaults):
            if item and item in names:
                prefix_slot.setdefault(names[item].split('_', 1)[0], slot)
    _cache.update(parts=parts, items=items, names=names, prefix_slot=prefix_slot)
    return _cache


def slot_of(part_name):
    """Slot of a part item by its name prefix; scopes (never a default part) go to SCOPE_SLOT."""
    return _load()['prefix_slot'].get(part_name.split('_', 1)[0], SCOPE_SLOT)


def compose(weapon_item, attachment_items=(), camo=0):
    """(part numbers, part names) for a weapon item with the given attachment item ids, or None
    when the weapon item or a part is unknown."""
    d = _load()
    if weapon_item not in d['items']:
        return None
    slots = list(d['items'][weapon_item][1])
    for item in attachment_items:
        name = d['names'].get(item)
        if item and name:
            slots[slot_of(name)] = item
    numbers, used = [], []
    for item in slots:
        if not item:
            continue
        name = d['names'].get(item)
        if name is None or name not in d['parts']:
            return None
        numbers.append(d['parts'][name])
        used.append(name)
    if not slots[SCOPE_SLOT] and slots[IRON_SLOT] and 'sco_none' in d['parts']:
        numbers.append(d['parts']['sco_none'])
        used.append('sco_none')
    return numbers[:15], used[:15]


if __name__ == '__main__':
    import sys
    weapon = int(sys.argv[1]) if len(sys.argv) > 1 else 10001
    attach = [int(v) for v in sys.argv[2:]] or [25035, 22142]
    print(compose(weapon, attach))
    print('prefix slots', sorted(_load()['prefix_slot'].items(), key=lambda kv: kv[1]))
