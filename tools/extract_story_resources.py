"""Extract first-campaign IFS copies; retain per-package provenance and hashes."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z'
STAGE = ROOT / 'research/experiments/story-native/resources'
DLL_SHA256 = '5b0324e0b2ba3545a6c02626287d4fbc6a3116594744f4647333982d85508421'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(base=False, common=False, pvp=False):
    stage = STAGE.with_name('resources-base') if base else STAGE
    map_name = 'mp_cargoship' if base else 'coop_training_mp_cargoship'
    dll = GAME / 'IIPS/IFS2.dll'
    if digest(dll) != DLL_SHA256:
        raise ValueError('IFS DLL hash mismatch: recovered structure offsets are version-specific')
    extractor = STAGE.parent / 'ifs-read.exe'
    archives = sorted(path for path in (GAME / 'IIPS/IIPSDownload').glob(f'*init_{map_name}*.ifs'))
    if common:
        stage = STAGE.with_name('resources-common')
        map_name = 'common_mp+common_gametype_coop'
        archives = [GAME / 'IIPS/IIPSDownload' / name for name in (
            'ff_init_common_mp_V43.ifs', 'ff_init_common_gametype_coop_V28.ifs')]
    if pvp:
        stage = STAGE.with_name('resources-pvp')
        map_name = 'mp_killhouse_sh+common_gametype_mp'
        archives = [GAME / 'IIPS/IIPSDownload' / name for name in (
            'ff_init_common_gametype_mp_V26.ifs', 'ff_init_mp_killhouse_sh_V32.ifs',
            'lf_init_mp_killhouse_sh_const_V26.ifs')]
    if not archives:
        raise FileNotFoundError('first campaign archives')
    stage.mkdir(exist_ok=False)
    manifest = {'map': map_name, 'dll_sha256': DLL_SHA256,
                'extractor_sha256': digest(extractor), 'archives': []}
    for source in archives:
        folder = stage / source.stem
        folder.mkdir()
        archive = folder / source.name
        before = digest(source)
        shutil.copyfile(source, archive)
        if digest(archive) != before:
            raise ValueError('archive copy hash mismatch')
        task = subprocess.run([str(extractor), str(dll), str(archive), str(folder)],
                              capture_output=True, text=True, timeout=60)
        (folder / 'extract.log').write_text(task.stderr, encoding='utf-8')
        item = {'archive': source.name, 'sha256': before, 'exit_code': task.returncode,
                'source_unchanged': digest(source) == before,
                'copy_unchanged': digest(archive) == before, 'files': []}
        for line in task.stdout.splitlines():
            index, size, name = line.split('\t', 2)
            data = folder / f'{index}.bin'
            with data.open('rb') as stream:
                header = stream.read(16)
            item['files'].append({'index': int(index), 'name': name.replace('\\', '/'),
                                  'size': int(size), 'sha256': digest(data), 'header': header.hex(),
                                  'file': data.relative_to(ROOT).as_posix()})
        manifest['archives'].append(item)
        (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        if task.returncode or not item['source_unchanged'] or not item['copy_unchanged']:
            raise RuntimeError(f'{source.name}: extraction failed; see manifest/log')
        print(source.name, len(item['files']))
    if pvp:
        required = {'common_gametype_mp.ff', 'localized_common_gametype_mp.ff',
                    'mp_killhouse_sh.ff', 'mp_killhouse_sh_load.ff', 'mp_killhouse_sh_const.ff'}
        assets = STAGE.parent / 'startup-assets/chinese'
        for archive in manifest['archives']:
            for item in archive['files']:
                name = Path(item['name']).name
                if name in required:
                    source = ROOT / item['file']
                    if digest(source) != item['sha256']:
                        raise ValueError('extracted fastfile hash mismatch')
                    shutil.copyfile(source, assets / name)
                    required.remove(name)
        if required:
            raise ValueError(f'missing PVP fastfiles: {sorted(required)}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--base', action='store_true', help='extract the first campaign map\'s mp_cargoship base resources')
    group.add_argument('--common', action='store_true', help='inspect shared MP and coop dependencies for scripts')
    group.add_argument('--pvp', action='store_true', help='extract and install Killhouse/MP fastfiles in the isolated server')
    args = parser.parse_args()
    main(args.base, args.common, args.pvp)
