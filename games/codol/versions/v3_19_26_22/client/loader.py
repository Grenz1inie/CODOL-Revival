"""3.19 bootstrap from source; only the newly created private game is patched."""
import argparse
from contextlib import ExitStack
import ctypes
from ctypes import wintypes
import mmap
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from games.codol.versions.v3_19_26_22.client.preparation import CLIENT, check_client


def metadata():
    """TCLS offset/length records recovered from the 3.19 launcher, not 3.3."""
    data = bytearray(0x100000)
    struct.pack_into('<I', data, 0, 64)
    struct.pack_into('<I', data, 0x50, 0x1000)
    for group in range(256):
        table = 0x2000 + group * 0x400
        struct.pack_into('<I', data, 0x1000 + group * 4, table)
        for key in range(256):
            offset = 0x42000 + group * 0x800 + key * 8
            struct.pack_into('<I', data, table + key * 4, offset)
            struct.pack_into('<II', data, offset, 4, 0)
    cursor = 0xc3000

    def put(table, key, value):
        nonlocal cursor
        if isinstance(value, int):
            value = struct.pack('<I', value)
        struct.pack_into('<I', data, table + key * 4, cursor)
        struct.pack_into('<I', data, cursor, len(value))
        data[cursor + 4:cursor + 4 + len(value)] = value
        cursor += (4 + len(value) + 3) & ~3

    for key in range(1, 20):
        put(0, key, 0)
    for key, value in {1: 1, 2: 1000001, 3: b'\0', 4: b'\0', 5: bytes(16),
                       7: b'127.0.0.1:31900\0', 22: bytes(16), 24: b'LocalPlayer\0',
                       25: bytes(16), 27: b'\0', 14: bytes(2), 15: bytes(2),
                       16: bytes(2), 17: 1, 18: 1, 19: bytes(2)}.items():
        put(0, key, value)
    for key, value in {1: 'Local CODOL 3.19\0'.encode('utf-16le'), 2: 1,
                       3: '127.0.0.1\0'.encode('utf-16le'), 4: 0x0100007f,
                       5: 31900, 6: 34, 7: b'127.0.0.1:31900;127.0.0.1:31901;1\0'}.items():
        put(0x2000, key, value)
    return data


class ProcessMemory:
    def __init__(self, pid):
        api = self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        pointer, size = ctypes.c_void_p, ctypes.c_size_t
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.OpenProcess.restype = wintypes.HANDLE
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        for name in ('ReadProcessMemory', 'WriteProcessMemory'):
            function = getattr(api, name)
            function.argtypes = [wintypes.HANDLE, pointer, pointer, size, ctypes.POINTER(size)]
            function.restype = wintypes.BOOL
        api.VirtualProtectEx.argtypes = [wintypes.HANDLE, pointer, size, wintypes.DWORD,
                                        ctypes.POINTER(wintypes.DWORD)]
        api.FlushInstructionCache.argtypes = [wintypes.HANDLE, pointer, size]
        self.handle = api.OpenProcess(0x38, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def __enter__(self):
        return self

    def __exit__(self, *error):
        self.api.CloseHandle(self.handle)

    def patch(self, address, original, replacement):
        if len(original) != len(replacement):
            raise ValueError('Patch size must preserve surrounding instructions')
        current = ctypes.create_string_buffer(len(original))
        count = ctypes.c_size_t()
        if not self.api.ReadProcessMemory(self.handle, address, current, len(original), ctypes.byref(count)):
            return False  # The protected client may not have unpacked this page yet.
        if count.value != len(original):
            return False
        if current.raw == replacement:
            return True
        if current.raw != original:
            return False
        protection = wintypes.DWORD()
        if not self.api.VirtualProtectEx(self.handle, address, len(original), 0x40, ctypes.byref(protection)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.api.WriteProcessMemory(self.handle, address, replacement, len(replacement), ctypes.byref(count)):
                raise ctypes.WinError(ctypes.get_last_error())
            if count.value != len(replacement):
                raise OSError('Incomplete bootstrap patch')
            if not self.api.FlushInstructionCache(self.handle, address, len(replacement)):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            previous = wintypes.DWORD()
            if not self.api.VirtualProtectEx(self.handle, address, len(original), protection.value, ctypes.byref(previous)):
                raise ctypes.WinError(ctypes.get_last_error())
        return True


def run(game, *, english=False):
    game = Path(game).resolve()
    check_client(game)
    command = subprocess.list2cmdline([str(game / CLIENT), '-q', '1000001', '-s', '127.0.0.1:31900',
                                      '+set', 'logfile', '2', '+set', '2452', '1'])
    command += ' ' + os.environ.get('CODOL319_EXTRA_ARGS', '')
    patches = [(0xd5a2cc, b'https://%s:%d/auth/\0', b'http://%s:%d/auth/\0\0'),
               (0x62136e, bytes.fromhex('8a4508'), bytes.fromhex('30c090')),
               (0xbae861, bytes.fromhex('b8020c0000'), bytes.fromhex('b8040c0000'))]
    if english:
        patches.append((0x483ec1, b'\x74\x1c', b'\x90\x90'))
    child = subprocess.Popen(command, cwd=game, close_fds=True)
    try:
        # The protection module must finish its first TAS lookup before the
        # empty mappings become visible (the historical loader waits 6000 ms).
        try:
            return child.wait(timeout=6)
        except subprocess.TimeoutExpired:
            pass
        with ExitStack() as stack:
            for name in (f'TCLS_TASMEMORY_{child.pid}', 'TCLS_TASMEMORY_', f'TCLS_SHAREDMEMEMORY{child.pid}'):
                mapping = stack.enter_context(mmap.mmap(-1, 0x100000, tagname=name))
            mapping[:] = metadata()
            process = stack.enter_context(ProcessMemory(child.pid))
            deadline = time.monotonic() + 120
            while child.poll() is None:
                for patch in patches[:]:
                    if process.patch(*patch):
                        patches.remove(patch)
                        print(f'bootstrap patch ready: {patch[0]:08x}', flush=True)
                if not patches:
                    return child.wait()
                if time.monotonic() >= deadline:
                    raise TimeoutError('3.19 bootstrap bytes unavailable: ' + ', '.join(f'{p[0]:08x}' for p in patches))
                time.sleep(0.25)
            return child.returncode
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=os.environ.get('CODOL319_GAME_DIR'), required='CODOL319_GAME_DIR' not in os.environ)
    parser.add_argument('--english-resources', action='store_true')
    args = parser.parse_args()
    sys.exit(run(args.game, english=args.english_resources))
