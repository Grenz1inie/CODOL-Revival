"""Custom classes (loadouts) in the 3.19 public player data (mp/playerdata.def).

Def resolved from the current client's asset registry (struct count +0x10, structs +0x14, arrays +0x1C, size +0x30,
index count +0x34, offsets table +0x38). Root member weaponClasses (index 1607) is array 8 =
60 x struct 2 {characterIndex 0, deathstreak 1, killstreaks[4] 2, lethal 6, meleeWpn 8,
perks[6] 10, primaryAttach[6] 16, primaryBase 22, secondaryAttach[6] 23, secondaryBase 29,
special 30, tactical 32, wildcards[3] 34}, 37 indices per class. Values are item ids
(item-ids319.txt: 10001 = m4_mp). The data block is the 0x8000-byte profile after its CRC.

client.resource_export publishes playerdata_classes319.json; classes() reads a profile with it.
"""
import json
import struct
import os
from pathlib import Path

H = Path(os.environ['CODOL319_SERVER_ROOT']) / 'match-host'
OUT = H / 'playerdata_classes319.json'


def classes(data):
    """data: profile bytes after the 4-byte CRC. Returns 60 dicts of item ids."""
    layout = json.loads(OUT.read_text(encoding='utf-8'))['classes']
    i32 = lambda o: struct.unpack_from('<i', data, o)[0]
    out = []
    for c in layout:
        out.append({k: ([i32(o) for o in v] if isinstance(v, list) else
                        (struct.unpack_from('<h', data, v)[0] if k == 'character' else i32(v)))
                    for k, v in c.items()})
    return out


_names = None


def weapon_index(item_id):
    """Item id -> runtime weapon number (weapons319.txt) via the item name (item-ids319.txt)."""
    global _names
    if _names is None:
        items = {}
        for line in (H.parent / 'item-ids319.txt').read_text(encoding='utf-8').splitlines():
            f = line.split()
            if len(f) >= 3 and f[0].isdigit():
                items[int(f[0])] = f[2]
        weapons = {}
        for line in (H / 'weapons319.txt').read_text(encoding='utf-8').splitlines():
            f = line.split()
            if len(f) >= 2 and f[0].isdigit():
                weapons[f[1]] = int(f[0])
        _names = (items, weapons)
    items, weapons = _names
    name = items.get(item_id)
    return weapons.get(name), name
