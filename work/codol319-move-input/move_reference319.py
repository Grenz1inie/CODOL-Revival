"""Reference model + fixture regeneration for the 3.19 Rust move input phase.

Two outputs (both written next to this script):
1. Real packet fixtures with usercmds decoded by the verified parser
   (client_message319), the baseline chained from the session's FIRST move
   packet so every window's first command is exact, and the conditional byte
   fields materialized (no implicit extras dict).
2. A golden trajectory from this reference movement model, which the Rust
   Movement must reproduce:
   - integrator: live_sim319's no-collision branch (Q3 friction 6.0 /
     accelerate 10.0 / stop speed 100 / max step 200 ms / z held at spawn),
     validated against the real 3.19 client in the Seatown phase;
   - wish scaling: collision_move319.wish_speed (C1 back 0.7 / strafe 0.8)
     plus sprint 1.5 while BUTTON_SPRINT(0x2) and forward are held;
   - angles: per-command short deltas accumulated onto the snapshot spawn
     orientation (the client sends usercmd angles relative to its spawn
     delta_angles; head yaw short was 0 while the spawn yaw was 330);
   - reconcile: adopt the move packet's predicted origin when its time equals
     the last executed command and it is within 16 units, as collision_move319.
"""
import json
import math
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'games/codol/versions/v3_19_26_22/server/match_host'))
import client_message319 as cm  # noqa: E402

PCAP = REPO / 'work/codol319-map-live-20261017/session.pcapng'
SPAWN = dict(origin=[-1601.8, 1176.2, -24.0], yaw=330.0)   # map-first-frame spawn, wiki 2026-10-17

FORWARD, BACK, RIGHT, LEFT = 1, 2, 4, 8
SPEED, FRICTION, ACCELERATE, STOP_SPEED, MAX_STEP = 190.0, 6.0, 10.0, 100.0, 0.2
BACK_SCALE, STRAFE_SCALE, SPRINT_SCALE, BUTTON_SPRINT = 0.7, 0.8, 1.5, 0x2
PITCH_LIMIT, PREDICTION_TOLERANCE = 85.0, 16.0


def wish_speed(fwd, right):
    if not fwd and not right:
        return 0.0
    f = 127.0 * fwd * (BACK_SCALE if fwd < 0 else 1.0)
    r = 127.0 * right * STRAFE_SCALE
    return SPEED * max(abs(f), abs(r)) / 127.0


def short_delta(new, old):
    return ((new - old + 0x8000) & 0xffff) - 0x8000


