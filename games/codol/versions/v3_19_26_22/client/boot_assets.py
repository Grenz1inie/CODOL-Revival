"""Build cached boot resources without importing a startup package."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from . import fastfile, localization, publisher

SOURCE = Path(__file__).parents[1] / 'resources'
ARCHIVE = 'IIPS/IIPSDownload/ff_init_common_gfx_V109.ifs'
SOURCE_HASHES = {
    'codoMP_client_shipRetail.exe': fastfile.CLIENT_SHA256,
    ARCHIVE: localization.ARCHIVE_SHA256,
    'IIPS/IFS2.dll': '5b0324e0b2ba3545a6c02626287d4fbc6a3116594744f4647333982d85508421',
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inputs(source):
    result = {name: digest(source / name) for name in SOURCE_HASHES}
    if result != SOURCE_HASHES:
        raise ValueError('3.19 original game resource hash mismatch')
    for folder in ('english', 'publisher'):
        result.update({str(p.relative_to(SOURCE)): digest(p) for p in sorted((SOURCE/folder).glob('*')) if p.is_file()})
    for module in (Path(__file__), Path(fastfile.__file__), Path(localization.__file__), Path(publisher.__file__)):
        result[module.name] = digest(module)
    return result


def generate(source, stage, native):
    # IFS2 comes from the fingerprinted original game. It sees only an archive
    # copy, and the source-built reader writes numeric filenames in this stage.
    shutil.copy2(source / 'IIPS/IFS2.dll', stage/'IFS2.dll')
    shutil.copy2(source / ARCHIVE, stage/'original.ifs')
    extracted = stage/'extracted'
    extracted.mkdir()
    read = subprocess.run([str(native/'ifs-read.exe'), str(stage/'IFS2.dll'),
                           str(stage/'original.ifs'), str(extracted)],
                          capture_output=True, text=True, timeout=60,
                          creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if read.returncode:
        raise RuntimeError('3.19 original archive extraction failed: ' + read.stderr)
    files = {}
    for line in read.stdout.splitlines():
        index, size, name = line.split('\t')
        if not index.isdecimal():
            raise ValueError('Invalid archive entry number')
        label = name.replace('\\', '/').rsplit('/', 1)[-1]
        if label in files:
            raise ValueError('Duplicate boot resource: ' + label)
        data = (extracted/(index+'.bin')).read_bytes()
        if len(data) != int(size):
            raise ValueError('Truncated boot resource: ' + label)
        files[label] = data
    client = (source/'codoMP_client_shipRetail.exe').read_bytes()
    private, public = fastfile.keys(client)
    playlist = fastfile.raw_files(fastfile.decode(files['mp_playlists.ff'], 'mp_playlists', private, public))['mp_playlists.info']
    result = publisher.files(client, playlist)
    replacements = []
    for name in ('localized_code_post_gfx_mp', 'localized_ui_mp'):
        wire = files[name+'.ff']
        spec = json.loads((SOURCE/'english'/f'{name}.json').read_text(encoding='utf-8'))
        zone = localization.translate_zone(fastfile.decode(wire, name, private, public), spec)
        replacements.append((wire, localization.unsigned(wire, zone, private)))
    result['patches/ff_init_common_gfx_V109.ifs'] = localization.patch_archive((source/ARCHIVE).read_bytes(), replacements)
    result['patches/localization.txt'] = (SOURCE/'english/localization.txt').read_text(encoding='utf-8').encode('gb18030')
    return result


def build(source, destination, native):
    source, destination, native = map(lambda p: Path(p).resolve(), (source, destination, native))
    fingerprints = inputs(source)
    marker = destination/'boot-build.json'
    try:
        manifest = json.loads(marker.read_text(encoding='utf-8'))
        if manifest['sources'] == fingerprints and all(digest(destination/p) == h for p,h in manifest['outputs'].items()):
            return destination
    except (OSError, ValueError, KeyError):
        pass
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.boot319-', dir=destination.parent) as temporary:
        stage = Path(temporary)
        generated = generate(source, stage, native)
        manifest = {'sources': fingerprints, 'outputs': {p: hashlib.sha256(b).hexdigest() for p,b in generated.items()}}
        for name, data in generated.items():
            path = stage/'output'/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for name in generated:
            path = destination/name
            path.parent.mkdir(parents=True, exist_ok=True)
            (stage/'output'/name).replace(path)
        temporary_marker = destination/'boot-build.tmp'
        temporary_marker.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
        temporary_marker.replace(marker)
    return destination
