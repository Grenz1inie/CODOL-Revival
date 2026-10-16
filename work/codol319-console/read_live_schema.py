"""Read-only, bounded 3.19 profile/table extraction. No writes or injected code in game."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import struct
import traceback

OUT = Path(__file__).resolve().parent
GAME = OUT.parents[1] / 'runtime/instances/codol-3.19.26.22-911c42a0027c/game/codoMP_client_shipRetail.exe'
SHA = '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537'
PID = 44184
k = c.WinDLL('kernel32', use_last_error=True)
k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
k.OpenProcess.restype = w.HANDLE
k.CloseHandle.argtypes = [w.HANDLE]
k.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
k.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.POINTER(c.c_size_t)]
k.K32EnumProcessModulesEx.argtypes = [w.HANDLE, c.POINTER(w.HMODULE), w.DWORD, c.POINTER(w.DWORD), w.DWORD]


def capture():
    h = k.OpenProcess(0x410, False, PID)
    if not h: raise c.WinError(c.get_last_error())
    try:
        name = c.create_unicode_buffer(32768)
        length = w.DWORD(len(name))
        if not k.QueryFullProcessImageNameW(h, 0, name, c.byref(length)): raise c.WinError(c.get_last_error())
        if Path(name.value).resolve() != GAME.resolve() or hashlib.sha256(GAME.read_bytes()).hexdigest() != SHA:
            raise ValueError('Unexpected client identity')
        modules = (w.HMODULE * 1024)()
        needed = w.DWORD()
        if not k.K32EnumProcessModulesEx(h, modules, c.sizeof(modules), c.byref(needed), 3): raise c.WinError(c.get_last_error())
        base = modules[0]
        ranges = []
        def read(address, size):
            if not 0 < size <= 4 * 1024 * 1024: raise ValueError('Unbounded read')
            buffer = c.create_string_buffer(size)
            actual = c.c_size_t()
            if not k.ReadProcessMemory(h, address, buffer, size, c.byref(actual)) or actual.value != size:
                raise c.WinError(c.get_last_error())
            ranges.append([hex(address), size])
            return buffer.raw
        def words(address, n): return list(struct.unpack('<' + 'I' * n, read(address, n * 4)))
        def string(address): return read(address, 256).split(b'\0')[0].decode('utf-8', errors='replace')
        def static(address): return base + address - 0x400000
        if read(base, 2) != b'MZ': raise ValueError('Not image base')
        expected = (GAME.parent / 'code319-44184-stage6-text-00401000.bin').read_bytes()
        for va in (0x49c870, 0x49ca70, 0x50f2c0):
            if read(static(va), 64) != expected[va - 0x401000:va - 0x401000 + 64]:
                raise ValueError('Consumer code changed')
        def asset(kind, name):
            key = kind
            for b in name.lower().replace('\\', '/').encode(): key = (key * 31 + b) & 0xffffffff
            index = words(static(0x1e2d338) + (key % 120000) * 4, 1)[0]
            visited = set()
            while index and index not in visited and len(visited) < 1000:
                visited.add(index)
                entry = words(static(0x239b120) + index * 28, 7)
                if entry[0] == kind and string(words(entry[2], 1)[0]).lower() == name.lower(): return entry[2]
                index = entry[5]
            raise ValueError('Loaded asset not found: ' + name)
        result = {'version': '3.19.26.22', 'exe_sha256': SHA, 'pid': PID, 'image_base': hex(base),
                  'source': 'ReadProcessMemory; DB lookup 0x49c870/0x49ca70; DDL consumer 0x50f2c0',
                  'schemas': {}, 'tables': {}, 'unverified': 'Client UI application; protocol replay'}
        for name in ('mp/playerdata.def', 'mp/playersecuredata.def'):
            pointer = asset(0x27, name)
            asset_header = words(pointer, 3)
            header = words(asset_header[2], 16)
            if not 0 < header[4] <= 2000 or header[6] > 2000 or header[10] != 5: raise ValueError('DDL header')
            structs = []
            for i in range(header[4]):
                item = words(header[5] + i * 20, 5)
                if not 0 <= item[0] <= 5000: raise ValueError('Property count')
                props = []
                for j in range(item[0]):
                    p = words(item[1] + j * 24, 6)
                    props.append({'name': string(p[0]), 'type': p[1], 'type_index': p[2], 'slot': p[3], 'flags': p[4], 'extra': p[5]})
                structs.append({'header': item, 'properties': props})
            slots = structs[header[11]]['header'][4]
            if not 0 < slots <= 100000: raise ValueError('Slot count')
            result['schemas'][name] = {'address': hex(pointer), 'asset_header': asset_header, 'header': header,
                'structs': structs, 'arrays': [words(header[7] + i * 16, 4) for i in range(header[6])],
                'offsets': words(header[14], slots)}
        for name in ('mp/rankTable.csv', 'mp/prestigeTable.csv', 'mp/unlockFlags.csv', 'mp/coMapList.csv',
                     'mp/coWeaponPrimaryRankTable.csv', 'mp/coWeaponSecondaryRankTable.csv'):
            try:
                pointer = asset(0x25, name)
            except ValueError as error:
                result['tables'][name] = {'unavailable': str(error)}
                continue
            header = words(pointer, 4)
            cols, rows, cells = header[1:]
            if not 0 < cols * rows <= 500000: raise ValueError('Table count')
            values = words(cells, cols * rows * 2)
            result['tables'][name] = {'address': hex(pointer), 'rows':
                [[string(values[(r * cols + col) * 2]) for col in range(cols)] for r in range(rows)]}
        result['read_ranges'] = ranges
        (OUT / 'live-schema319.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    finally:
        k.CloseHandle(h)


try:
    capture()
except Exception:
    (OUT / 'live-schema319.error.txt').write_text(traceback.format_exc(), encoding='utf-8')
