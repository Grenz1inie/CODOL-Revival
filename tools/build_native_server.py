"""Build the isolated native port from the immutable, user-provided source."""
from pathlib import Path
import os
import shutil
import subprocess
import hashlib
import json
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'research/experiments/story-native'
REFERENCE = STAGE / 'reference-source'


def prepare(destination):
    destination = Path(destination)
    for name in ('src', 'lib', 'plugins'):
        shutil.copytree(REFERENCE / name, destination / name)
    for name in ('makefile', 'License.md', 'Copyright.md', 'copying.md'):
        shutil.copy2(REFERENCE / name, destination / name)
    apply_port(destination)
    return destination


def apply_port(destination):
    """Apply to fresh reference files, then update changed generated files only."""
    patch = ROOT / 'tools/native/server3333.patch'
    names = [line[6:] for line in patch.read_text().splitlines() if line.startswith('--- a/')]
    inventory = json.loads((ROOT / 'research/evidence/reference-native-source.json').read_text())
    hashes = {entry['path']: entry['sha256'] for entry in inventory['files']}
    with tempfile.TemporaryDirectory(dir=STAGE) as scratch:
        scratch = Path(scratch)
        for name in names:
            original = REFERENCE / name
            if hashlib.sha256(original.read_bytes()).hexdigest() != hashes[name]:
                raise ValueError(f'Reference source hash mismatch: {name}')
            target = scratch / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(original.read_text(), newline='\n')
        subprocess.run(['A:/Coding/Git/usr/bin/patch.exe', '--batch', '--fuzz=0',
                        '-p1', '-i', str(patch)], cwd=scratch, check=True, capture_output=True)
        for name in names:
            target, patched = Path(destination) / name, (scratch / name).read_bytes()
            if target.read_bytes() != patched:
                target.write_bytes(patched)


def build_wire_probe(source, output):
    source, output = Path(source), Path(output)
    compiler = Path('A:/Coding/mingw64/bin')
    areas = [source / 'src/codol' / name for name in ('net', 'snapshot', 'assets', 'player', 'weapon')]
    files = [ROOT / 'tests/native/story_server_wire.c', areas[0] / 'codol_msg.c', areas[0] / 'codol_wire.c',
             areas[1] / 'codol_2697_configstrings.c', areas[1] / 'codol_2697_gamestate.c']
    files += [areas[1] / name for name in ('codol_2697_fields.c', 'codol_2697_profile.c',
        'codol_2697_delta.c', 'codol_delta.c', 'codol_2697_arrays.c', 'codol_2697_snapshot.c',
        'codol_2697_entities.c', 'codol_2697_clients.c', 'codol_2697_actors.c',
        'codol_2697_anim.c', 'codol_glass_snapshot.c', 'codol_2697_adapter.c',
        'codol_playerstate.c', 'codol_2697_resources.c', 'codol_configstrings.c',
        'codol_entities.c', 'codol_clients.c', 'codol_actors.c')]
    files += [areas[2] / name for name in ('codol_netconst_index.c', 'codol_netconst.c')]
    files += [areas[3] / 'codol_usercmd.c']
    env = dict(os.environ, PATH=str(compiler) + os.pathsep + os.environ['SystemRoot'] + '/System32')
    subprocess.run([str(compiler / 'gcc.exe'), '-shared', '-O1', '-std=gnu11',
                    '-static-libgcc', '-ffunction-sections', '-fno-asynchronous-unwind-tables',
                    '-Wl,--gc-sections,--exclude-all-symbols',
                    *['-I' + str(p) for p in areas],
                    *map(str, files), '-o', str(output)], env=env,
                   check=True, stdout=subprocess.PIPE)


