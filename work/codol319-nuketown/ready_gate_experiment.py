"""Authorized experiment only: hash/path-bound Ready gate in a disposable process."""
from contextlib import contextmanager
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import struct
import sys
import threading
import time
import traceback
from ready_gate_proposal import gate, ORIGINAL

EXPERIMENT = Path('A:/CODOL-Lab/ready319-20261017')
GAME = EXPERIMENT / 'game/codoMP_client_shipRetail.exe'
SHA = '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537'


def install(process):
    entry = process.base + 0x23c5e0
    with process.suspended():
        if process.read(entry, 6) != ORIGINAL:
            return None
        cave = process.allocate()
        payload, patch = gate(process.base, cave)
        process.write(cave, payload)
        if process.read(cave, len(payload)) != payload:
            raise OSError('Gate payload readback mismatch')
        process.executable(cave)
        process.patch(entry, ORIGINAL, patch)
        if process.read(entry, 6) != patch:
            raise OSError('Gate entry readback mismatch')
        return dict(entry=hex(entry), cave=hex(cave), original=ORIGINAL.hex(),
                    patch=patch.hex(), payload=payload.hex(), module_base=hex(process.base))


class NativeMemory:
    def __init__(self, pid):
        if hashlib.sha256(GAME.read_bytes()).hexdigest() != SHA:
            raise ValueError('Experimental client hash mismatch')
        k = self.k = c.WinDLL('kernel32', use_last_error=True)
        self.nt = c.WinDLL('ntdll')
        pointer, size = c.c_void_p, c.c_size_t
        k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        k.OpenProcess.restype = w.HANDLE
        k.CloseHandle.argtypes = [w.HANDLE]
        k.QueryFullProcessImageNameW.argtypes = [w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)]
        k.K32EnumProcessModulesEx.argtypes = [w.HANDLE,c.POINTER(w.HMODULE),w.DWORD,c.POINTER(w.DWORD),w.DWORD]
        for name in ('ReadProcessMemory', 'WriteProcessMemory'):
            getattr(k, name).argtypes = [w.HANDLE,pointer,pointer,size,c.POINTER(size)]
        k.VirtualAllocEx.argtypes = [w.HANDLE,pointer,size,w.DWORD,w.DWORD]
        k.VirtualAllocEx.restype = pointer
        k.VirtualProtectEx.argtypes = [w.HANDLE,pointer,size,w.DWORD,c.POINTER(w.DWORD)]
        k.FlushInstructionCache.argtypes = [w.HANDLE,pointer,size]
        for name in ('NtSuspendProcess', 'NtResumeProcess'):
            getattr(self.nt, name).argtypes = [w.HANDLE]
            getattr(self.nt, name).restype = w.LONG
        self.handle = k.OpenProcess(0xc38, False, pid)
        if not self.handle: raise c.WinError(c.get_last_error())
        try:
            name, count = c.create_unicode_buffer(32768), w.DWORD(32768)
            if not k.QueryFullProcessImageNameW(self.handle,0,name,c.byref(count)):
                raise c.WinError(c.get_last_error())
            if Path(name.value).resolve() != GAME.absolute():
                raise ValueError('Refusing any process outside the fixed experimental copy')
            modules, needed = (w.HMODULE * 1024)(), w.DWORD()
            if not k.K32EnumProcessModulesEx(self.handle,modules,c.sizeof(modules),c.byref(needed),3):
                raise c.WinError(c.get_last_error())
            self.base = modules[0]
        except BaseException:
            self.close()
            raise
    def close(self): self.k.CloseHandle(self.handle)
    def read(self, address, size):
        data, actual = c.create_string_buffer(size), c.c_size_t()
        if not self.k.ReadProcessMemory(self.handle,address,data,size,c.byref(actual)) or actual.value != size:
            raise c.WinError(c.get_last_error())
        return data.raw
    def write(self, address, data):
        actual = c.c_size_t()
        if not self.k.WriteProcessMemory(self.handle,address,data,len(data),c.byref(actual)) or actual.value != len(data):
            raise c.WinError(c.get_last_error())
    def protect(self, address, size, flags):
        previous = w.DWORD()
        if not self.k.VirtualProtectEx(self.handle,address,size,flags,c.byref(previous)):
            raise c.WinError(c.get_last_error())
        return previous.value
    def flush(self, address, size):
        if not self.k.FlushInstructionCache(self.handle,address,size): raise c.WinError(c.get_last_error())
    def allocate(self):
        result = self.k.VirtualAllocEx(self.handle,None,4096,0x3000,0x04)
        if not result or result > 0xffffffff: raise OSError('No x86 gate allocation')
        return result
    def executable(self, address):
        self.protect(address,4096,0x20)
        self.flush(address,4096)
    def patch(self, address, original, replacement):
        if self.read(address,len(original)) != original: raise ValueError('Original instruction mismatch')
        previous = self.protect(address,len(original),0x40)
        try:
            self.write(address,replacement)
            self.flush(address,len(replacement))
        except BaseException:
            self.write(address,original)
            self.flush(address,len(original))
            raise
        finally: self.protect(address,len(original),previous)
    @contextmanager
    def suspended(self):
        if self.nt.NtSuspendProcess(self.handle): raise OSError('Cannot suspend experimental process')
        try: yield
        finally:
            if self.nt.NtResumeProcess(self.handle): raise OSError('Cannot resume experimental process')
    def room(self):
        pointer = struct.unpack('<I',self.read(self.base + 0x7ee13fc,4))[0]
        if not pointer: return None
        count = struct.unpack('<I',self.read(pointer + 0x105d8,4))[0]
        if not 1 <= count <= 18: return None
        rows = self.read(pointer + 0xe368,count * 0x1d0)
        return dict(count=count, playlist=self.read(pointer+0x105fc,1)[0],
                    automatic=self.read(pointer+0x10614,1)[0], host=self.read(pointer+0x281,1)[0],
                    members=[dict(uid=struct.unpack_from('<Q',rows,i*0x1d0)[0],
                                  team=struct.unpack_from('<I',rows,i*0x1d0+0x88)[0],
                                  ready=rows[i*0x1d0+0x90]) for i in range(count)])


