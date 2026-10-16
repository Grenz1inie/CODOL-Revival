"""Build static call-site indexes from retained focused Ghidra observations."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def address(value):
    return f'0x{int(value, 16):08x}'


def build(index):
    functions = {f['address']: f for f in index['functions']}
    observations = []
    for path in sorted((ROOT / 'evidence/focused').glob('*.json')):
        raw = path.read_bytes()
        report = json.loads(raw)
        if report.get('producer') != 'standalone-ghidra-focused-script':
            continue
        assert report['binary_sha256'] == index['binary_sha256']
        for item in report['items']:
            if item.get('status') != 'ok' or 'call_sites' not in item:
                continue
            entry = address(item['address'])
            if entry not in functions:
                continue
            calls = []
            for site in item['call_sites']:
                assert any(line == site['address'][2:] + ' ' + site['instruction']
                           for line in item['instructions'])
                resolved = not site['computed'] and len(site['targets']) == 1
                calls.append({'site': address(site['address']),
                              'instruction': site['instruction'],
                              'kind': 'direct' if resolved else 'unresolved-indirect',
                              'target': address(site['targets'][0]) if resolved else None,
                              'provider_targets': [address(a) for a in site['targets']]})
            observations.append({'function': entry, 'body': item['body'],
                                 'record': path.relative_to(ROOT).as_posix(),
                                 'record_sha256': hashlib.sha256(raw).hexdigest(),
                                 'calls': calls})
    callees = {a: set() for a in functions}
    callers = {a: set() for a in functions}
    observed = {o['function'] for o in observations}
    for observation in observations:
        for call in observation['calls']:
            if call['kind'] == 'direct':
                callees[observation['function']].add(call['target'])
                if call['target'] in callers:
                    callers[call['target']].add(observation['function'])
    for entry, function in functions.items():
        function['call_coverage'] = 'focused-static-instructions' if entry in observed else 'not-collected'
        function['verified_direct_callees'] = sorted(callees[entry])
        function['verified_direct_callers'] = sorted(callers[entry])
    direct = [c for o in observations for c in o['calls'] if c['kind'] == 'direct']
    graph = {'schema_version': 1, 'binary_sha256': index['binary_sha256'],
             'authority': 'shipped-artifact', 'execution_observed': False,
             'coverage': {'functions_with_call_sites': len(observed),
                          'function_observations': len(observations),
                          'direct_call_observations': len(direct),
                          'unresolved_indirect_observations': sum(
                              c['kind'] != 'direct' for o in observations for c in o['calls']),
                          'direct_targets_outside_index': sorted({c['target'] for c in direct
                                                                 if c['target'] not in functions})},
             'limitations': ['Focused analysis without whole-program auto-analysis.',
                             'Calls from all retained body variants; duplicates are observations, not unique edges.',
                             'Caller lists cover only observed bodies, not all incoming calls in the executable.',
                             'Indirect calls, callbacks, tail jumps and runtime feasibility are not resolved by this index.'],
             'observations': observations}
    (ROOT / 'call-chains.json').write_text(json.dumps(graph, ensure_ascii=False, indent=2) + '\n',
                                         encoding='utf-8', newline='\n')
    return graph
