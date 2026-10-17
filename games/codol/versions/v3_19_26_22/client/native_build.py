"""Build the version-specific x86 bridge with public MinGW GCC."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

SOURCE = Path(__file__).with_name('native')
IFS_READER = SOURCE.parents[2] / 'v3_3_3_3/reverse/tools/ifs-read.c'
OUTPUTS = ('version.dll', 'client_loopback319.dll', 'collision319.exe', 'ifs-read.exe')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compiler():
    result = shutil.which(os.environ.get('CODOL319_CC', 'gcc'))
    if not result:
        raise RuntimeError('Install x86 MinGW GCC and set CODOL319_CC to its gcc.exe')
    return result


def compiler_env(path):
    return {**os.environ, 'PATH': str(Path(path).parent) + os.pathsep + os.environ.get('PATH', '')}


def inputs():
    return {p.name: digest(p) for p in [Path(__file__), IFS_READER, *sorted(SOURCE.glob('*'))] if p.is_file()}


def validate(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'native-build.json').read_text())
    if manifest['sources'] != inputs() or any(digest(directory / p) != manifest['outputs'][p] for p in OUTPUTS):
        raise ValueError('3.19 native build is missing, changed or stale; run preparation again')
    return directory


def build(directory):
    directory = Path(directory)
    try:
        return validate(directory)
    except (OSError, ValueError, KeyError):
        pass
    cc = compiler()
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.native319-', dir=directory.parent) as temporary:
        stage = Path(temporary)
        for output, sources in [('version.dll', ['version.c', 'version.def']),
                                ('client_loopback319.dll', ['bridge.c', 'capture.c']),
                                ('collision319.exe', ['collision.cpp']),
                                ('ifs-read.exe', [str(IFS_READER)])]:
            flags = ['-std=c++11', '-static', '-lstdc++', '-msse2', '-mfpmath=sse'] if output == 'collision319.exe' else (
                ['-std=gnu99', '-static-libgcc'] if output == 'ifs-read.exe' else
                ['-std=gnu99', '-shared', '-static-libgcc', '-lws2_32'])
            result = subprocess.run([cc, '-m32', '-O2', '-Wall', '-Wextra',
                '-o', str(stage / output), *[str(SOURCE / s) for s in sources], *flags],
                env=compiler_env(cc), capture_output=True, text=True, timeout=60)
            if result.returncode:
                raise RuntimeError('3.19 bridge requires x86 MinGW GCC:\n' + result.stderr)
        manifest = {'sources': inputs(), 'outputs': {p: digest(stage / p) for p in OUTPUTS}}
        (stage / 'native-build.json').write_text(json.dumps(manifest, indent=2) + '\n')
        directory.mkdir(parents=True, exist_ok=True)
        for name in (*OUTPUTS, 'native-build.json'):
            (stage / name).replace(directory / name)
    return directory
