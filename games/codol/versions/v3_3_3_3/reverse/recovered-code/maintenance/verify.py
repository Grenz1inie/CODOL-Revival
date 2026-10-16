"""Verify exported pseudocode, evidence provenance, links and preserved inputs."""
import hashlib
import json
import re
import struct
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[5]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    baseline = json.loads((ROOT / 'evidence/baseline.json').read_text(encoding='utf-8'))
    index = json.loads((ROOT / 'function-index.json').read_text(encoding='utf-8'))
    errors = []
    variants = 0
    origins = 0
    links = 0
    binary = Path(baseline['binary']).read_bytes()
    if sha(binary) != baseline['binary_sha256']:
        errors.append('Game executable hash changed')
    pe = struct.unpack_from('<I', binary, 0x3c)[0]
    if binary[pe:pe + 4] != b'PE\0\0' or struct.unpack_from('<H', binary, pe + 24)[0] != 0x10b:
        errors.append('Target is not the expected PE32 image')
    if struct.unpack_from('<I', binary, pe + 24 + 28)[0] != int(index['image_base'], 16):
        errors.append('PE image base mismatch')
    seen = set()
    for function in index['functions']:
        address = function['address']
        if address in seen:
            errors.append('Duplicate function ' + address)
        seen.add(address)
        for variant in function['variants']:
            variants += 1
            raw = (ROOT / variant['path']).read_bytes()
            body = raw.split(b'// BEGIN PSEUDOCODE\n', 1)[1]
            if sha(raw) != variant['file_sha256'] or sha(body) != variant['pseudocode_sha256']:
                errors.append('Code hash mismatch ' + variant['path'])
            for origin in variant['origins']:
                origins += 1
                source = REPO / origin['source']
                if sha(source.read_bytes()) != origin['source_sha256']:
                    errors.append('Origin changed ' + origin['source'])
                record = json.loads((ROOT / origin['record']).read_text(encoding='utf-8'))
                if origin['source_kind'] == 'standalone-ghidra':
                    if record['producer'] != 'standalone-ghidra-focused-script' or record['binary_sha256'] != index['binary_sha256']:
                        errors.append('Focused evidence identity mismatch ' + origin['record'])
                    items = record['items']
                    candidates = [item for item in items if item.get('status') == 'ok'
                                  and int(item['address'], 16) == int(address, 16)]
                else:
                    if record['evidence_id'] != origin['evidence_id'] or record['subject']['digest']['sha256'] != index['binary_sha256']:
                        errors.append('Evidence identity mismatch ' + origin['record'])
                    candidates = [item for item in record['normalized_result']['items']
                                  if item.get('procedure', {}).get('status') == 'resolved'
                                  and int(item['procedure']['address'], 16) == int(address, 16)]
                matching = [item for item in candidates
                            if sha(re.sub(r'\r+\n', '\n', item.get('pseudocode', '')).encode()) == sha(body)]
                if not matching:
                    errors.append('Export not found in evidence ' + variant['path'])
    for entry in json.loads((ROOT / 'evidence/support/manifest.json').read_text(encoding='utf-8')):
        if sha((ROOT / entry['copy']).read_bytes()) != entry['sha256']:
            errors.append('Supporting evidence hash mismatch ' + entry['copy'])
    expected_files = {v['path'] for f in index['functions'] for v in f['variants']}
    actual_files = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'codol').rglob('*.c')}
    if expected_files != actual_files:
        errors.append('Unindexed or missing pseudocode files')
    graph = json.loads((ROOT / 'call-chains.json').read_text(encoding='utf-8'))
    if graph['binary_sha256'] != index['binary_sha256'] or graph['execution_observed']:
        errors.append('Call graph target or authority mismatch')
    call_checks = 0
    outgoing = {f['address']: set() for f in index['functions']}
    incoming = {a: set() for a in outgoing}
    for observation in graph['observations']:
        raw = (ROOT / observation['record']).read_bytes()
        if sha(raw) != observation['record_sha256']:
            errors.append('Call observation source changed ' + observation['record'])
        record = json.loads(raw)
        item = next(i for i in record['items']
                    if int(i['address'], 16) == int(observation['function'], 16))
        if len(observation['calls']) != len(item['call_sites']):
            errors.append('Call sites omitted ' + observation['function'])
        for call, site in zip(observation['calls'], item['call_sites']):
            call_checks += 1
            direct = not site['computed'] and len(site['targets']) == 1
            target = f"0x{int(site['targets'][0], 16):08x}" if direct else None
            if (int(call['site'], 16) != int(site['address'], 16)
                    or call['instruction'] != site['instruction']
                    or call['target'] != target
                    or call['kind'] != ('direct' if direct else 'unresolved-indirect')
                    or site['address'][2:] + ' ' + site['instruction'] not in item['instructions']):
                errors.append('Call site differs from instructions ' + call['site'])
            if direct:
                outgoing[observation['function']].add(target)
                if target in incoming:
                    incoming[target].add(observation['function'])
    for function in index['functions']:
        if (function['verified_direct_callees'] != sorted(outgoing[function['address']])
                or function['verified_direct_callers'] != sorted(incoming[function['address']])):
            errors.append('Function call index mismatch ' + function['address'])
    for document in ROOT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', document.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            links += 1
            linked = document.parent / target.split('#')[0]
            if linked.resolve() == (ROOT / 'verification.json').resolve():
                continue  # This report is written by the current verification run.
            if not linked.exists():
                errors.append(f'Broken link {document.relative_to(ROOT)} -> {target}')
    changed = [path for path, digest in baseline['tracked_files'].items()
               if not (REPO / path).exists() or sha((REPO / path).read_bytes()) != digest]
    if index['missing']:
        errors.append('Selected functions still missing')
    report = {'verified_at_utc': datetime.now(timezone.utc).isoformat(),
              'passed': not errors, 'functions': len(seen), 'variants': variants,
              'origin_checks': origins, 'local_links': links,
              'call_site_checks': call_checks,
              'call_graph_coverage': graph['coverage'],
              'binary_sha256': sha(binary), 'binary_unchanged': sha(binary) == baseline['binary_sha256'],
              'preexisting_tracked_files_checked': len(baseline['tracked_files']),
              'preexisting_tracked_files_changed': changed,
              'workspace_baseline_matches': not changed,
              'git_status': subprocess.check_output(['git', 'status', '--short'], cwd=REPO).decode(),
              'missing_functions': index['missing'], 'errors': errors,
              'limits': ['Static export verification only; no game runtime or compilation test.',
                         'Workspace drift is reported separately; this check cannot attribute changes to another task.',
                         'Game immutability hash check covers the target EXE, not every game resource.']}
    (ROOT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
