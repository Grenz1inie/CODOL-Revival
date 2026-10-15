"""Export selected REA/Ghidra evidence into address-stable feature packages."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASELINE = json.loads((ROOT / 'evidence/baseline.json').read_text(encoding='utf-8'))
CATALOG = json.loads((ROOT / 'maintenance/catalog.json').read_text(encoding='utf-8'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


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


def normalized(code):
    return re.sub(r'\r+\n', '\n', code)


def main():
    binary = Path(BASELINE['binary'])
    assert sha(binary.read_bytes()) == BASELINE['binary_sha256'], 'Target binary changed'
    selected = {address: (package, label) for package, group in CATALOG.items()
                for address, label in group['functions'].items()}
    found = {address: {} for address in selected}
    prefixes = ('auth-parser-', 'lobby-keys-', 'controller-', 'expansion-',
                'dwprofile-', 'onboard-', 'onboarding-')
    sources = [p for p in sorted((REPO / 'research/evidence').glob('*.json'))
               if p.name.startswith(prefixes) and not p.name.endswith('.rea.json')]
    sources += sorted((ROOT / 'evidence/fresh').glob('*.json'))
    retained = {}
    for source in sources:
        raw = source.read_bytes()
        document = json.loads(raw.decode('utf-8-sig'))
        for record in records(document):
            if (record.get('subject') or {}).get('digest', {}).get('sha256') != BASELINE['binary_sha256']:
                continue
            if record.get('operation') != 'batch_decompile':
                continue
            for item in record['normalized_result'].get('items', []):
                procedure = item.get('procedure', {})
                if item.get('status') != 'ok' or procedure.get('status') != 'resolved':
                    continue
                address = f"{int(procedure['address'], 16):08x}"
                if address not in selected or not item.get('pseudocode'):
                    continue
                code = normalized(item['pseudocode'])
                code_hash = sha(code.encode())
                entry = found[address].setdefault(code_hash, {
                    'symbol': procedure['name'], 'code': code, 'origins': []})
                origin = {'source': source.relative_to(REPO).as_posix(),
                          'source_kind': 'rea-evidence',
                          'source_sha256': sha(raw), 'evidence_id': record['evidence_id'],
                          'record': f"evidence/records/{record['evidence_id']}.json",
                          'analysis_profile': record.get('analysis_profile'),
                          'collection': 'current-session' if source.is_relative_to(ROOT) else 'retained-history'}
                if origin not in entry['origins']:
                    entry['origins'].append(origin)
                retained[record['evidence_id']] = record
    for source in sorted((ROOT / 'evidence/focused').glob('*.json')):
        raw = source.read_bytes()
        report = json.loads(raw.decode('utf-8-sig'))
        if report.get('producer') != 'standalone-ghidra-focused-script':
            continue
        assert report['binary_sha256'] == BASELINE['binary_sha256']
        for item in report['items']:
            if item.get('status') != 'ok':
                continue
            address = f"{int(item['address'], 16):08x}"
            if address not in selected:
                continue
            code = normalized(item['pseudocode'])
            entry = found[address].setdefault(sha(code.encode()), {
                'symbol': item['name'], 'code': code, 'origins': []})
            entry['origins'].append({'source': source.relative_to(REPO).as_posix(),
                'source_kind': 'standalone-ghidra', 'source_sha256': sha(raw),
                'record': source.relative_to(ROOT).as_posix(), 'evidence_id': None,
                'direct_call_targets': item.get('direct_call_targets', []),
                'collection': 'current-session-focused',
                'analysis_profile': {'provider': 'Ghidra', 'version': report['ghidra_version'],
                                     'mode': report['analysis_mode'], 'limitations': report['limitations']}})
    for evidence_id, record in retained.items():
        save(ROOT / f'evidence/records/{evidence_id}.json', record)
    manifest = {'schema_version': 1, 'binary': str(binary),
                'binary_sha256': BASELINE['binary_sha256'], 'image_base': '0x00400000',
                'address_kind': 'preferred-image virtual address; RVA = VA - image_base',
                'normalization': 'CRLF or CRCRLF to LF only; code identifiers and statements unchanged',
                'coverage': 'Curated key functions, not complete original source or all dependencies',
                'functions': [], 'missing': []}
    index = ['# 关键功能索引', '', '按功能查找入口，再沿地址读取伪代码和证据。业务名称为分析标签；地址与原始符号保留。', '',
             '[使用说明](README.md) · [机器索引](function-index.json) · [维护方法](MAINTENANCE.md)', '']
    for package, group in CATALOG.items():
        directory = Path('codol/client') / package.replace('.', '/')
        lines = [f"# {group['title']}", '', f"逻辑包：`codol.client.{package}`", '',
                 '本目录保存 REA/Ghidra 伪代码，业务标签由分析者添加。完整来源、代码哈希和变体见根目录 function-index.json。', '',
                 '| 地址 | 功能标签 | 代码 |', '|---|---|---|']
        index += [f"## {group['title']}", '', f"包：`codol.client.{package}`", '',
                  '| 地址 | 功能标签 | 来源 |', '|---|---|---|']
        for address, label in group['functions'].items():
            variants = found[address]
            if not variants:
                manifest['missing'].append({'address': '0x' + address, 'label': label, 'package': package})
                index.append(f'| 0x{address} | {label} | 尚缺可用伪代码 |')
                continue
            ordered = sorted(variants.items(), key=lambda pair: (
                not any(o['source_kind'] == 'rea-evidence' for o in pair[1]['origins']),
                not any(o['collection'] == 'current-session' for o in pair[1]['origins']), pair[0]))
            function = {'address': '0x' + address, 'rva': hex(int(address, 16) - 0x400000),
                        'label': label, 'label_authority': 'analyst-inference',
                        'package': 'codol.client.' + package, 'variants': []}
            for number, (code_hash, entry) in enumerate(ordered):
                filename = f'FUN_{address}.c' if number == 0 else f'FUN_{address}.{code_hash[:12]}.c'
                relative = (directory / filename).as_posix()
                header = (f'// REA/Ghidra pseudocode; not original or directly buildable source.\n'
                          f'// Package: codol.client.{package}\n// Analyst label: {label}\n'
                          f'// VA: 0x{address}; binary SHA256: {BASELINE["binary_sha256"]}\n'
                          f'// Evidence: {entry["origins"][0]["evidence_id"] or entry["origins"][0]["record"]}\n// BEGIN PSEUDOCODE\n')
                target = ROOT / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(header + entry['code'], encoding='utf-8', newline='\n')
                function['variants'].append({'path': relative, 'pseudocode_sha256': code_hash,
                                            'file_sha256': sha(target.read_bytes()), 'origins': entry['origins']})
                if number == 0:
                    function.update({'path': relative, 'symbol': entry['symbol'],
                        'warnings': re.findall(r'/\*.*?WARNING:.*?\*/', entry['code'], re.S),
                        'textual_call_candidates': sorted({'0x' + x.lower() for x in
                            re.findall(r'\b(?:FUN_|func_0x)([0-9a-fA-F]{8})\s*\(', entry['code']) if x.lower() != address})})
            manifest['functions'].append(function)
            source_kind = ('Ghidra 定向分析' if all(o['source_kind'] == 'standalone-ghidra' for o in ordered[0][1]['origins'])
                           else 'REA 本次会话' if any(o['collection'] == 'current-session' for o in ordered[0][1]['origins']) else 'REA 历史证据')
            index.append(f'| [0x{address}]({function["path"]}) | {label} | {source_kind} |')
            lines.append(f'| 0x{address} | {label} | [伪代码](FUN_{address}.c) |')
        index.append('')
        (ROOT / directory / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    save(ROOT / 'function-index.json', manifest)
    (ROOT / 'INDEX.md').write_text('\n'.join(index) + '\n', encoding='utf-8')
    print(json.dumps({'functions': len(manifest['functions']), 'records': len(retained),
                      'variants': sum(len(f['variants']) for f in manifest['functions']),
                      'missing': manifest['missing']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
