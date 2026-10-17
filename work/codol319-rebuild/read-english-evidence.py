"""Read-only resource evidence from the identified, already running client."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import struct
import traceback

OUT = Path(__file__).resolve().parent
GAME = OUT.parents[1] / 'runtime/instances/codol-3.19.26.22-911c42a0027c/game/codoMP_client_shipRetail.exe'
k = c.WinDLL('kernel32', use_last_error=True)
k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
k.OpenProcess.restype = w.HANDLE
k.CloseHandle.argtypes = [w.HANDLE]
k.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
k.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.POINTER(c.c_size_t)]

def capture():
    h = k.OpenProcess(0x410, False, 47740)
    if not h: raise c.WinError(c.get_last_error())
    records = {}
    try:
        name, size = c.create_unicode_buffer(32768), w.DWORD(32768)
        if not k.QueryFullProcessImageNameW(h, 0, name, c.byref(size)): raise c.WinError(c.get_last_error())
        assert Path(name.value).resolve() == GAME.resolve()
        assert hashlib.sha256(GAME.read_bytes()).hexdigest() == '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537'
        def read(va, n):
            assert 0 < n <= 16 * 1024 * 1024
            buf, actual = c.create_string_buffer(n), c.c_size_t()
            if not k.ReadProcessMemory(h, va, buf, n, c.byref(actual)) or actual.value != n:
                raise c.WinError(c.get_last_error())
            records[(va, n)] = buf.raw
            return buf.raw
        def words(va, n=1): return struct.unpack('<'+'I'*n, read(va, n*4))
        def string(va): return read(va, 256).split(b'\0')[0].decode('gb18030', errors='replace')
        assert read(0x400000, 2) == b'MZ'
        result, seen = {}, set()
        for index in words(0x1e2d338, 120000):
            while index and index not in seen:
                assert 0 < index < 150000
                seen.add(index)
                entry = words(0x239b120 + index * 28, 7)
                if entry[0] == 27:
                    value, name = words(entry[2], 2)
                    label = read(name,256).split(b'\0')[0].decode('ascii')
                    text = bytearray()
                    for offset in range(0,65536,128):
                        block=read(value+offset,128)
                        text.extend(block.split(b'\0')[0])
                        if b'\0' in block:break
                    else:raise ValueError('Unterminated localization')
                    result[label]=text.decode('gb18030')
                index=entry[5]
        (OUT/'english-loaded.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:k.CloseHandle(h)

try:capture()
except Exception:(OUT/'english-loaded.error.txt').write_text(traceback.format_exc(),encoding='utf-8')
