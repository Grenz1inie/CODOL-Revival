"""Authoritative single-player movement for the diagnostic host (version 1).

Consumes decoded 3.19 usercmds (client_message319.read_usercmd) in serverTime
order and produces the player state the source encoder (snapshot_codec319)
writes each tick. Version 1 limits, by design:
  * horizontal Q3-style ground movement only (accelerate/friction at speed 190);
  * without a collision map z is held at the spawn height; with one
    (collision_move319) ground trace, gravity and step-slide, no jumping yet;
  * view angles come straight from the command (delta_angles stay 0).
Static models (cars, crates) are not in the collision capture yet, so the
client and host can still disagree around them.
"""
import math
import struct
import time
import os
from pathlib import Path

from client_message319 import FORWARD, BACK, RIGHT, LEFT, short_to_degrees
from snapshot_codec319 import encode
from collision_move319 import CollisionMovement, ENTITYNUM_NONE, wish_speed, BUTTON_JUMP, BUTTON_SPRINT, SPRINT_SCALE

ROOT = Path(os.environ['CODOL319_SERVER_ROOT']) / 'match-host'
PREDICTED_PS = ROOT / 'predicted-ps319.bin'
PREDICTED_RING = ROOT / 'predicted-ps-ring319.bin'
USE_PS_RING = False   # off: run 20261016T052004Z stalled with it (proxy 2 ms polling + ring); revisit
BUTTON_RELOAD = 0x10          # usercmd reload (seen in run 20261016T023306Z when R was pressed)
RELOAD_SECONDS = 2.2
# Server-side reload is off: with the weapon phase mirrored (MIRROR_STATE) the client completes its
# own reload, and both together moved the reserve twice (run 20261016T034846Z: 3|24 -> 11|0).
SERVER_RELOAD = False
# Client-predicted playerState words echoed back in every snapshot (netfield index: ps offset), so
# the snapshot no longer resets the client's own sprint and weapon-phase state each frame (which
# cut the sprint/reload animations short). Sprint block +284..+29C (seen to follow the sprint
# button in run 20261015T213425Z + ps-record319.bin: +284/+288 = 1 while sprinting, +290 start
# time); weapon phase block +2BC..+2E0 (anim/time/delay/state). The mantle block (+2A8..+2B8) stays
# owned by the host simulation.
MIRROR_FIELDS = {101: 0x284, 93: 0x288, 35: 0x28C, 36: 0x290, 43: 0x294, 30: 0x298, 172: 0x29C,
                 9: 0x2BC, 3: 0x2C0, 44: 0x2C4, 189: 0x2C8, 17: 0x2CC, 121: 0x2D0, 87: 0x2D4,
                 51: 0x2D8, 162: 0x2DC, 107: 0x2E0}
MIRROR_STATE = True
# Aim: ADS fraction (field 220, ps+40C, float) and the aim-spread fields 193 (+410, 6 bits), 194
# (+414, 2 bits), 106 (+418, 1 bit) from the 2.6.9.7 reference mapping; the server's zeros made the
# crosshair and ADS jitter while moving (2026-10-16 video). Narrow fields are echoed only when the
# client's value fits them.
MIRROR_AIM = {41: (0x404, 32), 151: (0x578, 14), 152: (0x57C, 2)}
# (measured in ps-record319-fire.bin: +404 = ADS fraction while the ADS button 0x800 is held,
#  +578 = crosshair spread 28..80; the reference-mapped +40C/+410 stayed 0, so they are not aim.)
# Player events: the client predicts its own (54 EV_SV_FIRE_WEAPON, 25-30 reload, ... in run
# 20261016T045423Z) with eventSequence +108 (field 1) and slots {event, parm} at +10C..+12B
# (fields 21-24); second queue +12C (field 2), slots +138..+157 (46, 48, 49, 50). The server's
# zeros reset the sequence every snapshot, so shot effects (impacts) were dropped; echo them.
MIRROR_EVENTS = {1: 0x108, 2: 0x12C}
MIRROR_EVENT_SLOTS = {21: 0x10C, 22: 0x114, 23: 0x11C, 24: 0x124, 46: 0x138, 48: 0x140, 49: 0x148, 50: 0x150}          # M4-class reload time; refill lands at the end of the animation
WEAPON_MOVE_SCALE = {78: 0.795}   # ak47_mp (measured, see LiveSim.__init__)
SPEED = 190.0          # ps speed (profile idx 60) sent to the client
ACCELERATE = 10.0      # Q3 pm_accelerate
FRICTION = 6.0         # Q3 pm_friction
STOP_SPEED = 100.0     # Q3 pm_stopspeed
MAX_STEP = 0.2         # never integrate more than 200 ms from one command