def build_input_probe(source, output):
    source, output = Path(source), Path(output)
    compiler = Path('A:/Coding/MinGW/bin')
    includes = [source / 'src', *[p for p in (source / 'src/codol').iterdir() if p.is_dir()]]
    files = [ROOT / 'tests/native/story_server_input.c']
    files += [source / 'src/codol' / name for name in
              ('snapshot/codol_game.c', 'player/codol_usercmd.c', 'net/codol_msg.c')]
    env = dict(os.environ, PATH=str(compiler) + os.pathsep + os.environ['SystemRoot'] + '/System32')
    subprocess.run([str(compiler / 'gcc.exe'), '-m32', '-O1', '-std=gnu11', '-static-libgcc',
        '-ffunction-sections', '-fno-asynchronous-unwind-tables', '-Wl,--gc-sections',
        *['-I' + str(p) for p in includes], *map(str, files), '-o', str(output)],
        env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_publication_probe(source, output):
    source = Path(source)
    compiler = Path('A:/Coding/MinGW/bin')
    includes = [source / 'src', *[p for p in (source / 'src/codol').iterdir() if p.is_dir()]]
    files = [ROOT / 'tests/native/story_server_publication.c']
    files += [source / 'src/codol' / name for name in
              ('snapshot/codol_2697_publication.c', 'snapshot/codol_2697_resources.c',
               'snapshot/codol_2697_registration.c', 'snapshot/codol_configstrings.c',
               'assets/codol_netconst_index.c', 'assets/codol_netconst.c')]
    env = dict(os.environ, PATH=str(compiler) + os.pathsep + os.environ['SystemRoot'] + '/System32')
    subprocess.run([str(compiler / 'gcc.exe'), '-m32', '-O1', '-std=gnu11', '-static-libgcc',
        '-DCODOL_SERVER', '-ffunction-sections', '-fno-asynchronous-unwind-tables', '-Wl,--gc-sections',
        *['-I' + str(p) for p in includes], *map(str, files), '-o', str(output)],
        env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def build_core(source):
    source = Path(source)
    compiler = Path('A:/Coding/MinGW/bin')
    nasm = STAGE / 'toolchain/nasm-3.02/nasm.exe'
    if not nasm.is_file():
        raise FileNotFoundError('Extract the documented NASM 3.02 archive under story-native/toolchain')
    env = dict(os.environ, PATH=os.pathsep.join((str(compiler), 'A:/Coding/Git/usr/bin',
                                               os.environ['SystemRoot'] + '/System32')))
    log = STAGE / 'native-build3333.log'
    with log.open('w') as output:
        # The supplied archive's one UCRT object cannot link to MinGW.org CRT.
        # Rebuild that original source object with the selected compiler.
        (source / 'obj/codol').mkdir(parents=True, exist_ok=True)
        subprocess.run([str(compiler / 'gcc.exe'), '-m32', '-O1', '-Isrc/tomcrypt',
            '-c', 'src/tomcrypt/misc/crypt/crypt_argchk.c', '-o', 'obj/codol/crypt_argchk.o'],
            cwd=source, env=env, check=True, stdout=output, stderr=subprocess.STDOUT)
        subprocess.run([str(compiler / 'ar.exe'), 'r', 'lib/libtomcrypt.a', 'obj/codol/crypt_argchk.o'],
            cwd=source, env=env, check=True, stdout=output, stderr=subprocess.STDOUT)
        subprocess.run(['A:/Coding/mingw64/bin/mingw32-make.exe', '-j6',
            'CPP=g++ -fpermissive', 'SHELL=A:/Coding/Git/usr/bin/sh.exe',
            'NASM=' + nasm.as_posix(), 'EXTERNAL=', 'WIN_DEFINES=WINVER=0x501 AI_NUMERICSERV=8',
            'BUILD_NUMBER=1', 'BUILD_BRANCH=port3333', 'BUILD_REVISION=source-port',
            'bin/codol_dedrun.exe'], cwd=source, env=env, check=True,
            stdout=output, stderr=subprocess.STDOUT)
    executable = source / 'bin/codol_dedrun.exe'
    manifest = dict(reference_zip_sha256='152755e1ee460b8cbb1bf5c6e0069dd7a13541bf9a4a2e65b5a11ebf36fa5978',
        patch_sha256=hashlib.sha256((ROOT / 'tools/native/server3333.patch').read_bytes()).hexdigest(),
        executable=str(executable), executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
        compiler='MinGW.org GCC 6.3.0, x86', assembler='NASM 3.02', log=str(log),
        gameplay_verified=False)
    (STAGE / 'native-build3333.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    source = STAGE / 'server3333'
    if source.exists():
        apply_port(source)
    else:
        prepare(source)
    print(json.dumps(build_core(source),indent=2))
