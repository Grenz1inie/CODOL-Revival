"""Publish resource-only data from the identified local 3.19 game process."""
import csv
import ctypes
from ctypes import wintypes
import hashlib
import io
import json
from pathlib import Path
import tempfile
import time

from .fastfile import CLIENT_SHA256
from .loaded_resources import LoadedResources
from .resource_tables import catalog


class ReadOnlyProcess:
    def __init__(self, identity, executable):
        api = self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        api.OpenProcess.restype = wintypes.HANDLE
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        api.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        api.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        api.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                        ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.handle = api.OpenProcess(0x410, False, identity['pid'])
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            buffer, length = ctypes.create_unicode_buffer(32768), wintypes.DWORD(32768)
            times = [wintypes.FILETIME() for _ in range(4)]
            if not api.QueryFullProcessImageNameW(self.handle, 0, buffer, ctypes.byref(length)) or not api.GetProcessTimes(
                    self.handle, *[ctypes.byref(t) for t in times]):
                raise ctypes.WinError(ctypes.get_last_error())
            created = ((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime) / 10000000 - 11644473600
            if Path(buffer.value).resolve() != Path(executable).resolve() or abs(created-identity['created']) > 0.001:
                raise ValueError('3.19 resource process identity mismatch')
            with Path(executable).open('rb') as source:
                if hashlib.file_digest(source, 'sha256').hexdigest() != CLIENT_SHA256:
                    raise ValueError('3.19 resource process executable hash mismatch')
        except BaseException:
            api.CloseHandle(self.handle)
            raise

    def __enter__(self):
        return self

    def __exit__(self, *error):
        self.api.CloseHandle(self.handle)

    def read(self, address, count):
        if not 0 < count <= 16*1024*1024 or not 0 < address < address+count <= 1 << 32:
            raise ValueError('Invalid 3.19 resource memory range')
        buffer, actual = ctypes.create_string_buffer(count), ctypes.c_size_t()
        if not self.api.ReadProcessMemory(self.handle, address, buffer, count, ctypes.byref(actual)) or actual.value != count:
            raise OSError('3.19 resource memory is not readable yet')
        return buffer.raw


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False)+'\n').encode('utf-8')


def common_files(loaded, registry):
    weapons = loaded.weapons()
    rows = io.StringIO(newline='')
    csv.writer(rows, lineterminator='\n').writerows(loaded.table('mp/rankTable.csv'))
    parts = [f'part {number} {name}\n' for number,name in registry['parts']]
    parts += [f'item {item} {name} {extension} ' + ' '.join(map(str, defaults))+'\n'
              for item,name,extension,defaults in registry['weapons']]
    result = {
        'item-registry319.json': json_bytes({'items': [[item,name] for item,_,name in registry['items']]}),
        'item-ids319.txt': ('# id index name\n'+''.join(f'{item} {index} {name}\n' for item,index,name in registry['items'])).encode(),
        'weapon-parts319.txt': ''.join(parts).encode('ascii'),
        'sku-items319.txt': ''.join(f'{sku} {product} ' + ' '.join(map(str,items))+'\n'
                                  for sku,product,items,_,_,_ in registry['skus']).encode(),
        'sku-prices319.txt': ''.join(f'{sku} {currency} {price} {days}\n'
                                   for sku,_,_,currency,price,days in registry['skus']).encode(),
        'rankTable319.csv': rows.getvalue().encode('utf-8'),
        'match-host/weapons319.txt': (f'count={len(weapons)-1} default_weapon=1\n'+''.join(
            f'{index} {name}\n' for index,name in enumerate(weapons))).encode('ascii'),
        'match-host/playerdata_classes319.json': json_bytes(loaded.classes()),
    }
    source = Path(__file__).parents[1]/'resources/match'
    for name in ('server-commands319.txt', 'viewmodel-arms56.txt'):
        result['match-host/'+name] = (source/name).read_text(encoding='utf-8').encode('utf-8')
    return result


def publish(root, files, game):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root/'common-ready.json').unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix='.resources-', dir=root) as temporary:
        stage = Path(temporary)
        for name,data in files.items():
            path = stage/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for name in files:
            target = root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            (stage/name).replace(target)
        marker = stage/'ready.json'
        marker.write_bytes(json_bytes({'game': game, 'outputs': {p: hashlib.sha256(b).hexdigest() for p,b in files.items()}}))
        marker.replace(root/'common-ready.json')


def validate_common(root):
    root = Path(root)
    manifest = json.loads((root/'common-ready.json').read_text(encoding='utf-8'))
    if not manifest['outputs']:
        raise ValueError('3.19 generated resources are empty')
    for name, expected in manifest['outputs'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('3.19 generated resource hash mismatch: '+name)
    return manifest


def wait_ready(root, timeout=30):
    deadline = time.monotonic()+timeout
    while not (Path(root)/'common-ready.json').is_file():
        if time.monotonic() >= deadline:
            raise TimeoutError('3.19 game resources are not ready; see startup.json and logs')
        time.sleep(0.1)


def export_common(root, game, executable):
    with ReadOnlyProcess(game, executable) as process:
        loaded = LoadedResources(process.read)
        # Check the late registrations before walking the larger catalog.
        loaded.classes()
        loaded.weapons()
        files = common_files(loaded, catalog(process.read))
    publish(root, files, game)


def export_map(target, game, executable, map_name):
    target = Path(target)
    with ReadOnlyProcess(game, executable) as process:
        clipmap, ladders = LoadedResources(process.read).clipmap(map_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    for path, data in ((target.with_suffix('.ladders.json'), json_bytes(ladders)), (target, clipmap)):
        temporary = path.with_suffix(path.suffix+'.tmp')
        temporary.write_bytes(data)
        temporary.replace(path)
