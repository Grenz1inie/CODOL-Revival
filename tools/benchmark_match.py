"""Deterministic migration oracle; no live socket, profile or game writes."""
import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import subprocess
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tools')]


def percentiles(samples):
    values = sorted(samples)
    if not values:
        raise ValueError('timing samples required')
    return dict(count=len(values), p50_ms=values[math.ceil(len(values)*.50)-1],
                p95_ms=values[math.ceil(len(values)*.95)-1],
                p99_ms=values[math.ceil(len(values)*.99)-1], max_ms=values[-1])


def scenario(weapon):
    now, frames = 1000, []
    for i in range(400):
        elapsed = 125 if i == 120 else 50
        now += elapsed
        commands = []
        if not 240 <= i < 260:  # menu pause, then fresh input resumes
            direction = 1 if i % 120 < 50 else 2 if i % 120 < 100 else 0
            buttons = 16 if i in (90, 190, 290) else 1 if 30 <= i % 100 < 60 else 0
            if i in (10, 150, 320):
                buttons |= 1024
            commands = [dict(time=now, weapon=weapon, direction=direction,
                             buttons=buttons, yaw=32768, pitch=0)]
        frames.append(dict(milliseconds=elapsed, commands=commands))
    return dict(schema=1, frames=frames)


def compare_states(expected, actual, path='state'):
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and expected.keys() == actual.keys(), path + ' keys'
        for key in expected:
            compare_states(expected[key], actual[key], path + '.' + key)
    elif isinstance(expected, (list, tuple)):
        assert isinstance(actual, (list, tuple)) and len(expected) == len(actual), path + ' length'
        for i, (left, right) in enumerate(zip(expected, actual)):
            compare_states(left, right, f'{path}[{i}]')
    elif isinstance(expected, float):
        assert math.isfinite(actual) and abs(expected-actual) <= 1e-6, f'{path}: {expected} != {actual}'
    else:
        assert expected == actual, f'{path}: {expected} != {actual}'


def compare_frames(expected, actual):
    """Float state is numeric; integer fields remain exact, wire parity is reported."""
    float_fields = {'8','10','11','13','14','16','18','19','30','34','217'}
    assert len(expected) == len(actual), 'frame count'
    for i, (left, right) in enumerate(zip(expected, actual)):
        for key in ('time', 'players'):
            compare_states(left[key], right[key], f'frame[{i}].{key}')
        assert left['fields'].keys() == right['fields'].keys(), 'snapshot fields'
        for key, value in left['fields'].items():
            other = right['fields'][key]
            if key in float_fields:
                value, other = [struct.unpack('<f', struct.pack('<I', v))[0] for v in (value, other)]
            compare_states(value, other, f'frame[{i}].fields.{key}')
    return sum(a['wire'] == b['wire'] for a, b in zip(expected, actual))


def python_replay(package, inputs):
    from match_server.runtime import load_world
    start = time.perf_counter()
    world = load_world(package)
    startup = (time.perf_counter()-start)*1000
    output, step_ms, snapshot_ms, frame_ms = [], [], [], []
    for frame in inputs['frames']:
        begin = time.perf_counter()
        world.step(frame['commands'], milliseconds=frame['milliseconds'])
        simulated = time.perf_counter()
        wire, fields = world.snapshot()
        end = time.perf_counter()
        step_ms.append((simulated-begin)*1000)
        snapshot_ms.append((end-simulated)*1000)
        frame_ms.append((end-begin)*1000)
        output.append(dict(time=world.time, players=[asdict(p) for p in world.players],
                           fields={str(k): v for k, v in fields.items()}, wire=wire.hex()))
    return dict(engine='python', startup_ms=startup, states=output,
                step_ms=step_ms, snapshot_ms=snapshot_ms, frame_ms=frame_ms)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=ROOT/'runtime/match/nuketown')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rust', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((args.package/'manifest.json').read_text('utf-8'))
    ncs = json.loads((args.package/'ncs.json').read_text('utf-8'))
    registry = ncs['registry']['kinds']['13']
    inputs = scenario(registry['reserved']+len(registry['strings']))
    scenario_path = args.output/'scenario.json'
    scenario_path.write_text(json.dumps(inputs), encoding='utf-8')
    baseline_path = args.output/'python.json'
    # Reuse the frozen baseline on later stages; never benchmark a changed input silently.
    identity = dict(map=manifest['map'], files=manifest['files'], scenario=inputs)
    identity_path = args.output/'identity.json'
    if baseline_path.exists():
        if json.loads(identity_path.read_text('utf-8')) != identity:
            raise ValueError('baseline map/input changed; use a new output directory')
        baseline = json.loads(baseline_path.read_text('utf-8'))
    else:
        baseline = python_replay(args.package, inputs)
        baseline_path.write_text(json.dumps(baseline), encoding='utf-8')
        identity_path.write_text(json.dumps(identity), encoding='utf-8')
    report = dict(map=manifest['map'], frames=len(inputs['frames']), python={
        name: percentiles(baseline[name]) for name in ('step_ms','snapshot_ms','frame_ms')})
    if args.rust:
        result = subprocess.run([str(args.rust.resolve()), 'replay', '--package', str(args.package.resolve()),
                                 '--scenario', str(scenario_path.resolve())],
                                check=True, capture_output=True, text=True, encoding='utf-8')
        native = json.loads(result.stdout)
        (args.output/'rust.json').write_text(json.dumps(native), encoding='utf-8')
        report['wire_identical_frames'] = compare_frames(baseline['states'], native['states'])
        report['states_equal'] = True
        report['rust'] = {name: percentiles(native[name]) for name in ('step_ms','snapshot_ms','frame_ms')}
    (args.output/'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
