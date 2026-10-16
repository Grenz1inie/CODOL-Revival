"""Read-only checks for the local launcher; no installers or configuration writes."""
from importlib import metadata
from pathlib import Path
import re
import sys


def check_environment(root):
    root = Path(root).resolve()
    errors = []
    if sys.version_info < (3, 11):
        errors.append('Python 3.11+ is required; this project is validated with Python 3.13.')
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

    required = [root / name for name in ('src/controller.py', 'src/manager/installations.py',
                'games/codol/versions.json', 'scripts/Start-Controller.ps1')]
    errors.extend(f'Missing file: {path}' for path in required if not path.is_file())
    build = f'Build the controller UI: cd "{root / "web"}"; npm ci; npm run build'
    index = root / 'web/dist/index.html'
    if not index.is_file():
        errors.append(build)
    else:
        for asset in re.findall(r'(?:src|href)=["\']([^"\']+)["\']', index.read_text(encoding='utf-8')):
            if asset.lstrip('/').startswith('assets/') and not (index.parent / asset.lstrip('/')).is_file():
                errors.append(f'Missing UI asset: {asset}. {build}')

    return errors


if __name__ == '__main__':
    problems = check_environment(Path(__file__).resolve().parents[1])
    for problem in problems: print('[FAIL] ' + problem)
    if not problems: print('[OK] Manager prerequisites passed.')
    sys.exit(bool(problems))
