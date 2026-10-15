"""Rebuild frontend and Killhouse NCS sets from already extracted signed FF423.

Run from any directory; defaults point at this project's archived inputs.
No game process, IFS mutation, baseline renumbering, or loadout export occurs.
Selected zones are a loader-derived candidate, not a live mounted-set capture.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zlib

from decode_story_fastfile import CLIENT_SHA256, decode
from export_match_map import read_zone_ncs
from story_netconst423 import build_registry

ROOT = Path(__file__).resolve().parents[1]
COMMON = ('code_pre_gfx_mp', 'localized_code_pre_gfx_mp',
          'code_post_gfx_default_mp', 'code_post_gfx_mp', 'localized_code_post_gfx_mp',
          'common_mp', 'localized_common_mp',
          'common_marketplace_lite', 'localized_common_marketplace_lite')
PHASES = {
    'frontend': COMMON + ('ui_mp', 'localized_ui_mp'),
    'map': COMMON + ('common_gametype_mp', 'localized_common_gametype_mp',
                    'mp_killhouse_sh', 'mp_killhouse_sh_const', 'common_mp_reload',
                    'mp_killhouse_sh_load', 'common_loadscreen'),
}


def build(client_path, ff_directory, registration_path):
    client = Path(client_path).read_bytes()
    if hashlib.sha256(client).hexdigest() != CLIENT_SHA256:
        raise ValueError('client hash mismatch')
    captured = Path(registration_path).read_bytes()
    registration = json.loads(captured)
    if (registration['exe_sha256'] != CLIENT_SHA256 or
            zlib.crc32(''.join(registration['names']).encode('ascii')) != registration['checksum_seed']):
        raise ValueError('registration evidence does not match client/seed')
    decoded, sources = {}, []
    for name in dict.fromkeys(zone for zones in PHASES.values() for zone in zones):
        path = Path(ff_directory) / (name + '.ff')
        wire = path.read_bytes()
        zone = decode(client, wire, name)  # Signature, name, block hashes, version.
        ncs = read_zone_ncs(zone)
        if ncs['unresolved']:
            raise ValueError(f'{name}: unresolved NCS; cannot publish a complete set')
        decoded[name] = ncs
        sources.append(dict(name=name, path=str(path.resolve()),
            ff_sha256=hashlib.sha256(wire).hexdigest(),
            zone_sha256=hashlib.sha256(zone).hexdigest(), signed_ff_verified=True))
    result = {}
    for phase, zones in PHASES.items():
        tables = [dict(table, zone=name) for name in zones for table in decoded[name]['tables']]
        registry = build_registry(tables, checksum_seed=registration['checksum_seed'])
        result[phase] = dict(tables=tables, unresolved=[],
            empty_assets=[dict(asset, zone=name) for name in zones for asset in decoded[name]['empty_assets']],
            selected_zones=list(zones), registry=registry,
            checksum_seed=registration['checksum_seed'], client_checksum=registry['checksum'],
            registration_evidence=registration, zone_type='mp', gametype='dm',
            mounted_set_verified=False, client_checksum_verified=False,
            status='signed_ff_loader_selected_inputs_not_live_mount_proof')
    result['sources'] = dict(client_sha256=CLIENT_SHA256,
        registration_evidence_path=str(Path(registration_path).resolve()),
        registration_evidence_sha256=hashlib.sha256(captured).hexdigest(), fastfiles=sources)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, default=ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe')
    parser.add_argument('--ff-directory', type=Path, default=ROOT / 'research/experiments/story-native/startup-assets/chinese')
    parser.add_argument('--registration', type=Path, default=ROOT / 'research/evidence/live-netconst-registration423.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'research/experiments/independent-match/registration/rebuilt')
    args = parser.parse_args()
    result = build(args.client, args.ff_directory, args.registration)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, key in [('ncs.json', 'map'), ('frontend-ncs.json', 'frontend'), ('sources.json', 'sources')]:
        (args.output / name).write_text(json.dumps(result[key], indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(output=str(args.output.resolve()),
        checksums={phase: result[phase]['client_checksum'] for phase in PHASES},
        map_tables=len(result['map']['tables']))))


if __name__ == '__main__':
    main()
