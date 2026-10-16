"""Export retained REA pseudocode and shipped scripts for offline indexing."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def records(value):
    if isinstance(value, dict):
        if 'evidence_id' in value and 'normalized_result' in value:
            yield value
            return
        for key, child in value.items():
            if key == 'text' and isinstance(child, str):
                try:
                    yield from records(json.loads(child))
                except json.JSONDecodeError:
                    pass
            elif isinstance(child, (dict, list)):
                yield from records(child)
    elif isinstance(value, list):
        for child in value:
            yield from records(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', required=True, type=Path)
    args = parser.parse_args()
    game = args.game_root.resolve()
    binary = game / 'codoMP_client_shipRetail.exe'
    binary_hash = digest(binary.read_bytes())
    output = ROOT / 'research/client-code-index'
    functions = {}
    for source in sorted((ROOT / 'research/evidence').glob('*.json')):
        data = json.loads(source.read_text(encoding='utf-8-sig'))
        for record in records(data):
            if record.get('subject', {}).get('digest', {}).get('sha256') != binary_hash:
                continue
            result = record.get('normalized_result')
            if record.get('operation') != 'batch_decompile' or not isinstance(result, dict):
                continue
            for item in result.get('items', []):
                code = item.get('pseudocode')
                procedure = item.get('procedure', {})
                if not code or procedure.get('status') != 'resolved':
                    continue
                address = f"{int(procedure['address'], 16):08x}"
                code = code.replace('\r\n', '\n')
                code_hash = digest(code.encode())
                key = (address, code_hash)
                entry = functions.setdefault(key, {
                    'address': '0x' + address, 'symbol': procedure.get('name'),
                    'path': f'decompiled/{address}_{code_hash[:12]}.c',
                    'pseudocode_sha256': code_hash, 'evidence': [], 'code': code,
                })
                origin = {'file': source.relative_to(ROOT).as_posix(),
                          'evidence_id': record['evidence_id'],
                          'limitations': record.get('limitations', [])}
                if origin not in entry['evidence']:
                    entry['evidence'].append(origin)
    manifest = {'binary': str(binary), 'binary_sha256': binary_hash,
                'coverage': 'Retained batch_decompile results only; not full binary coverage.',
                'functions': [], 'shipped_files': []}
    for entry in sorted(functions.values(), key=lambda e: e['path']):
        code = entry.pop('code')
        target = output / entry['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        header = (f"// REA/Ghidra pseudocode; not original source or buildable C.\n"
                  f"// Binary SHA256: {binary_hash}\n"
                  f"// Address: {entry['address']}; provenance: ../manifest.json\n"
                  f"// Evidence: {entry['evidence'][0]['evidence_id']}\n")
        target.write_text(header + code, encoding='utf-8', newline='\n')
        manifest['functions'].append(entry)
    for source in sorted((game / 'IIPS/TPFUI').rglob('*')):
        if source.is_file() and source.suffix.lower() in {'.lua', '.h'}:
            relative = source.relative_to(game)
            target = output / 'shipped' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = source.read_bytes()
            target.write_bytes(raw)
            manifest['shipped_files'].append({'path': target.relative_to(output).as_posix(),
                                              'source': relative.as_posix(), 'sha256': digest(raw)})
    output.mkdir(parents=True, exist_ok=True)
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Exported {len(functions)} pseudocode variants and {len(manifest['shipped_files'])} shipped files to {output}")


if __name__ == '__main__':
    main()
