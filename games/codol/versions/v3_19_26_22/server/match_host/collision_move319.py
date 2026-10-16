"""Collision movement mixed into LiveSim (Q3 PM_GroundTrace / PM_SlideMove / PM_StepSlideMove)."""
import json
import math
import struct
import subprocess
import os
from pathlib import Path

ROOT = Path(os.environ['CODOL319_SERVER_ROOT']) / 'match-host'
GRAVITY = 800.0        # ps gravity (profile idx 63) sent to the client
STEPSIZE = 18.0
MIN_WALK_NORMAL = 0.7
OVERCLIP = 1.001
PLAYER_MINS = (-15.0, -15.0, 0.0)
PLAYER_MAXS = (15.0, 15.0, 70.0)
ENTITYNUM_WORLD, ENTITYNUM_NONE = 2046, 2047
# CoD ground movement (engine-reference codol_pmove_c1_ground.c: PM_Friction
# 0x0040fb70, PM_Accelerate 0x0040fc91, PM_CmdScale): friction 5.5, stop speed
# 100, ground accel 9 (standing), air accel 1, accel step = frametime * accel *
# max(wishspeed, 100); back moves x0.7, strafe x0.8, wish = speed * max/127.
C1_FRICTION = 5.5
C1_STOPSPEED = 100.0
C1_GROUND_ACCEL = 9.0
C1_AIR_ACCEL = 1.0
BACK_SCALE, STRAFE_SCALE = 0.7, 0.8
C1_STEP_HEIGHT = 18.0
C1_JUMP_HEIGHT = 39.0          # jump_height default (engine-reference g_sv_main.c:425)
C1_JUMP_INTERVAL_MS = 500      # PM_CheckJump: serverTime - jumpTime >= 500
SPRINT_SCALE = 1.5             # PMF_SPRINTING (0x4000) PM_CmdScale
BUTTON_SPRINT, BUTTON_JUMP = 0x2, 0x400
# Mantle (C1 bg_mantle / engine-reference codol_pmove_c1_mantle.c). Seatown mantle brushes:
# material mantle_on, contents 0x01000000, surfaceFlags 0x02000000 (no mantle-over surfaces).
PMF_MANTLE, PMF_JUMPING, PMF_SPRINTING = 0x4, 0x2000, 0x4000
PMF_ADS_BITS = 0x50           # ADS 0x40 | ADS button 0x10 (client-owned)
# Sprint is client-owned too: the client's own sprint meter/cooldown decides PMF_SPRINTING
# (speed > 200 only with its 0x4000, ps-record319-fire.bin); the host follows it.
PMF_CLIENT_BITS = PMF_ADS_BITS | PMF_SPRINTING
PMF_HOST_BITS = PMF_MANTLE | PMF_JUMPING   # the host runs mantles and jumps
EF_MANTLE = 0x10000
MANTLE_HEIGHTS = (57.0, 51.0, 45.0, 39.0, 33.0, 27.0, 21.0)   # s_mantleTrans heights, index 0..6
MANTLE_LEDGE_SOLID, MANTLE_END_CLEAR, MANTLE_HINT = 0x02, 0x04, 0x08
# Mantle length per transition (the up animation; Seatown has no mantle-over surfaces).
# Measured from the client's own timer: transition 2 ended at exactly 600 ms (run 085708Z),
# transition 3 was still running at 599 ms (run 090226Z). The host must end at the same
# time and never send a timer beyond it: past the up length with no over animation the
# client divides by a zero over length (C1 Mantle_GetAnimDelta) and stops sending.
MANTLE_TOTAL_MS = {i: 600 for i in range(7)}
# Ladders: brushes with a SURF_LADDER (0x8) face (clipmap_materials319.py --ladders-json; Seatown
# has three). While the player is against one the host stops gravity, climbs with forward/back
# (down when looking steeply down) and follows the client's reported origin, as for mantles.
LADDER_FILE = ROOT / 'collision319' / 'ladders-mp_seatown.json'
LADDER_REACH = 20.0            # horizontal distance from the ladder brush (player half-width 15 + 5)
LADDER_SPEED = 110.0           # climb speed, units/s
LADDER_DOWN_PITCH = 30.0       # looking further down than this, forward climbs down
try:
    LADDERS = json.loads(LADDER_FILE.read_text(encoding='utf-8'))