WEAPFLAGS_HOLD_MS = 5000
WEAPON_SELECT_DELAY = True
OTHER_FLAGS = 0x1000
try:
    ARMS56 = int((ROOT / 'viewmodel-arms56.txt').read_text().split()[0])
except (OSError, ValueError, IndexError):
    ARMS56 = 0


class LiveSim(CollisionMovement):
    def __init__(self, origin, yaw=0.0, weapon=0, viewmodels=(0, 0), weapflags=0, collision=None):
        self.origin = [float(v) for v in origin]
        self.velocity = [0.0, 0.0, 0.0]
        self.pitch = 0.0
        self.yaw = float(yaw)
        self.command_time = 0
        self.commands = 0
        self.weapon = int(weapon)
        # First-person arms/hands CS_MODELS indices (encoder fields 57 / 118); need a weapon.
        self.viewmodels = tuple(int(v) for v in viewmodels)
        # Field 77 (+400); bit 0x80 skips the HUD weapon-name draw (00458190).
        self.weapflags = int(weapflags)
        # Bit 0x80 is also IW's "weapons disabled", which hides the viewmodel; it only has
        # to cover the first frames before weapon info loads (packet ~25), so it is cleared
        # (field 77 override) WEAPFLAGS_HOLD_MS after the first live frame.
        self.first_server_time = None
        if self.weapflags and not any(self.viewmodels):
            raise ValueError('weapflags requires viewmodels')
        if any(self.viewmodels) and not self.weapon:
            raise ValueError('viewmodels require a weapon')
        self.eflags = 0
        # Optional collision_move319.Collision: ground trace, gravity and step-slide
        # against the captured clipMap; groundEntityNum is then sent each frame.
        self.collision = collision
        # Weapon moveSpeedScale (PM_CmdScale). The 3.19 AK-47 value is not read yet;
        # 0.795 is the client's measured steady forward speed (151) / 190 in run 073038Z.
        self.weapon_scale = WEAPON_MOVE_SCALE.get(self.weapon, 1.0)
        self.ground = ENTITYNUM_NONE if collision else None
        self.ground_normal = None
        self.prev_buttons = 0
        # Server-side reload (button 0x10): the client's predicted reload never completes because
        # each snapshot resets its weapon state, so the magazine refill is done here and held
        # until the client's predicted clip shows it (see ammo_from_client).
        self.clip = self.ammo = None
        self.max_clip = 0
        self.reload_done_at = None
        self.ammo_override = None          # (clip, ammo, expires)
        self.prev_reload = False
        if collision:
            self.settle()

    # ---- simulation -------------------------------------------------
    def apply(self, cmd):
        """Run one usercmd if it is newer than the last executed one."""
        t = cmd['server_time']
        if t <= self.command_time:
            return False
        dt = 0.0 if not self.command_time else min(MAX_STEP, (t - self.command_time) / 1000.0)
        self.command_time = t
        self.commands += 1
        self.pitch = max(-85.0, min(85.0, short_to_degrees(cmd['angles'][0])))
        self.yaw = short_to_degrees(cmd['angles'][1])
        self.check_reload(cmd.get('buttons', 0))
        cls = cmd['move_class']
        fwd = (1 if cls & FORWARD else 0) - (1 if cls & BACK else 0)
        right = (1 if cls & RIGHT else 0) - (1 if cls & LEFT else 0)
        yaw = math.radians(self.yaw)
        fx, fy = math.cos(yaw), math.sin(yaw)
        rx, ry = math.sin(yaw), -math.cos(yaw)          # Q3 AngleVectors right
        wx, wy = fx * fwd + rx * right, fy * fwd + ry * right
        length = math.hypot(wx, wy)
        if dt <= 0:
            return True
        if self.collision:
            buttons = cmd.get('buttons', 0)
            jump = bool(buttons & BUTTON_JUMP) and not (self.prev_buttons & BUTTON_JUMP)
            self.prev_buttons = buttons
            wish = wish_speed(SPEED, fwd, right, self.weapon_scale)
            ps = self._predicted_ps()
            if ps is not None:
                # The client decides sprint (meter, cooldown, animation); follow its PMF_SPRINTING.
                self.sprinting = bool(struct.unpack_from('<I', ps, 0xC)[0] & 0x4000) and fwd > 0
            else:
                self.sprinting = bool(buttons & BUTTON_SPRINT) and fwd > 0
            if self.sprinting:
                wish *= SPRINT_SCALE           # sprint (button 0x2, forward held)
            self.move_collision(dt, wx, wy, length, wish, jump, t, buttons)
            return True
        # Friction (PM_Friction, ground).
        speed = math.hypot(self.velocity[0], self.velocity[1])
        if speed > 0:
            drop = max(speed, STOP_SPEED) * FRICTION * dt
            scale = max(0.0, speed - drop) / speed
            self.velocity[0] *= scale; self.velocity[1] *= scale
        # Acceleration (PM_Accelerate) towards the wish direction.
        if length > 0:
            wx, wy = wx / length, wy / length
            current = self.velocity[0] * wx + self.velocity[1] * wy
            add = SPEED - current
            if add > 0:
                accel = min(add, ACCELERATE * dt * SPEED)
                self.velocity[0] += accel * wx; self.velocity[1] += accel * wy
        self.origin[0] += self.velocity[0] * dt
        self.origin[1] += self.velocity[1] * dt
        return True

    # ---- encoding ---------------------------------------------------
    def weapflags_override(self, server_time):
        if self.first_server_time is None:
            self.first_server_time = server_time
        out = ()
        if self.weapflags & 0x80 and server_time - self.first_server_time >= WEAPFLAGS_HOLD_MS:
            out += ('F77=%d' % (self.weapflags & ~0x80),)
        # Field 56 (ps+15C): CS_MODELS index of the first-person arms, read by the viewmodel
        # builder (0059049x). Set per experiment in viewmodel-arms56.txt (0 or missing = off).
        if ARMS56 and server_time - self.first_server_time >= WEAPFLAGS_HOLD_MS:
            out += ('F56=%d' % ARMS56,)
        # Held weapon (field 39) stays 0 until then: the client only copies a *changed* ps weapon
        # into its weapon select (cg+C7228 -> usercmd weapon); with the weapon present from the
        # first frame the select stayed 0 and the client never became ready to fire.
        if WEAPON_SELECT_DELAY and server_time - self.first_server_time < WEAPFLAGS_HOLD_MS:
            out += ('F39=0',)
        # otherFlags (field 54, protected ps+0x10): 0x1000 lets the client adopt the ps weapon
        # as its weapon select (005952E9), which the usercmd then carries.
        if OTHER_FLAGS and server_time - self.first_server_time >= WEAPFLAGS_HOLD_MS:
            out += ('F54=%d' % OTHER_FLAGS,)
        out += self.ammo_from_client()
        if getattr(self, 'ammo_weapon', 0):
            out += ('F902=%d' % self.ammo_weapon,)     # composite: reserve also under its base weapon
        out += self.mirror_client_state()
        return out

    def mirror_client_state(self):
        if not MIRROR_STATE or getattr(self, 'mantle', None):
            return ()
        ps = self._predicted_ps()
        if ps is None:
            return ()
        out = ['F%d=%d' % (idx, struct.unpack_from('<I', ps, off)[0])
               for idx, off in sorted(MIRROR_FIELDS.items())]
        for idx, off in sorted(MIRROR_EVENTS.items()):
            out.append('F%d=%d' % (idx, struct.unpack_from('<I', ps, off)[0] & 0x7FF))
        for idx, off in sorted(MIRROR_EVENT_SLOTS.items()):
            ev, parm = struct.unpack_from('<II', ps, off)
            out.append('F%d=%d:%d' % (idx, ev, parm))
        for idx, (off, bits) in sorted(MIRROR_AIM.items()):
            v = struct.unpack_from('<I', ps, off)[0]
            if bits >= 32 or v < (1 << bits):
                out.append('F%d=%d' % (idx, v))
        return tuple(out)

    def _predicted_ps(self):
        """The client's predicted playerState (0x600 bytes) for exactly this simulation's command time
        when the proxy's history ring has it (predicted-ps-ring319.bin), otherwise its latest state;
        None if missing/stale/torn. The client rebuilds its prediction from the snapshot's command
        time, so echoing a state from another moment made the crosshair jump while moving."""
        if USE_PS_RING:
            ring = self._ring_ps(self.command_time)
            if ring is not None:
                return ring
        return self._latest_ps()

    def _ring_ps(self, command_time):
        if not command_time:
            return None
        try:
            if time.time() - PREDICTED_RING.stat().st_mtime > 1.0:
                return None
            key = (command_time, PREDICTED_RING.stat().st_mtime_ns)
            if getattr(self, '_ring_cache', (None,))[0] == key:
                return self._ring_cache[1]
            b = PREDICTED_RING.read_bytes()
            found = None
            if b[:4] == b'PSR1':
                slots = struct.unpack_from('<I', b, 4)[0]
                step = 8 + 0x600
                for k in range(min(slots, 64)):
                    o = 16 + k * step
                    if o + step > len(b):
                        break
                    a, z = struct.unpack_from('<I', b, o)[0], struct.unpack_from('<I', b, o + 4 + 0x600)[0]
                    if a == z == command_time:
                        found = b[o + 4:o + 4 + 0x600]
                        break
            self._ring_cache = (key, found)
            self.ring_hits = getattr(self, 'ring_hits', 0) + (found is not None)
            self.ring_misses = getattr(self, 'ring_misses', 0) + (found is None)
            return found
        except OSError:
            return None

    def _latest_ps(self):
        """The client's latest predicted playerState (0x600 bytes) or None if missing/stale/torn.
        Read once per file version: several features ask for it every frame."""
        try:
            st = PREDICTED_PS.stat()
            if time.time() - st.st_mtime > 1.0:
                return None
            if getattr(self, '_latest_cache', (None,))[0] == st.st_mtime_ns:
                return self._latest_cache[1]
        except OSError:
            return None
        ps = self._read_latest_ps()
        self._latest_cache = (st.st_mtime_ns, ps)
        return ps

    def _read_latest_ps(self):
        try:
            b = PREDICTED_PS.read_bytes()
            if len(b) != 12 + 0x600 + 4 or b[:4] != b'PS19' or b[4:8] != b[-4:]:
                return None
            if time.time() - PREDICTED_PS.stat().st_mtime > 1.0:
                return None
            return b[12:]
        except OSError:
            return None

    def set_weapon(self, weapon):
        """Switch field 39; the client adopts the weapon with otherFlags 0x1000."""
        self.weapon = int(weapon)
        self.weapon_scale = WEAPON_MOVE_SCALE.get(self.weapon, 1.0)
        self.clip = self.ammo = None
        self.max_clip = 0
        self.ammo_override = None
        self.reload_done_at = None

    def check_reload(self, buttons):
        pressed = bool(buttons & BUTTON_RELOAD)
        if (SERVER_RELOAD and pressed and not self.prev_reload and self.reload_done_at is None and self.clip is not None
                and self.clip < self.max_clip and self.ammo):
            self.reload_done_at = time.time() + RELOAD_SECONDS
        self.prev_reload = pressed

    def ammo_from_client(self):
        now = time.time()
        if self.reload_done_at is not None and now >= self.reload_done_at:
            self.reload_done_at = None
            moved = min(self.max_clip - self.clip, self.ammo)
            self.clip, self.ammo = self.clip + moved, self.ammo - moved
            self.ammo_override = (self.clip, self.ammo, now + 1.5)
        mirrored = self._mirror_client_ammo()
        if self.ammo_override:
            clip, ammo, expires = self.ammo_override
            if (mirrored and mirrored[0] == clip) or now > expires:
                self.ammo_override = None          # the client has adopted the refill
            else:
                return ('F900=%d' % clip, 'F901=%d' % ammo)
        if not mirrored:
            return ()
        self.clip, self.ammo = mirrored
        self.max_clip = max(self.max_clip, self.clip)
        return ('F900=%d' % self.clip, 'F901=%d' % self.ammo)

    def _mirror_client_ammo(self):
        """Mirror the client's own predicted clip/reserve (predicted-ps319.bin, written by the
        proxy every 20 ms: clip pair ps+494 {weapon, clip}, reserve ps+41C {weapon, count}) so
        the snapshot does not refill the magazine after every shot. Pseudo fields 900/901."""
        try:
            ps = self._latest_ps()
            if ps is None:
                return None
            w, clip = struct.unpack_from('<ii', ps, 0x494)
            # Reserve: entries {weapon, count} at +41C (8 bytes each). A composite's reserve is
            # spent from its base weapon's entry (the one the HUD shows, F902), so read that one;
            # reading the composite's own entry kept the reserve full ("unlimited ammo").
            want = getattr(self, 'ammo_weapon', 0) or self.weapon
            ammo = None
            for k in range(15):
                rw, count = struct.unpack_from('<ii', ps, 0x41C + 8 * k)
                if rw == want:
                    ammo = count
                    break
            if w != self.weapon or ammo is None or not 0 <= clip < 512 or not 0 <= ammo < 4096:
                return None
            return clip, ammo
        except (OSError, struct.error):
            return None

    def bot_tokens(self):
        """Static test bots from bots319.txt -> encoder E<n>=... / C<n>=... tokens."""
        out = []
        try:
            lines = (ROOT / 'bots319.txt').read_text(encoding='utf-8').splitlines()
        except OSError:
            return ()
        for line in lines:
            if line.startswith('BM='):                       # entity field mask (encoder bisect)
                out.append(line.split()[0]); continue
            f = line.split('#', 1)[0].split()
            if len(f) < 8:
                continue
            n, x, y, z, yaw, w, team, model = f[:8]
            legs, torso = (f[8], f[9]) if len(f) >= 10 else ('0', '0')
            etype = f[10] if len(f) >= 11 else '1'          # entity type (1 = player)
            if etype != '-':                                  # TYPE '-' = client record only
                out.append('E%s=%s,%s,%s,%s,%s,%s,%s,%s' % (n, x, y, z, yaw, w, legs, torso, etype))
            if model != '0':                                  # MODEL 0 = no client record
                # MODEL may be "body+att1+att2+..." (CS_MODELS indices of the character parts)
                out.append('C%s=%s,%s' % (n, team, ','.join(model.split('+'))))
        return tuple(out)

    def payload(self, server_time):
        """Full flag-8 snapshot for this tick (the host turns it into a delta)."""
        command_time = self.command_time or server_time
        request = ' '.join(str(v) for v in (server_time, command_time, *[round(x, 3) for x in self.origin],
                                             *[round(x, 3) for x in self.velocity],
                                             round(self.pitch, 4), round(self.yaw, 4),
                                             int(self.eflags) | (self.eflags_extra() if self.collision else 0))
                           + ((int(self.ground),) if self.ground is not None else ())
                           + (tuple('F%d=%d' % kv for kv in sorted(self.movement_fields().items())) if self.collision else ())
                           + self.weapflags_override(server_time)
                           + self.bot_tokens())
        return encode(request, self.weapon, self.viewmodels, self.weapflags)

    def close(self):
        # The Collision process is owned by the host (shared across peers).
        pass
