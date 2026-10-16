"""Prepare the current Nuketown package from an explicitly selected client."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

VERSION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VERSION / 'reverse/tools'))
from decode_story_fastfile import CLIENT_SHA256, decode
from reference_match.mapdata import load_map

PACKAGE = Path('runtime/builds/codol/v3_3_3_3/maps/nuketown')
SERVER = Path('runtime/builds/codol/v3_3_3_3/rust-match/release/codol-match.exe')


def resource_errors(root, *, include_package=True):
    root = Path(root)
    errors = []
    if not (root / SERVER).is_file():
        errors.append('Missing Rust match server. Run scripts/Invoke-MatchCargo.ps1 build --release')
    if include_package:
        try:
            validate_package(root / PACKAGE)
        except (OSError, ValueError, KeyError, TypeError) as error:
            errors.append(f'Nuketown package unavailable: {error}. Run games/codol/versions/'
                          'v3_3_3_3/scripts/Prepare-Resources.ps1 -GameRoot <game directory>. '
                          'If an existing package is damaged, move it aside first; preparation preserves it.')
    return errors


def validate_package(directory):
    package = load_map(directory)
    manifest = package['manifest']
    if manifest['map'] != 'mp_nuked' or manifest['gametype'] != 'dm' or not manifest['physics_ready']:
        raise ValueError('Nuketown DM package is not physics ready')
    for name in ('geometry.json', 'position.json', 'waypoints.csv', 'weapon-acr.bin', 'loadout.json'):
        if name not in package['files']:
            raise ValueError(f'incomplete Nuketown package: {name}')
    loadout = json.loads(package['files']['loadout.json'])
    if ([loadout[k]['index'] for k in ('weapon', 'body', 'hands')] != [5, 109, 54]
            or package['ncs']['client_checksum'] != 1765105316):
        raise ValueError('Nuketown registration/loadout mismatch')
    return manifest


def prepare(root, game):
    root, game = Path(root).resolve(), Path(game).resolve()
    client = game / 'codoMP_client_shipRetail.exe'
    with client.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != CLIENT_SHA256:
            raise ValueError('client hash mismatch: select the supported 3.3.3.3 installation')
    destination = root / PACKAGE
    if destination.exists():
        validate_package(destination)
        return destination
    compiler = shutil.which(os.environ.get('CODOL_IFS_CC', 'gcc'))
    if not compiler:
        raise RuntimeError('Install an x86 MinGW GCC toolchain and set CODOL_IFS_CC to its gcc.exe')
    from build_match_registration import build
    from export_match_map import export_zones, export_geometry_package
    from export_match_loadout import export_loadout
    from extract_story_resources import extract_nuketown

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.prepare-', dir=destination.parent) as temporary:
        stage = Path(temporary)
        extractor = stage / 'ifs-read.exe'
        shutil.copyfile(VERSION / 'reverse/tools/ifs-read.c', stage / 'ifs-read.c')
        compiler_env = dict(os.environ, PATH=str(Path(compiler).parent) + os.pathsep + os.environ.get('PATH', ''))
        task = subprocess.run([compiler, '-m32', '-O2', '-Wall', '-static-libgcc', '-o', 'ifs-read.exe', 'ifs-read.c'],
                              cwd=stage, env=compiler_env, capture_output=True, text=True, timeout=60)
        if task.returncode:
            raise RuntimeError('IFS reader requires x86 MinGW GCC; set CODOL_IFS_CC.\n' + task.stderr)
        print('Extracting Nuketown and shared fastfiles...', file=sys.stderr, flush=True)
        fastfiles = extract_nuketown(game, stage / 'extracted', extractor)
        definition = VERSION / 'resources/definitions/network-registration423.json'
        print('Verifying signed fastfiles and rebuilding registration...', file=sys.stderr, flush=True)
        registration = build(client, fastfiles, definition, map_name='mp_nuked')
        registry = stage / 'registration'
        registry.mkdir()
        for name, key in (('ncs.json', 'map'), ('sources.json', 'sources')):
            (registry / name).write_text(json.dumps(registration[key], indent=2) + '\n', encoding='utf-8')
        client_bytes = client.read_bytes()
        zones = {name: decode(client_bytes, (fastfiles / (name + '.ff')).read_bytes(), name)
                 for name in ('mp_nuked', 'mp_nuked_const', 'common_mp')}
        common = stage / 'common_mp.zone'
        common.write_bytes(zones['common_mp'])
        print('Exporting collision, loadout and navigation...', file=sys.stderr, flush=True)
        export_zones(zones, stage / 'base', map_name='mp_nuked',
                     registration=json.loads(definition.read_text()), output_root=stage)
        export_loadout(stage / 'base', stage / 'loadout', common,
                       VERSION / 'resources/navigation/mp_nuked_wp.csv', registry, output_root=stage)
        final = stage / 'complete'
        export_geometry_package(stage / 'loadout', final,
                                model_zones={'common_mp': zones['common_mp']}, output_root=stage)
        validate_package(final)
        # Same-volume rename publishes only a complete, verified package.
        # If another preparation won the race, preserve and verify its result.
        try:
            final.rename(destination)
        except FileExistsError:
            validate_package(destination)
    return destination


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--require-server', action='store_true')
    args = parser.parse_args()
    try:
        if args.require_server:
            errors = resource_errors(args.root, include_package=False)
            if errors:
                raise ValueError('\n'.join(errors))
        print(json.dumps({'package': str(prepare(args.root, args.game))}))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'Resource preparation failed: {error}', file=sys.stderr)
        sys.exit(1)
