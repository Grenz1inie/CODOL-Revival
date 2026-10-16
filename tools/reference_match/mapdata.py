"""Load an independent map package using only its manifest and data files."""
import hashlib
import json
from pathlib import Path
import struct


def load_map(directory):
    """Verify all exported hashes; return data without implying map readiness.

    ncs.registry is an offline candidate. Client registration verification is
    independent of collision.physics_ready, which applies only to the explicit
    manifest.readiness_scope (for v5, the DM frozen initial static world).
    position contains evidence/status, not a fallback quantization origin.
    Earlier packages without position.json return None for this field.
    """
    directory = Path(directory).resolve()
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['schema_version'] != 1 or manifest['format_version'] != 423:
        raise ValueError('unsupported map package version')
    files = {}
    for name, expected in manifest['files'].items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory):
            raise ValueError('map package path escapes directory')
        data = path.read_bytes()
        if len(data) != expected['bytes'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
            raise ValueError(f'map package integrity mismatch: {name}')
        files[name] = data
    baseline = files['baseline.bin']
    if baseline[:8] != b'IWCB000\x01' or (len(baseline) - 8) % 272 or len(baseline) > 190408:
        raise ValueError('invalid baseline header/length')
    states = [baseline[i:i + 272] for i in range(8, len(baseline), 272)]
    if len(states) != manifest['baseline']['count']:
        raise ValueError('baseline count mismatch')
    for state in states:
        number, kind = struct.unpack_from('<ii', state)
        if not 0 <= number <= 2048 or kind < 0:
            raise ValueError('invalid baseline entity')
    return dict(manifest=manifest, baselines=states, spawns=json.loads(files['spawns.json']),
                ncs=json.loads(files['ncs.json']), collision=json.loads(files['collision.json']),
                position=json.loads(files['position.json']) if 'position.json' in files else None,
                geometry=json.loads(files['geometry.json']) if 'geometry.json' in files else None,
                spawn_grounding=json.loads(files['spawn-grounding.json']) if 'spawn-grounding.json' in files else None,
                static_model_closure=json.loads(files['static-model-closure.json']) if 'static-model-closure.json' in files else None,
                submodel_placements=json.loads(files['submodel-placements.json']) if 'submodel-placements.json' in files else None,
                files=files)
