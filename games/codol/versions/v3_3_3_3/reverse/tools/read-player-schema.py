"""Read only the known CODOL player schemas/rank tables from its live process.

No process writes, injection, debug privilege adjustment, or arbitrary addresses.
Address evidence: REA controller-stat-lookup.json / controller-stat-context.json.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[6]
GAME = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
SHA256 = 'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b'
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                     ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                            wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]


def capture(pid, image_base, marketplace=False, weapon_progression=False, pve=False, commands=False, netconst=False, weapon_models=False):
    handle = kernel.OpenProcess(0x1010, False, pid)  # QUERY_LIMITED_INFORMATION | VM_READ
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        image = ctypes.create_unicode_buffer(32768)
        size = wintypes.DWORD(len(image))
        if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        if Path(image.value).resolve() != GAME.resolve() or hashlib.sha256(GAME.read_bytes()).hexdigest() != SHA256:
            raise ValueError('The process must be the verified CODOL 3.3.3.3 client')

        def read(address, length):
            if not 0 < length <= 4 * 1024 * 1024:
                raise ValueError('Read exceeds the bounded schema size')
            buffer = ctypes.create_string_buffer(length)
            actual = ctypes.c_size_t()
            if not kernel.ReadProcessMemory(handle, address, buffer, length, ctypes.byref(actual)) or actual.value != length:
                raise ctypes.WinError(ctypes.get_last_error())
            return buffer.raw

        def words(address, count):
            return list(struct.unpack('<' + 'I' * count, read(address, count * 4)))

        def string(address):
            return read(address, 256).split(b'\0', 1)[0].decode('utf-8', errors='replace')

        if read(image_base, 2) != b'MZ':
            raise ValueError('Unexpected module base')

        if netconst:
            from story_netconst423 import read_registration
            result = read_registration(read, image_base)
            result.update(exe_sha256=SHA256, pid=pid, image_base=image_base,
                          scope='Network registration names and checksum only; no map-ready claim')
            output = ROOT / 'research/evidence/live-netconst-registration423.json'
            output.write_text(json.dumps(result, indent=2), encoding='utf-8')
            print(output)
            return

        if commands:
            # REA 0x6ece70: cmd_function_s is next/name/callback; read only.
            node = words(image_base + 0x2e01224 - 0x400000, 1)[0]
            entries, visited = [], set()
            while node:
                if node in visited or len(visited) >= 4096:
                    raise ValueError('Unexpected command registry chain')
                visited.add(node)
                following, name, callback = words(node, 3)
                entries.append({'name': string(name), 'callback': callback,
                                'static_callback': callback - image_base + 0x400000 if callback else 0})
                node = following
            output = ROOT / 'research/evidence/live-console-commands.json'
            output.write_text(json.dumps({'exe_sha256': SHA256, 'pid': pid, 'image_base': image_base,
                                          'commands': entries}, indent=2), encoding='utf-8')
            print(output)
            return

        def asset(kind, name):
            key = kind
            for byte in name.lower().replace('\\', '/').encode():
                key = (key * 31 + byte) & 0xffffffff
            index = words(image_base + 0x1bc9f20 - 0x400000 + (key % 80000) * 4, 1)[0]
            visited = set()
            while index and index not in visited and len(visited) < 1000:
                visited.add(index)
                entry = words(image_base + 0x1fc4e28 - 0x400000 + index * 28, 7)
                if entry[0] == kind and string(words(entry[2], 1)[0]).lower() == name.lower():
                    return entry[2]
                index = entry[5]
            raise ValueError('Loaded asset not found: ' + name)

        result = {'exe_sha256': SHA256, 'pid': pid, 'image_base': image_base, 'schemas': {}, 'tables': {}}
        for name in (() if marketplace or weapon_progression or pve or weapon_models else ('mp/playerdata.def', 'mp/playersecuredata.def')):
            address = asset(0x27, name)
            asset_header = words(address, 3)
            definition = asset_header[2]
            header = words(definition, 16)
            if header[4] > 2000 or header[6] > 2000 or header[10] != 5:
                raise ValueError('Unexpected structured data definition')
            structs = []
            for i in range(header[4]):
                item = words(header[5] + i * 20, 5)
                if item[0] > 5000:
                    raise ValueError('Unexpected property count')
                properties = []
                for j in range(item[0]):
                    prop = words(item[1] + j * 24, 6)
                    properties.append({'name': string(prop[0]), 'type': prop[1], 'type_index': prop[2],
                                       'slot': prop[3], 'flags': prop[4], 'extra': prop[5]})
                structs.append({'header': item, 'properties': properties})
            slots = structs[header[11]]['header'][4]
            if not 0 < slots <= 100000:
                raise ValueError('Unexpected offset table size')
            result['schemas'][name] = {'asset_header': asset_header, 'header': header, 'structs': structs,
                                      'arrays': [words(header[7] + i * 16, 4) for i in range(header[6])],
                                      'offsets': words(header[14], slots)}
        tables = ('mp/unlockFlags.csv', 'mp/coMarketplaceItems.csv') if marketplace else ('mp/rankTable.csv', 'mp/prestigeTable.csv')
        if weapon_progression:
            tables = ('mp/coWeaponPrimaryRankTable.csv', 'mp/coWeaponSecondaryRankTable.csv')
        if pve:
            tables = ('mp/coMapList.csv', 'mp/coGameTypesTable.csv')
        if weapon_models:
            tables = ('mp/coweapmodels/acr_mp.csv', 'mp/coweapitemswea.csv',
                      'mp/coWeaponAttachmentTable.csv',
                      *(f'mp/coweapitems/{group}.csv' for group in ('muz', 'sto', 'gri', 'mag', 'iro')))
        for name in tables:
            header = words(asset(0x25, name), 4)
            columns, rows, cells = header[1:]
            if not 0 < columns * rows <= 500000:
                raise ValueError('Unexpected rank table size')
            result['tables'][name] = [[string(words(cells + (row * columns + col) * 8, 1)[0])
                                      for col in range(columns)] for row in range(rows)]
            if weapon_models and name.startswith('mp/coweapitems/'):
                result['tables'][name] = [row for row in result['tables'][name] if row[1] == 'acr_mp']
        if weapon_models:
            # 0x42e44d consumes these 14-bit name slots, not marketplace ordinals.
            result['attachment_slots'] = {
                index: string(words(image_base + 0x17e5848 - 0x400000 + index * 4, 1)[0])
                for index in (1690, 2683, 2385, 9641, 13370)
            }
            result['models'] = {}
            for name in ('viewhands_player_tf141', 'viewhands_tf141',
                         'wea_acr_acr_blk', 'wea_acr_acr_blk_vmgun'):
                pointer = asset(4, name)
                header = read(pointer, 0x48)
                bones, roots = header[4:6]
                names, parents, quaternions, translations, _, matrices = struct.unpack_from('<6I', header, 0x2c)
                result['models'][name] = dict(address=pointer, bones=bones, roots=roots,
                    translation_scale=struct.unpack_from('<f', header, 8)[0],
                    bone_ids=list(struct.unpack('<'+'H'*bones, read(names, 2*bones))),
                    parents=list(read(parents, bones-roots)),
                    local_quaternions=list(struct.iter_unpack('<4h', read(quaternions, 8*(bones-roots)))),
                    local_translations=list(struct.iter_unpack('<3f', read(translations, 12*(bones-roots)))),
                    bind_matrices=[list(struct.unpack('<8f', read(matrices+32*i, 32))) for i in range(bones)])
        if marketplace:
            # REA 0x5840a0 / 0x7070b0: read the loaded catalogue, never execute game code.
            def global_words(address, count):
                return words(image_base + address - 0x400000, count)
            result['catalogue'] = {}
            for label, address, stride in (('items', 0x2db8ac4, 40), ('products', 0x2dbb270, 24), ('skus', 0x2dbb288, 24), ('requirements', 0x2db8ab4, 8)):
                pointer, count = global_words(address, 2)
                if not 0 < count <= 65536:
                    raise ValueError('Unexpected catalogue size: ' + label)
                result['catalogue'][label] = {'address': pointer, 'count': count, 'stride': stride, 'hex': read(pointer, count * stride).hex()}
                if label == 'products':
                    # 0x706ed0 / 0x706f10: byte count at +10, uint16 item + byte quantity, stride 4.
                    entries = []
                    for i in range(count):
                        record = read(pointer + i * stride, stride)
                        item_count = record[10]
                        item_pointer = struct.unpack_from('<I', record, 12)[0]
                        entries.append(read(item_pointer, item_count * 4).hex() if item_count else '')
                    result['catalogue'][label]['items'] = entries
                if label == 'requirements':
                    names = [words(pointer + i * stride + 4, 1)[0] for i in range(count)]
                    result['catalogue'][label]['names'] = [string(name) if name else '' for name in names]
            result['catalogue']['sku_keys'] = global_words(0xcdd57c, 9)
            result['catalogue']['item_key'] = global_words(0xcdd5a0, 1)[0]
        output = ROOT / ('research/evidence/live-marketplace.json' if marketplace else 'research/evidence/live-player-schema.json')
        if weapon_progression:
            output = ROOT / 'research/evidence/live-weapon-progression.json'
        if pve:
            output = ROOT / 'research/evidence/live-pve-tables.json'
        if weapon_models:
            output = ROOT / 'research/evidence/live-acr-models.json'
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(output)
    finally:
        kernel.CloseHandle(handle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--base', type=int, required=True)
    parser.add_argument('--marketplace', action='store_true', help='Read only unlock/item tables and the loaded marketplace catalogue')
    parser.add_argument('--weapon-progression', action='store_true', help='Read only the primary and secondary weapon rank tables')
    parser.add_argument('--pve', action='store_true', help='Read only the map and game type tables')
    parser.add_argument('--commands', action='store_true', help='Read only the registered console command names and callbacks')
    parser.add_argument('--netconst', action='store_true', help='Read only network registration names and verify their CRC seed')
    parser.add_argument('--weapon-models', action='store_true', help='Read only ACR model recipes and default weapon parts')
    args = parser.parse_args()
    if sum((args.marketplace, args.weapon_progression, args.pve, args.commands, args.netconst, args.weapon_models)) > 1:
        parser.error('Choose one bounded capture scope')
    capture(args.pid, args.base, args.marketplace, args.weapon_progression, args.pve, args.commands, args.netconst, args.weapon_models)
