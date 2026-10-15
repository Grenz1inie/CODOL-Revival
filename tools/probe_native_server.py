"""Bounded isolated native-map regression; never launches the game client."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from native_server import NativeServer


def main(root=ROOT, *, mode='story'):
    server = NativeServer(root, port=28971, mode=mode)
    ready = False
    try:
        try:
            # Keep the original diagnostic probe's empty connection material.
            server.start(security_id=bytes.fromhex('4600000000000000'),
                         profile_path='', admission_path='', key_path='')
            ready = server.ready
        except RuntimeError:
            if server.process is None:
                raise
    finally:
        server.close()
    home = server.home
    result = dict(command=server.command, home=str(home), reason=server.reason, ready=ready,
                  executable_sha256=server.manifest['executable_sha256'],
                  patch_sha256=server.manifest['patch_sha256'],
                  returncode=server.process.returncode, gameplay_verified=False)
    (home / 'probe.json').write_text(json.dumps(result, indent=2))
    (Path(root) / 'research/evidence/server3333-startup-latest.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    for name in ['console.log', 'main/qconsole.log', 'sys_error.txt']:
        p = home / name
        if p.exists():
            print(name + '\n' + p.read_text(errors='backslashreplace')[-6500:])
    assert ready, server.reason


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pvp', action='store_true')
    main(mode='pvp' if parser.parse_args().pvp else 'story')