def monitor():
    process = None
    try:
        deadline = time.monotonic() + 120
        result = None
        while time.monotonic() < deadline and not (EXPERIMENT / 'stop.request').exists():
            state = json.loads((EXPERIMENT / 'startup.json').read_text())
            game = state.get('game')
            if game and process is None: process = NativeMemory(game['pid'])
            if process:
                try: result = install(process)
                except OSError as error:
                    # Only unreadable, still-unpacked original pages may be retried.
                    if getattr(error, 'winerror', None) not in (299, 487): raise
                if result:
                    result.update(pid=game['pid'], game=str(GAME), exe_sha256=SHA, time=time.time())
                    (EXPERIMENT / 'ready-gate-installed.json').write_text(json.dumps(result,indent=2))
                    break
            time.sleep(.5)
        if not result: raise TimeoutError('Ready gate original bytes unavailable')
        previous = None
        while not (EXPERIMENT / 'stop.request').exists():
            try:
                state = dict(room=process.room(),
                             gate_active=process.read(int(result['entry'],16),6).hex() == result['patch'])
            except OSError: state = None
            if state != previous:
                with (EXPERIMENT / 'ready-room-observations.jsonl').open('a') as stream:
                    stream.write(json.dumps(dict(time=time.time(), observation=state)) + '\n')
                previous = state
            time.sleep(.25)
    except BaseException:
        (EXPERIMENT / 'ready-gate-error.txt').write_text(traceback.format_exc())
        (EXPERIMENT / 'stop.request').touch()
    finally:
        if process: process.close()


if __name__ == '__main__':
    # A frozen, previously accepted lobby build keeps the Ready experiment apart
    # from concurrent startup/resource reconstruction. No production source edit.
    sys.path.insert(0,str(EXPERIMENT / 'source'))
    from games.codol.versions.v3_19_26_22.client.launch import supervise
    (EXPERIMENT / 'startup.json').write_text('{}')
    worker = threading.Thread(target=monitor, daemon=True)
    worker.start()
    try: supervise(EXPERIMENT)
    finally:
        (EXPERIMENT / 'stop.request').touch()
        worker.join(timeout=3)