class ReferenceMovement:
    """The exact behaviour the Rust movement module must reproduce."""

    def __init__(self, origin, yaw):
        self.origin = [float(v) for v in origin]
        self.spawn_z = self.origin[2]
        self.velocity = [0.0, 0.0, 0.0]
        self.pitch, self.yaw = 0.0, float(yaw)
        self.command_time = 0
        self.last_pitch = None
        self.last_yaw = None
        self.applied = 0
        self.reconciles = []

    def apply(self, cmd):
        t = cmd['server_time']
        if t <= self.command_time:
            return False
        dt = 0.0 if not self.command_time else min(MAX_STEP, (t - self.command_time) / 1000.0)
        self.command_time = t
        self.applied += 1
        if self.last_pitch is not None:
            self.pitch = max(-PITCH_LIMIT, min(PITCH_LIMIT,
                self.pitch + short_delta(cmd['angles'][0], self.last_pitch) * 360.0 / 65536.0))
        if self.last_yaw is not None:
            self.yaw += short_delta(cmd['angles'][1], self.last_yaw) * 360.0 / 65536.0
        self.last_pitch, self.last_yaw = cmd['angles'][0], cmd['angles'][1]
        if dt <= 0:
            return True
        cls = cmd['move_class']
        fwd = (1 if cls & FORWARD else 0) - (1 if cls & BACK else 0)
        right = (1 if cls & RIGHT else 0) - (1 if cls & LEFT else 0)
        yaw = math.radians(self.yaw)
        fx, fy, rx, ry = math.cos(yaw), math.sin(yaw), math.sin(yaw), -math.cos(yaw)
        wx, wy = fx * fwd + rx * right, fy * fwd + ry * right
        length = math.hypot(wx, wy)
        speed = math.hypot(self.velocity[0], self.velocity[1])
        if speed > 0:
            drop = max(speed, STOP_SPEED) * FRICTION * dt
            scale = max(0.0, speed - drop) / speed
            self.velocity[0] *= scale
            self.velocity[1] *= scale
        wish = wish_speed(fwd, right)
        if cmd.get('buttons', 0) & BUTTON_SPRINT and fwd > 0:
            wish *= SPRINT_SCALE
        if length > 0 and wish > 0:
            dx, dy = wx / length, wy / length
            current = self.velocity[0] * dx + self.velocity[1] * dy
            add = wish - current
            if add > 0:
                accel = min(add, ACCELERATE * dt * max(wish, STOP_SPEED))
                self.velocity[0] += accel * dx
                self.velocity[1] += accel * dy
        self.origin[0] += self.velocity[0] * dt
        self.origin[1] += self.velocity[1] * dt
        self.origin[2] = self.spawn_z
        self.velocity[2] = 0.0
        return True

    def reconcile(self, predicted):
        xyz, t = predicted
        if t != self.command_time:
            return None
        d = math.dist(self.origin, xyz)
        if d <= PREDICTION_TOLERANCE:
            self.origin = list(xyz)
        self.reconciles.append((t, round(d, 3), d <= PREDICTION_TOLERANCE))
        return d


def materialize(c):
    extra = c['extra']
    return dict(server_time=c['server_time'], buttons=c['buttons'], angles=c['angles'],
                move_class=c['move_class'], w14=c['w14'], w16=c['w16'], w18=c['w18'],
                b20=c.get('b20', 0), w22=c.get('w22', 0),
                a1c=extra.get('a1c', 0), b24=extra.get('b24', 0), b25=extra.get('b25', 0),
                b26=extra.get('b26', 0), b27=extra.get('b27', 0), b28=extra.get('b28', 0))


