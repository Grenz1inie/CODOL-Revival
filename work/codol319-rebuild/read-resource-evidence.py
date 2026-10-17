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
        assets, seen = [], set()
        for index in words(0x1e2d338, 120000):
            while index and index not in seen:
                assert 0 < index < 150000
                seen.add(index)
                entry = words(0x239b120 + index * 28, 7)
                if entry[0] in (0x24, 0x25, 0x27, 44, 14):
                    data = words(entry[2], 4)
                    label = string(data[0])
                    assets.append([entry[0], label, entry[2], data])
                    if entry[0] == 0x25 and label.lower() == 'mp/ranktable.csv':
                        cells = words(data[3], data[1]*data[2]*2)
                        for pointer in cells[::2]: string(pointer)
                    if entry[0] == 0x24 and any(s in label.lower() for s in ('playlist', 'configs', 'market', 'motd')):
                        n = data[1] or data[2]
                        if 0 < n < 4*1024*1024: read(data[3], n)
                    if entry[0] == 0x27 and label == 'mp/playerdata.def':
                        d = words(data[2], 16)
                        read(d[5], d[4]*20);read(d[7], d[6]*16);read(d[14], d[13]*4)
                    if entry[0] == 44:
                        header = words(entry[2], 5)
                        if header[3]:
                            for pointer in words(header[4], header[3]): string(pointer)
                index = entry[5]
        for va, n in [(0x779583c,0x200),(0x7797fe8,0x40),(0x77988e4,8),(0xe57358,0x24),(0x8301ae4,10004)]:read(va,n)
        for va, stride in [(0x779583c,40),(0x7795844,2),(0x77988e4,144),(0x7797fe8,28),(0x7797ff8,2),(0x7798000,24),(0x7798008,2)]:
            pointer, count = words(va, 2)
            if count:read(pointer,count*stride)
        pointer, count = words(0x779583c,2)
        for i in range(count):
            p = words(pointer+i*40+8)[0]
            if p:string(p)
        pointer,count=words(0x7797fe8,2)
        for i in range(count):
            b=read(pointer+i*28,28);n=b[14];p=struct.unpack_from('<I',b,16)[0]
            if n:read(p,n*4)
        for p in words(0x1978640,0x3ffd):
            if p:string(p)
        result={'pid':47740,'assets':assets,'records':len(records),'bytes':sum(len(b) for b in records.values())}
        with (OUT/'resource-memory.bin').open('wb') as f:
            for (va,n),b in records.items():f.write(struct.pack('<II',va,n)+b)
        (OUT/'resource-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:k.CloseHandle(h)

try:capture()
except Exception:(OUT/'resource-evidence.error.txt').write_text(traceback.format_exc(),encoding='utf-8')
