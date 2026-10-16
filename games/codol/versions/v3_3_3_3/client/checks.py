"""Read-only checks for the local launcher; no installers or configuration writes."""
from datetime import datetime, timezone
from importlib import metadata
import json
from pathlib import Path
import re
import ssl
import sys


def check_environment(root, game, runtime):
    root = Path(root).resolve()
    game, runtime = Path(game), Path(runtime)
    errors = []
    if sys.version_info < (3, 9):
        errors.append('Python 3.9+ is required; this project is validated with Python 3.13.')
    requirements = root / 'requirements.txt'
    if requirements.is_file():
        for line in requirements.read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            name, expected = line.strip().split('==')
            try:
                installed = metadata.version(name)
            except metadata.PackageNotFoundError:
                installed = 'missing'
            if installed != expected:
                errors.append(f'{name}: {installed}, expected {expected}. Run: '
                              f'& "{sys.executable}" -m pip install -r "{requirements}"')
    else:
        errors.append(f'Missing file: {requirements}')

    required = [root / name for name in (
        'games/codol/versions/v3_3_3_3/server/local_server.py', 'src/controller.py', 'games/codol/versions/v3_3_3_3/scripts/Start-Services.ps1',
        'scripts/Start-Controller.ps1', 'games/codol/versions/v3_3_3_3/scripts/Launch-Game.ps1',
        'games/codol/versions/v3_3_3_3/scripts/Control-Game.ps1', 'games/codol/versions/v3_3_3_3/scripts/Control-Services.ps1', 'games/codol/versions/v3_3_3_3/scripts/Stop-Game.ps1',
        'games/codol/versions/v3_3_3_3/resources/definitions/marketplace-catalog.json')]
    required += [runtime / 'certs' / name for name in ('ca.pem', 'server.pem', 'server-key.pem')]
    required += [game / name for name in ('codoMP_client_shipRetail.exe', 'dwauth.ini', 'stun.ini', 'cacert.pem')]
    errors.extend(f'Missing file: {path}' for path in required if not path.is_file())

    build = f'Build the controller UI: cd "{root / "web"}"; npm ci; npm run build'
    index = root / 'web/dist/index.html'
    if not index.is_file():
        errors.append(build)
    else:
        for asset in re.findall(r'(?:src|href)=["\']([^"\']+)["\']', index.read_text(encoding='utf-8')):
            if asset.lstrip('/').startswith('assets/') and not (index.parent / asset.lstrip('/')).is_file():
                errors.append(f'Missing UI asset: {asset}. {build}')

    for name, expected in (
        ('dwauth.ini', ['127.0.0.1', '3074', '127.0.0.1', '443', '0x03EA']),
        ('stun.ini', ['127.0.0.1']),
    ):
        path = game / name
        if path.is_file() and path.read_text(encoding='utf-8-sig').split() != expected:
            errors.append(f'{path}: expected {" ".join(expected)}. See docs/wiki/03-redirection-tls-auth.md.')

    settings = runtime / 'data/controller.json'
    if settings.is_file():
        try:
            value = json.loads(settings.read_text(encoding='utf-8-sig'))
            if not isinstance(value, dict) or type(value.get('skip_tutorial')) is not bool:
                raise ValueError('skip_tutorial must be a boolean')
        except ValueError as error:
            errors.append(f'{settings}: {error}')

    certificates = runtime / 'certs'
    if all((certificates / name).is_file() for name in ('ca.pem', 'server.pem', 'server-key.pem')):
        try:
            from cryptography import x509
            from cryptography.exceptions import InvalidSignature
        except ImportError as error:
            errors.append(f'Cannot load cryptography: {error}. Install requirements.txt with the selected Python.')
            return errors
        try:
            ca_pem = (certificates / 'ca.pem').read_bytes()
            ca = x509.load_pem_x509_certificate(ca_pem)
            server = x509.load_pem_x509_certificate((certificates / 'server.pem').read_bytes())
            now = datetime.now(timezone.utc)
            for name, cert in (('ca.pem', ca), ('server.pem', server)):
                if not cert.not_valid_before_utc <= now <= cert.not_valid_after_utc:
                    errors.append(f'{name}: certificate expired or not yet valid; check the clock and local certificates.')
            server.verify_directly_issued_by(ca)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.set_ciphers('ALL:@SECLEVEL=0')
            context.load_cert_chain(certificates / 'server.pem', certificates / 'server-key.pem')
            trust = game / 'cacert.pem'
            if trust.is_file() and ca_pem.replace(b'\r\n', b'\n').strip() not in trust.read_bytes().replace(b'\r\n', b'\n'):
                errors.append(f'{trust}: local CA is missing. See docs/wiki/03-redirection-tls-auth.md.')
        except (ValueError, OSError, TypeError, InvalidSignature) as error:
            errors.append(f'Local certificate check failed: {error or type(error).__name__}')
    return errors


if __name__ == '__main__':
    import os
    problems = check_environment(os.environ['CODOL_REPO_ROOT'], os.environ['CODOL_GAME_ROOT'], os.environ['CODOL_RUNTIME'])
    for problem in problems: print('[FAIL] ' + problem)
    sys.exit(bool(problems))