def main():
    proc = subprocess.run(
        ['tshark', '-r', str(PCAP), '-Y', 'udp.srcport==58436 && udp.dstport==28970',
         '-T', 'fields', '-e', 'frame.number', '-e', 'udp.payload'],
        capture_output=True, text=True, check=True)
    baseline = None
    by_frame = {}
    order = []
    for line in proc.stdout.splitlines():
        frame, _, payload = line.partition('\t')
        if not payload:
            continue
        payload = bytes.fromhex(payload.replace(':', ''))
        if payload.startswith(b'\xff\xff\xff\xff'):
            continue
        parsed = cm.parse(payload, challenge=0, baseline=baseline)
        if not parsed or not parsed['move'] or parsed['move'].get('cmd_error'):
            continue
        baseline = parsed['move']['cmds'][-1]
        by_frame[int(frame)] = (payload, parsed)
        order.append(int(frame))

    def record(frame):
        payload, parsed = by_frame[frame]
        move = parsed['move']
        return dict(frame=frame, packet=payload.hex(),
                    sequence=parsed['sequence'], server_id=parsed['server_id'],
                    server_ack=parsed['server_ack'], command_ack=parsed['command_ack'],
                    commands=[[n, t] for n, t in parsed['commands']],
                    move=dict(delta=move['delta'], count=move['count'],
                              cmds=[materialize(c) for c in move['cmds']],
                              predicted=[[round(v, 4) for v in move['predicted'][0]],
                                         move['predicted'][1]] if move.get('predicted') else None))

    windows = dict(
        head=[f for f in order if f < 736][:40],
        moving=[f for f in order if 3420 <= f <= 3500],
        tail=[f for f in order if f >= order[-20]],
    )
    for name, frames in windows.items():
        rows = [record(f) for f in frames]
        out = Path(__file__).resolve().parent / f'move319-{name}.json'
        out.write_text(json.dumps(rows, separators=(',', ':')), encoding='utf-8')
        print(out.name, len(rows), 'records', frames[0], '..', frames[-1])

    # Golden trajectory: real moving window through the reference model.
    sim = ReferenceMovement(SPAWN['origin'], SPAWN['yaw'])
    trajectory = []
    for f in windows['moving']:
        _, parsed = by_frame[f]
        for c in parsed['move']['cmds']:
            if sim.apply(c):
                trajectory.append(dict(frame=f, t=c['server_time'],
                                       origin=[round(v, 4) for v in sim.origin],
                                       velocity=[round(v, 4) for v in sim.velocity],
                                       pitch=round(sim.pitch, 4), yaw=round(sim.yaw, 4)))
        if parsed['move'].get('predicted'):
            sim.reconcile((parsed['move']['predicted'][0], parsed['move']['predicted'][1]))
    # Same window with no predicted reports (what a live server whose snapshots
    # the client echoes would diverge to): pure integration of the real LEFT hold.
    solo = ReferenceMovement(SPAWN['origin'], SPAWN['yaw'])
    for f in windows['moving']:
        _, parsed = by_frame[f]
        for c in parsed['move']['cmds']:
            solo.apply(c)
    golden = dict(spawn=SPAWN, steps=trajectory, reconciles=sim.reconciles,
                  applied=sim.applied,
                  noreconcile=dict(steps=solo.applied,
                                   origin=[round(v, 4) for v in solo.origin],
                                   velocity=[round(v, 4) for v in solo.velocity],
                                   yaw=round(solo.yaw, 4), pitch=round(solo.pitch, 4)))

    # Snapshot byte references from the verified Python codec for states the
    # Rust Snapshot::set_player + encode must reproduce byte-for-byte.
    from snapshot_codec319 import encode as py_encode

    def snap(stamp, command, state):
        req = ' '.join(str(v) for v in (stamp, command, *state['origin'], *state['velocity'],
                                        state['pitch'], state['yaw']))
        return dict(stamp=stamp, command=command,
                    origin=state['origin'], velocity=state['velocity'],
                    pitch=state['pitch'], yaw=state['yaw'], hex=py_encode(req).hex())

    mid = trajectory[len(trajectory) // 2]
    end = dict(origin=golden['noreconcile']['origin'], velocity=golden['noreconcile']['velocity'],
               pitch=golden['noreconcile']['pitch'], yaw=golden['noreconcile']['yaw'])
    golden['snapshots'] = [
        snap(1000, 1000, dict(origin=SPAWN['origin'], velocity=[0.0, 0.0, 0.0], pitch=0.0, yaw=SPAWN['yaw'])),
        snap(mid['t'], mid['t'], dict(origin=mid['origin'], velocity=mid['velocity'],
                                      pitch=mid['pitch'], yaw=mid['yaw'])),
        snap(4000, end_origin_t := trajectory[-1]['t'], end),
        snap(5000, end_origin_t, dict(origin=[-1601.8, 1176.2, -24.0], velocity=[-100.0, 50.0, 0.0],
                                      pitch=-12.5, yaw=271.25)),
    ]
    golden['final'] = dict(origin=[round(v, 4) for v in sim.origin],
                           velocity=[round(v, 4) for v in sim.velocity],
                           pitch=round(sim.pitch, 4), yaw=round(sim.yaw, 4),
                           command_time=sim.command_time, applied=sim.applied)
    out = Path(__file__).resolve().parent / 'move319-trajectory.json'
    out.write_text(json.dumps(golden, separators=(',', ':')), encoding='utf-8')
    print(out.name, len(trajectory), 'steps,', len(sim.reconciles), 'reconciles')
    moved = trajectory[-1]['origin'] if trajectory else None
    print('start origin', trajectory[0]['origin'] if trajectory else None,
          'end origin', moved, 'end yaw', trajectory[-1]['yaw'] if trajectory else None)


if __name__ == '__main__':
    main()
