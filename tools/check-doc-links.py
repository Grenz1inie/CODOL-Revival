"""Check this project's Markdown file links, including local evidence artifacts."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote

root = Path(__file__).resolve().parents[1]
documents = [root / 'README.md', root / 'CONTRIBUTING.md',
             *sorted((root / 'docs').rglob('*.md'))]
missing = []
checked = 0
for document in documents:
    for match in re.finditer(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', document.read_text(encoding='utf-8-sig')):
        target = match[1].strip('<>')
        if re.match(r'[a-zA-Z]+:', target) or target.startswith('#'):
            continue
        target = unquote(target.split('#', 1)[0])
        checked += 1
        if not (document.parent / target).exists():
            missing.append(f'{document.relative_to(root)}: {target}')
print(f'Checked {checked} local links; missing {len(missing)}.')
for item in missing:
    print(item)
sys.exit(bool(missing))
