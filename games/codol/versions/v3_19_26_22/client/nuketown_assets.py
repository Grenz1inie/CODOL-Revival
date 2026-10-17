"""One current-version map spawn, generated from the selected game's signed FF."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

from . import fastfile
from .boot_assets import SOURCE_HASHES

SPEC = Path(__file__).parents[1]/'resources/definitions/nuketown319.json'


def select_spawn(data):
    if not data.endswith(b'\0'):
        raise ValueError('Unterminated 3.19 map entities')
    for block in re.findall(r'\{([^{}]*)\}', data[:-1].decode('ascii')):
        row = dict(re.findall(r'"([^"]*)"\s+"([^"]*)"', block))
        if row.get('classname') != 'mp_tdm_spawn':
            continue
        try:
            origin = list(map(float, row['origin'].split()))
            angles = list(map(float, row['angles'].split()))
        except (KeyError, ValueError) as error:
            raise ValueError('Invalid team spawn') from error
        if len(origin) != 3 or len(angles) != 3 or any(not math.isfinite(x) or abs(x)>131072 for x in origin+angles):
            raise ValueError('Invalid team spawn position')
        return {'map':'mp_nuked', 'origin':origin, 'yaw':angles[1], 'classname':'mp_tdm_spawn'}
    raise ValueError('No 3.19 team spawn in map entities')


def build(game, destination, reader):
    game, destination, reader = map(Path, (game, destination, reader))
    spec = json.loads(SPEC.read_text())
    archive = game/spec['archive']
    digest = lambda data: hashlib.sha256(data).hexdigest()
    wire_archive = archive.read_bytes()
    if digest(wire_archive) != spec['archive_sha256']:
        raise ValueError('Unsupported 3.19 Nuketown archive')
    client = (game/'codoMP_client_shipRetail.exe').read_bytes()
    keys = fastfile.keys(client)
    library = (game/'IIPS/IFS2.dll').read_bytes()
    if digest(library) != SOURCE_HASHES['IIPS/IFS2.dll']:
        raise ValueError('3.19 IFS library hash mismatch')
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.nuketown-', dir=destination) as temporary:
        stage = Path(temporary)
        (stage/'map.ifs').write_bytes(wire_archive)
        (stage/'IFS2.dll').write_bytes(library)
        (stage/'out').mkdir()
        result = subprocess.run([str(reader.resolve()), str(stage/'IFS2.dll'), str(stage/'map.ifs'), str(stage/'out')],
            capture_output=True, text=True, check=True, timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        entries = [line.split('\t') for line in result.stdout.splitlines()]
        index, size, _ = next(row for row in entries if row[2].replace('\\','/').endswith('/mp_nuked.ff'))
        if not index.isdecimal(): raise ValueError('Invalid IFS entry index')
        wire = (stage/'out'/(index+'.bin')).read_bytes()
        if len(wire) != int(size) or digest(wire) != spec['ff_sha256']:
            raise ValueError('3.19 Nuketown FF hash mismatch')
        zone = fastfile.decode(wire, 'mp_nuked', *keys)
        if digest(zone) != spec['zone_sha256']:
            raise ValueError('3.19 Nuketown entity source mismatch')
        start = spec['entity_offset']
        spawn = select_spawn(zone[start:start+spec['entity_bytes']])
        spawn['source'] = {key:spec[key] for key in ('version','archive_sha256','zone_sha256','entity_offset','entity_bytes')}
        spawn['source']['exe_sha256'] = fastfile.CLIENT_SHA256
        path = destination/'spawn.json'
        (stage/'spawn.json').write_text(json.dumps(spawn)+'\n', encoding='utf-8')
        (stage/'spawn.json').replace(path)
        return path
