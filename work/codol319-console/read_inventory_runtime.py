"""Bounded read-only inspection of the current isolated client's inventory."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import struct
import sys
import traceback

OUT = Path(__file__).resolve().parent
GAME = OUT.parents[1] / 'runtime/instances/codol-3.19.26.22-911c42a0027c/game/codoMP_client_shipRetail.exe'
SHA = '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537'
PID = int(sys.argv[1])
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
        name, length = c.create_unicode_buffer(32768), w.DWORD(32768)
        if not k.QueryFullProcessImageNameW(h, 0, name, c.byref(length)): raise c.WinError(c.get_last_error())
        if Path(name.value).resolve() != GAME.resolve() or hashlib.sha256(GAME.read_bytes()).hexdigest() != SHA:
            raise ValueError('Unexpected client identity')
        modules, needed = (w.HMODULE * 1024)(), w.DWORD()
        if not k.K32EnumProcessModulesEx(h, modules, c.sizeof(modules), c.byref(needed), 3): raise c.WinError(c.get_last_error())
        base, ranges = modules[0], []
        def read(address, size):
            if not 0 < size <= 4 * 1024 * 1024: raise ValueError('Unbounded read')
            buf, actual = c.create_string_buffer(size), c.c_size_t()
            if not k.ReadProcessMemory(h, address, buf, size, c.byref(actual)) or actual.value != size:
                raise c.WinError(c.get_last_error())
            ranges.append([hex(address), size])
            return buf.raw
        def static(va): return base + va - 0x400000
        def words(address, count): return list(struct.unpack('<' + 'I' * count, read(address, count * 4)))
        reference = (OUT / 'analysis-client319.exe').read_bytes()
        if read(static(0xb87c00), 64) != reference[0x787c00:0x787c40]: raise ValueError('Consumer code changed')
        header = words(static(0x88aa2b8), 64)
        vtables = {hex(header[i]): words(header[i], 10) for i in (0, 2)}
        count = words(static(0x82c4a8c), 1)[0]
        if count > 20000: raise ValueError('Inventory count out of known bounds')
        assets = words(static(0x88aa2b8+0x368), 4)
        inventory = read(static(0x88ba0d8), max(count, 1) * 0xb8)
        ids = [struct.unpack_from('<I', inventory, i*0xb8+0x40)[0] for i in range(count)]
        owned = json.loads((GAME.parent.parent/'server/local-profiles319/owned_items.json').read_text())
        invalid = []
        for i in range(count):
            offset = i*0xb8
            values = [struct.unpack_from(fmt,inventory,offset+pos)[0] for pos,fmt in
                      [(0x30,'<Q'),(0x44,'<I'),(0x90,'<I'),(0x98,'<q'),(0xa4,'<I')]]
            if values != [1000001,1,0xffffffff,0x7fffffffffffffff,0xffffffff]: invalid.append(i)
        first = inventory[:min(max(count,1),3)*0xb8].hex()
        result = {'version': '3.19.26.22', 'exe_sha256': SHA, 'pid': PID, 'base': hex(base),
                  'assets_address': hex(static(0x88aa2b8)), 'header': header, 'vtables': vtables,
                  'inventory_count': count, 'first_items_hex': first, 'read_ranges': ranges,
                  'asset_inventory': assets, 'first_ids': ids[:3], 'last_ids': ids[-3:],
                  'matches_owned_prefix': ids == owned[:count], 'invalid_fields': invalid,
                  'inventory_sha256': hashlib.sha256(inventory).hexdigest(),
                  'source': 'ReadProcessMemory; 0x4a713c assets result, 0x4a76c0 inventory copy/count',
                  'unverified': 'GUI item visibility; full packet replay'}
        (OUT / f'inventory-live-{PID}.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    finally:
        k.CloseHandle(h)

try:
    capture()
except Exception:
    (OUT / f'inventory-live-{PID}.error.txt').write_text(traceback.format_exc(), encoding='utf-8')
    raise