except (OSError, ValueError):
    LADDERS = []
PREDICTION_TOLERANCE = 16.0   # units; larger disagreements are corrected by the host
C1_GROUND_SNAP = 9.0


def wish_speed(speed, fwd, right, weapon_scale):
    """PM_CmdScale for keyboard moves (+-127 per axis): speed * max(|f'|,|r'|)/127 * weapon scale."""
    if not fwd and not right:
        return 0.0
    f = 127.0 * fwd * (BACK_SCALE if fwd < 0 else 1.0)
    r = 127.0 * right * STRAFE_SCALE
    return speed * max(abs(f), abs(r)) / 127.0 * weapon_scale


class Collision:
    """Pipe to collision319.exe: box sweeps against the captured clipMap."""
    def __init__(self, clipmap, exe=None):
        exe = exe or ROOT / 'mainframe-verification/collision319.exe'
        self.proc = subprocess.Popen([str(exe), str(clipmap)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1,
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        ready = self.proc.stdout.readline()
        if not ready.startswith('READY'):
            raise ValueError('collision319: ' + ready)
        self.traces = 0

    def trace(self, start, end, mins=PLAYER_MINS, maxs=PLAYER_MAXS):
        """Returns (fraction, endpos, normal, startsolid, allsolid).
        The player hull (PLAYER_MINS/MAXS) is swept as a capsule of radius 15 from
        z 0 to 70, as the 3.19 client does (run 082740Z: ramps and angled clips
        only fit a capsule); other bounds are swept as boxes."""
        self.traces += 1
        if tuple(mins) == PLAYER_MINS and tuple(maxs) == PLAYER_MAXS:
            line = 'C ' + ' '.join('%.4f' % v for v in (*start, *end, maxs[0], mins[2], maxs[2]))
        else:
            line = 'T ' + ' '.join('%.4f' % v for v in (*start, *end, *mins, *maxs))
        self.proc.stdin.write(line + '\n')
        self.proc.stdin.flush()
        f, nx, ny, nz, ss, als = self.proc.stdout.readline().split()
        f = float(f)
        endpos = [s + (e - s) * f for s, e in zip(start, end)]
        return f, endpos, (float(nx), float(ny), float(nz)), ss == '1', als == '1'

    def mantle_trace(self, start, end):
        """Thin box (+-0.1, z 0..70) against CONTENTS_MANTLE brushes (collision319 'M')."""
        self.traces += 1
        self.proc.stdin.write('M ' + ' '.join('%.4f' % v for v in (*start, *end)) + '\n')
        self.proc.stdin.flush()
        f, nx, ny, nz, ss, als = self.proc.stdout.readline().split()
        return float(f), (float(nx), float(ny), float(nz)), ss == '1', als == '1'

    def close(self):
        if self.proc.poll() is None:
            self.proc.stdin.close(); self.proc.wait(timeout=5)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _project(v, n):
    """C1 PM_ProjectVelocity: put v on the plane by solving z, keeping the speed."""
    d2 = v[0] * v[0] + v[1] * v[1]
    if abs(n[2]) < 0.001 or d2 == 0.0:
        return list(v)
    new_z = -(n[0] * v[0] + n[1] * v[1]) / n[2]
    denom = new_z * new_z + d2
    if denom == 0.0:
        return list(v)
    scale = math.sqrt((v[2] * v[2] + d2) / denom)
    if scale < 1.0 or new_z < 0.0 or v[2] > 0.0:
        return [v[0] * scale, v[1] * scale, new_z * scale]
    return list(v)


def _clip(v, n, overbounce=OVERCLIP):
    backoff = _dot(v, n)
    backoff = backoff * overbounce if backoff < 0 else backoff / overbounce
    return [v[i] - n[i] * backoff for i in range(3)]


class CollisionMovement:
    """Needs self.origin, self.velocity, self.collision; sets self.ground / self.ground_normal."""

    def _ground_trace(self):
        o = self.origin
        f, end, n, ss, als = self.collision.trace(o, [o[0], o[1], o[2] - 0.25])
        if als or f == 1.0 or n[2] < MIN_WALK_NORMAL or (self.velocity[2] > 0 and _dot(self.velocity, n) > 10):
            self.ground, self.ground_normal = ENTITYNUM_NONE, None
            return False
        self.ground, self.ground_normal = ENTITYNUM_WORLD, n
        self.origin = end
        return True

    def _slide(self, dt, gravity):
        """PM_SlideMove; returns True if anything was hit."""
        planes, end_velocity = [], None
        if gravity:
            end_velocity = list(self.velocity); end_velocity[2] -= GRAVITY * dt
            self.velocity[2] = (self.velocity[2] + end_velocity[2]) * 0.5
            if self.ground_normal:
                self.velocity = _clip(self.velocity, self.ground_normal)
        if self.ground_normal:
            planes.append(self.ground_normal)
        n = math.sqrt(_dot(self.velocity, self.velocity))
        if n:
            planes.append([v / n for v in self.velocity])
        time_left, hit = dt, False
        for _ in range(4):
            end = [self.origin[i] + self.velocity[i] * time_left for i in range(3)]
            f, endpos, normal, ss, als = self.collision.trace(self.origin, end)
            if als:
                self.velocity[2] = 0.0
                return True
            if f > 0:
                self.origin = endpos
            if f == 1.0:
                break
            hit = True
            time_left -= time_left * f
            if len(planes) >= 5:
                self.velocity = [0.0, 0.0, 0.0]
                return True
            if any(_dot(normal, p) > 0.99 for p in planes):
                self.velocity = [self.velocity[i] + normal[i] for i in range(3)]
                continue
            planes.append(normal)
            for i, p in enumerate(planes):
                if _dot(self.velocity, p) >= 0.1:
                    continue
                clip = _clip(self.velocity, p)
                end_clip = _clip(end_velocity, p) if end_velocity else None
                stopped = False
                for j, q in enumerate(planes):
                    if j == i or _dot(clip, q) >= 0.1:
                        continue
                    clip = _clip(clip, q)
                    if end_clip:
                        end_clip = _clip(end_clip, q)
                    if _dot(clip, p) >= 0:
                        continue
                    d = [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]]
                    dl = math.sqrt(_dot(d, d)) or 1.0
                    d = [x / dl for x in d]
                    s = _dot(d, self.velocity); clip = [x * s for x in d]
                    if end_clip:
                        s2 = _dot(d, end_velocity); end_clip = [x * s2 for x in d]
                    for k, r in enumerate(planes):
                        if k not in (i, j) and _dot(clip, r) < 0.1:
                            stopped = True
                            break
                    if stopped:
                        break
                if stopped:
                    self.velocity = [0.0, 0.0, 0.0]
                    return True
                self.velocity = clip
                if end_clip:
                    end_velocity = end_clip
                break
        if gravity:
            self.velocity = end_velocity
        return hit

    def _trace_to(self, start, end):
        """Trace and return (fraction, endpos, normal); endpos is the start when allsolid."""
        f, endpos, n, ss, als = self.collision.trace(start, end)
        if als:
            return 0.0, list(start), n
        return f, endpos, n

    def _step_slide(self, dt, gravity, on_ground):
        """C1 PM_StepSlideMove (engine-reference codol_pmove_c1_ground.c step_slide):
        step up 18 when blocked or on a slope steeper than normal z 0.9, snap down
        9 units while walking, keep the plain slide if stepping got no further,
        and slow the move on a real step."""
        start_o, start_v = list(self.origin), list(self.velocity)
        blocked = self._slide(dt, gravity)
        down_o, down_v = list(self.origin), list(self.velocity)
        if not on_ground:
            return                      # airborne: no stepping (no jump-step without jumping)
        step_up = 0.0
        if blocked or (self.ground_normal and self.ground_normal[2] < 0.9):
            f, up, _ = self._trace_to(start_o, [start_o[0], start_o[1], start_o[2] + C1_STEP_HEIGHT + 1.0])
            step_up = f * (C1_STEP_HEIGHT + 1.0) - 1.0
            if step_up < 1.0:
                step_up = 0.0
            else:
                self.origin = [start_o[0], start_o[1], start_o[2] + step_up]
                self.velocity = list(start_v)
                self._slide(dt, gravity)
        o = self.origin
        f, end, n = self._trace_to(o, [o[0], o[1], o[2] - (step_up + C1_GROUND_SNAP)])
        if f < 1.0 and n[2] < 0.3:
            self.origin, self.velocity = down_o, down_v
            return
        if f >= 1.0:
            if step_up:
                self.origin = [o[0], o[1], o[2] - step_up]
        else:
            self.origin = end
            self.velocity = _project(self.velocity, n)
        slide_dot = (down_o[0] - start_o[0]) * start_v[0] + (down_o[1] - start_o[1]) * start_v[1]
        step_dot = (self.origin[0] - start_o[0]) * start_v[0] + (self.origin[1] - start_o[1]) * start_v[1]
        if slide_dot + 0.001 >= step_dot:
            self.origin, self.velocity = down_o, down_v
            o = self.origin
            f, end, n = self._trace_to(o, [o[0], o[1], o[2] - C1_GROUND_SNAP])
            if f < 1.0:
                self.origin = end
                self.velocity = _clip(self.velocity, n)
        dz = self.origin[2] - down_o[2]
        if abs(dz) > 0.5 and round(dz) != 0:
            scale = (1.0 - abs(self.origin[2] - start_o[2]) / C1_STEP_HEIGHT) * 0.8 + 0.2
            self.velocity = [v * scale for v in self.velocity]

    # ---- mantle (C1 PM_CheckMantle 0x0040a740 / PM_MantleMove 0x0040a7a0) ----
    def _box(self, start, end, height):
        return self.collision.trace(start, end, (-15.0, -15.0, 0.0), (15.0, 15.0, height))

    def _mantle_ledge(self, d, h):
        o = self.origin
        start = [o[0], o[1], o[2] + h]
        end = [start[0] + d[0] * 16.0, start[1] + d[1] * 16.0, start[2]]
        f, _, _, ss, als = self._box(start, end, 30.0)
        if ss or als or f < 1.0:
            return None
        f, ledge, n, ss, als = self._box(end, [end[0], end[1], o[2] + 18.0], 30.0)
        if ss or als or f >= 1.0 or n[2] < MIN_WALK_NORMAL:
            return None
        f, _, _, ss, _ = self._box(ledge, ledge, 50.0)
        return None if ss else ledge

    def check_mantle(self, buttons, server_time):
        """Returns True when a mantle starts this command."""
        self.mantle_flags = getattr(self, 'mantle_flags', 0) & ~MANTLE_HINT
        if getattr(self, 'mantle', None):
            return False
        yaw = math.radians(self.yaw)
        fwd = (math.cos(yaw), math.sin(yaw))
        inner = 15.0 - 0.1
        o = self.origin
        start = [o[0] - fwd[0] * inner, o[1] - fwd[1] * inner, o[2]]
        end = [o[0] + fwd[0] * (inner + 20.0), o[1] + fwd[1] * (inner + 20.0), o[2]]
        f, n, ss, als = self.collision.mantle_trace(start, end)
        if ss or als or f >= 1.0:
            return False
        d = (-n[0], -n[1]); l = math.hypot(*d)
        if l <= 0.0001:
            return False
        d = (d[0] / l, d[1] / l)
        if math.degrees(math.acos(max(-1.0, min(1.0, fwd[0] * d[0] + fwd[1] * d[1])))) > 60.0:
            return False
        ledge = None
        for h in (60.0, 40.0, 20.0):
            ledge = self._mantle_ledge(d, h)
            if ledge:
                break
        if not ledge:
            return False
        self.mantle_flags |= MANTLE_HINT
        if not buttons & BUTTON_JUMP:
            return False
        rise = ledge[2] - o[2]
        trans = min(range(len(MANTLE_HEIGHTS)), key=lambda i: abs(MANTLE_HEIGHTS[i] - rise))
        flags = MANTLE_HINT
        if self._box(ledge, ledge, 70.0)[3]:
            flags |= MANTLE_LEDGE_SOLID
        if not self._box(ledge, ledge, 50.0)[3]:
            flags |= MANTLE_END_CLEAR
        self.mantle = dict(yaw=math.degrees(math.atan2(d[1], d[0])), timer=0, trans=trans, start=server_time,
                           still=0, last=list(o), rise=rise)
        self.mantle_flags = flags
        self.ground, self.ground_normal = ENTITYNUM_NONE, None
        self.velocity = [0.0, 0.0, 0.0]
        self.mantles = getattr(self, 'mantles', 0) + 1
        return True

    def client_mantle(self):
        """(yaw bits, timer, transition, flags) from the client's predicted ps while it mantles."""
        ps = self._predicted_ps() if hasattr(self, '_predicted_ps') else None
        if ps is None or not struct.unpack_from('<I', ps, 0xC)[0] & PMF_MANTLE:
            return None
        return struct.unpack_from('<IiiI', ps, 0x2AC)

    def _mantle_step(self, msec):
        m = self.mantle
        # The client's mantle ended (its pm_flags lost PMF_MANTLE after it had started): end ours.
        ps = self._predicted_ps() if hasattr(self, '_predicted_ps') else None
        if ps is not None and m['timer'] >= 100 and not struct.unpack_from('<I', ps, 0xC)[0] & PMF_MANTLE:
            m['timer'] = MANTLE_TOTAL_MS.get(m['trans'], 600)
        self.mantle_flags &= ~MANTLE_HINT        # C1 PM_MantleMove clears the hint each step
        total = MANTLE_TOTAL_MS.get(m['trans'], 600)
        m['timer'] = min(total, m['timer'] + msec)
        if m['timer'] >= total:
            self.mantle_log = getattr(self, 'mantle_log', []) + [(m['trans'], round(m['rise'], 1), m['timer'])]
            self.mantle = None
            self.mantle_flags &= ~MANTLE_HINT
            if self.velocity[2] > 0:
                self.velocity[2] = 0.0
            self._ground_trace()

    def ladder_at(self):
        o = self.origin
        for lad in LADDERS:
            mn, mx = lad['mins'], lad['maxs']
            if (mn[0] - LADDER_REACH <= o[0] <= mx[0] + LADDER_REACH and
                    mn[1] - LADDER_REACH <= o[1] <= mx[1] + LADDER_REACH and mn[2] - 8 <= o[2] <= mx[2] - 4):
                return lad
        return None

    def _ladder_move(self, dt, wx, wy, jump):
        """One command on a ladder; False when not on one (normal movement runs)."""
        yaw = math.radians(self.yaw)
        fwd = wx * math.cos(yaw) + wy * math.sin(yaw)
        lad = self.ladder_at()
        on = lad is not None and (getattr(self, 'on_ladder', False) or abs(fwd) > 0.1)
        if not on or jump:
            if getattr(self, 'on_ladder', False):
                self.ladder_log = getattr(self, 'ladder_log', 0) + 1
            self.on_ladder = False
            return False
        self.on_ladder = True
        self.ground, self.ground_normal = ENTITYNUM_NONE, None
        up = 1.0 if self.pitch < LADDER_DOWN_PITCH else -1.0
        vz = LADDER_SPEED * up * (1 if fwd > 0.1 else -1 if fwd < -0.1 else 0)
        side_x, side_y = wx - fwd * math.cos(yaw), wy - fwd * math.sin(yaw)
        self.velocity = [side_x * LADDER_SPEED * 0.5, side_y * LADDER_SPEED * 0.5, vz]
        self.origin = [self.origin[0] + self.velocity[0] * dt, self.origin[1] + self.velocity[1] * dt,
                       self.origin[2] + vz * dt]
        if vz < 0 and self._ground_trace():          # reached the floor: step off
            self.on_ladder = False
            self.velocity[2] = 0.0
        return True

    def movement_fields(self):
        """Player-state overrides for the encoder (F<index>=<value>)."""
        pm = 0
        if getattr(self, 'mantle', None):
            pm |= PMF_MANTLE
        if getattr(self, 'sprinting', False):
            pm |= PMF_SPRINTING
        if getattr(self, 'jumping', False):
            pm |= PMF_JUMPING
        if getattr(self, 'on_ladder', False):
            # The ladder pose is the client's own movement state: echo its predicted pm_flags (ps+0xC).
            ps = self._predicted_ps() if hasattr(self, '_predicted_ps') else None
            if ps is not None:
                pm = struct.unpack_from('<I', ps, 0xC)[0]
        # ADS (0x40) and ADS-button (0x10) are the client's own (set while aiming, run
        # 20261016T045423Z); clearing them every snapshot made the sights jitter.
        ps = self._predicted_ps() if hasattr(self, '_predicted_ps') else None
        if ps is not None:
            # Every pm_flags bit except mantle and jump is the client's own (ADS, sprint, ladder,
            # stance...): its weapon state machine lowers/raises the gun on ladders from them.
            client_pm = struct.unpack_from('<I', ps, 0xC)[0]
            # Handing over every other bit (ladder/stance/timer bits) caused rubber banding and an
            # ack stall (run 20261016T052004Z): timer bits go with pm_time, which the host does not
            # send. Only ADS and sprint are client-owned for now.
            pm = (pm & ~PMF_SPRINTING) | (client_pm & PMF_CLIENT_BITS)
        out = {20: pm, 99: getattr(self, 'mantle_flags', 0)}
        m = getattr(self, 'mantle', None)
        if m:
            out.update({115: struct.unpack('<I', struct.pack('<f', m['yaw']))[0], 108: m['timer'], 113: m['trans']})
            # Prefer the client's own mantle block (ps+2AC yaw, +2B0 timer, +2B4 transition,
            # +2B8 flags): its up-animation length differs per transition, and a host timer past
            # it (with no "over" flag) makes the client divide by a zero over-length and freeze
            # (0040DC30, run 20261016T024818Z froze 400 ms into a mantle).
            cm = self.client_mantle()
            if cm:
                out.update({115: cm[0], 108: cm[1], 113: cm[2], 99: cm[3]})
        if getattr(self, 'jumping', False):
            out.update({102: self.jump_time, 114: struct.unpack('<I', struct.pack('<f', self.jump_origin_z))[0]})
        return out

    def eflags_extra(self):
        return EF_MANTLE if getattr(self, 'mantle', None) else 0

    def move_collision(self, dt, wx, wy, length, wishspeed, jump=False, server_time=0, buttons=0):
        """C1 PM_WalkMove / PM_AirMove for one command (friction, accelerate, step-slide).
        jump: rising edge of BUTTON_JUMP; C1 PM_CheckJump (0x409630) launches a
        standing, walking player at sqrt(2 g 39) at most every 500 ms."""
        msec = int(round(dt * 1000.0))
        if getattr(self, 'mantle', None):
            self._mantle_step(msec)          # origin follows the client's reports (reconcile)
            return
        if self.check_mantle(buttons, server_time):
            return
        if self._ladder_move(dt, wx, wy, jump):
            return
        walking = self._ground_trace()
        if walking and getattr(self, 'jumping', False) and self.velocity[2] <= 0:
            self.jumping = False             # landed
        if walking and jump and server_time - getattr(self, 'jump_time', -10 ** 9) >= C1_JUMP_INTERVAL_MS:
            self.velocity[2] = math.sqrt(2.0 * GRAVITY * C1_JUMP_HEIGHT)
            self.jump_time = server_time
            self.jumping = True
            self.jump_origin_z = self.origin[2]
            self.jumps = getattr(self, 'jumps', 0) + 1
            self.ground, self.ground_normal = ENTITYNUM_NONE, None
            walking = False
        if walking:
            speed = math.hypot(self.velocity[0], self.velocity[1])
            if speed < 1.0:
                self.velocity = [0.0, 0.0, 0.0]
            else:
                drop = max(speed, C1_STOPSPEED) * C1_FRICTION * dt
                scale = max(0.0, speed - drop) / speed
                self.velocity = [v * scale for v in self.velocity]
        if length > 0 and wishspeed > 0:
            d = [wx / length, wy / length, 0.0]
            if walking:
                d = _project(d, self.ground_normal)
            rate = C1_GROUND_ACCEL if walking else C1_AIR_ACCEL
            add = wishspeed - _dot(self.velocity, d)
            if add > 0:
                step = min(add, rate * dt * max(wishspeed, 100.0))
                self.velocity = [self.velocity[i] + d[i] * step for i in range(3)]
        if walking:
            self.velocity = _project(self.velocity, self.ground_normal)
            if self.velocity[0] == 0.0 and self.velocity[1] == 0.0:
                return                  # 0x00410aee: no step-slide for a standing player
        self._step_slide(dt, not walking, walking)
        # The slope-aligned velocity is kept (C1 does not zero z on the ground;
        # zeroing it lost ~1/3 of the speed per frame on a 0.83 ramp).
        if self._ground_trace() and self.ground_normal and self.ground_normal[2] > 0.999 and self.velocity[2] < 0:
            self.velocity[2] = 0.0

    def reconcile(self, predicted, tolerance=PREDICTION_TOLERANCE):
        """Adopt the client's predicted origin for the command time just run.

        IW servers leave origin/velocity out of a snapshot while the client's
        reported prediction is within tolerance (1.1.1.13 msg.c
        MSG_WithinAllowedPredictionError); our encoder always sends them, so the
        host takes the client's value instead and the next snapshot confirms what
        the client already shows. Beyond the tolerance the host's own result
        stands and corrects the client. Returns the distance, or None if the
        report is for another command time."""
        xyz, t = predicted
        if t != self.command_time:
            return None
        d = math.sqrt(sum((a - b) ** 2 for a, b in zip(self.origin, xyz)))
        if getattr(self, 'on_ladder', False):
            self.origin = list(xyz)          # ladder climbing follows the client, like mantles
            self.reconciled = getattr(self, 'reconciled', 0) + 1
            return d
        m = getattr(self, 'mantle', None)
        if m:
            moved = math.dist(m['last'], xyz)
            m['still'] = m['still'] + 1 if moved < 0.01 else 0
            m['last'] = list(xyz)
            self.origin = list(xyz)          # mantle root motion is the client's
            self.reconciled = getattr(self, 'reconciled', 0) + 1
            return d
        if d <= tolerance:
            self.origin = list(xyz)
            self.reconciled = getattr(self, 'reconciled', 0) + 1
            # Also the client's velocity (ps+3C) when its latest predicted state is for about this
            # command time: the crosshair grows with speed, and the host's own slightly different
            # velocity made it jump every snapshot while moving.
            ps = self._predicted_ps() if hasattr(self, '_predicted_ps') else None
            if ps is not None and abs(struct.unpack_from('<i', ps, 0)[0] - t) <= 100:
                v = struct.unpack_from('<3f', ps, 0x3C)
                if all(math.isfinite(c) and abs(c) < 2000 for c in v):
                    self.velocity = list(v)
        else:
            self.corrected = getattr(self, 'corrected', 0) + 1
        return d

    def settle(self):
        """Drop to the floor below the spawn point at the start of the match."""
        o = self.origin
        f, end, n, ss, als = self.collision.trace([o[0], o[1], o[2] + 1], [o[0], o[1], o[2] - 128])
        if not als and f < 1.0 and n[2] >= MIN_WALK_NORMAL:
            self.origin = end
            self.ground, self.ground_normal = ENTITYNUM_WORLD, n
