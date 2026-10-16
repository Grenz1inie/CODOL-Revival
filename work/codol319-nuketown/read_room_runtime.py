"""Bounded read-only room-interface inspection in the isolated current client."""
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import struct
import sys
import traceback

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
GAME = ROOT / 'runtime/instances/codol-3.19.26.22-911c42a0027c/game/codoMP_client_shipRetail.exe'
SHA = '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537'
PID = int(sys.argv[1])
k = c.WinDLL('kernel32', use_last_error=True)
k.OpenProcess.argtypes = [w.DWORD,w.BOOL,w.DWORD]
k.OpenProcess.restype = w.HANDLE
k.CloseHandle.argtypes = [w.HANDLE]
k.QueryFullProcessImageNameW.argtypes = [w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)]
k.ReadProcessMemory.argtypes = [w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
k.K32EnumProcessModulesEx.argtypes = [w.HANDLE,c.POINTER(w.HMODULE),w.DWORD,c.POINTER(w.DWORD),w.DWORD]

def capture():
    h = k.OpenProcess(0x410,False,PID)
    if not h: raise c.WinError(c.get_last_error())
    try:
        name,n = c.create_unicode_buffer(32768),w.DWORD(32768)
        if not k.QueryFullProcessImageNameW(h,0,name,c.byref(n)): raise c.WinError(c.get_last_error())
        assert Path(name.value).resolve() == GAME.resolve()
        assert hashlib.sha256(GAME.read_bytes()).hexdigest() == SHA
        modules,needed = (w.HMODULE*1024)(),w.DWORD()
        if not k.K32EnumProcessModulesEx(h,modules,c.sizeof(modules),c.byref(needed),3): raise c.WinError(c.get_last_error())
        base,ranges = modules[0],[]
        def read(va,size):
            assert 0 < size <= 16384
            buf,actual = c.create_string_buffer(size),c.c_size_t()
            if not k.ReadProcessMemory(h,va,buf,size,c.byref(actual)) or actual.value != size: raise c.WinError(c.get_last_error())
            ranges.append([hex(va),size])
            return buf.raw
        def static(va): return base+va-0x400000
        def words(va,n): return list(struct.unpack('<'+'I'*n,read(va,n*4)))
        original = (ROOT/'work/codol319-console/analysis-client319.exe').read_bytes()
        assert read(static(0x7cad60),64) == original[0x3cad60:0x3cada0]
        obj = words(static(0x82e13fc),1)[0]
        header = words(obj,64)
        vtable = words(header[0],40)
        count = words(obj+0x105d8,1)[0]
        assert 0 <= count <= 18
        roster = read(obj+0xe368,max(count,1)*0x1d0)
        info = read(obj+0x105f0,0x70)
        party = read(header[7],0x40)
        players = [{'uid':struct.unpack_from('<Q',roster,i*0x1d0)[0],
                    'name':roster[i*0x1d0+8:i*0x1d0+0x48].split(b'\0')[0].decode('gb18030', errors='replace'),
                    'team':struct.unpack_from('<I',roster,i*0x1d0+0x88)[0],
                    'bytes':roster[i*0x1d0:(i+1)*0x1d0].hex()} for i in range(count)]
        result = {'version':'3.19.26.22','exe_sha256':SHA,'pid':PID,'module_base':hex(base),
            'object':hex(obj),'header':header,'vtable':list(map(hex,vtable)),
            'count':count,'players':players,'room_info':info.hex(),'party_header':party.hex(),
            'flags':read(obj+0x278,0x20).hex(),
            'channel_members':read(header[7]+0x38,18*0x60).hex(),
            'source':'ReadProcessMemory; 0x7cad60 reads interface 0x82e13fc and calls virtual +0x78',
            'read_ranges':ranges,'unverified':'Network serialization; no writes or function execution'}
        (OUT/f'room-live-{PID}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    finally: k.CloseHandle(h)

try: capture()
except Exception:
    (OUT/f'room-live-{PID}.error.txt').write_text(traceback.format_exc(),encoding='utf-8')
    raise
