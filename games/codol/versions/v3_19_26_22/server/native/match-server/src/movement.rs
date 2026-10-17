//! First-phase player movement over decoded 3.19 usercmds. The integrator is
//! the version's Python reference (match_host/live_sim319 no-collision branch:
//! Q3 friction 6.0 / accelerate 10.0 / stop speed 100 / 200 ms step cap / z
//! held at the spawn height), with C1 wish scaling (match_host/collision_move319:
//! back 0.7, strafe 0.8, sprint 1.5) and predicted-origin reconciliation within
//! 16 units. Collision, jumping and mantling stay later phases.
use crate::transport::UserCmd;

const FORWARD: u8 = 1;
const BACK: u8 = 2;
const RIGHT: u8 = 4;
const LEFT: u8 = 8;
const SPEED: f32 = 190.0;          // ps speed, profile idx 60, sent in the first frame
const FRICTION: f32 = 6.0;
const ACCELERATE: f32 = 10.0;
const STOP_SPEED: f32 = 100.0;
const MAX_STEP: f32 = 0.2;         // seconds integrated from one command
const BACK_SCALE: f32 = 0.7;
const STRAFE_SCALE: f32 = 0.8;
const SPRINT_SCALE: f32 = 1.5;
const BUTTON_SPRINT: u32 = 0x2;
const PITCH_LIMIT: f32 = 85.0;
const PREDICTION_TOLERANCE: f32 = 16.0;
const DEG_PER_SHORT: f32 = 360.0 / 65536.0;

fn wish_speed(forward: f32, right: f32) -> f32 {
    if forward == 0.0 && right == 0.0 { return 0.0; }
    let f = 127.0 * forward * if forward < 0.0 { BACK_SCALE } else { 1.0 };
    let r = 127.0 * right * STRAFE_SCALE;
    SPEED * f.abs().max(r.abs()) / 127.0
}

fn short_delta_degrees(new: u16, old: u16) -> f32 {
    new.wrapping_sub(old) as i16 as f32 * DEG_PER_SHORT
}

pub struct Movement {
    pub origin: [f32; 3],
    pub velocity: [f32; 3],
    pub pitch: f32,
    pub yaw: f32,
    pub command_time: u32,
    pub applied: u32,
    pub reconciled: u32,
    pub corrected: u32,
    spawn_z: f32,
    last_pitch: Option<u16>,
    last_yaw: Option<u16>,
}

impl Movement {
    pub fn new(origin: [f32; 3], yaw: f32) -> Result<Self, &'static str> {
        let bad = |v: f32| !v.is_finite() || v.abs() > 131072.0;
        if origin.iter().any(|v| bad(*v)) || bad(yaw) { return Err("invalid movement spawn"); }
        Ok(Self {
            origin,
            spawn_z: origin[2],
            velocity: [0.0; 3],
            pitch: 0.0,
            yaw,
            command_time: 0,
            applied: 0,
            reconciled: 0,
            corrected: 0,
            last_pitch: None,
            last_yaw: None,
        })
    }

    /// Run one command if it is newer than the last executed one. Usercmd
    /// angles arrive relative to the client's spawn orientation (the first
    /// commands read 0 while the spawn yaw is 330), so per-command short
    /// deltas accumulate onto the snapshot spawn orientation.
    pub fn apply(&mut self, cmd: &UserCmd) -> bool {
        if cmd.server_time <= self.command_time { return false; }
        let dt = if self.command_time == 0 { 0.0 }
            else { ((cmd.server_time - self.command_time) as f32 / 1000.0).min(MAX_STEP) };
        self.command_time = cmd.server_time;
        self.applied += 1;
        if let Some(old) = self.last_pitch {
            self.pitch = (self.pitch + short_delta_degrees(cmd.angles[0], old)).clamp(-PITCH_LIMIT, PITCH_LIMIT);
        }
        if let Some(old) = self.last_yaw {
            self.yaw += short_delta_degrees(cmd.angles[1], old);
        }
        self.last_pitch = Some(cmd.angles[0]);
        self.last_yaw = Some(cmd.angles[1]);
        if dt <= 0.0 { return true; }

        let class = cmd.move_class;
        let forward = ((class & FORWARD != 0) as i32 - (class & BACK != 0) as i32) as f32;
        let right = ((class & RIGHT != 0) as i32 - (class & LEFT != 0) as i32) as f32;
        let yaw = self.yaw.to_radians();
        let (sin, cos) = (yaw.sin(), yaw.cos());
        let (wx, wy) = (cos * forward + sin * right, sin * forward - cos * right);
        let length = wx.hypot(wy);

        let speed = self.velocity[0].hypot(self.velocity[1]);
        if speed > 0.0 {
            let drop = speed.max(STOP_SPEED) * FRICTION * dt;
            let scale = (speed - drop).max(0.0) / speed;
            self.velocity[0] *= scale;
            self.velocity[1] *= scale;
        }
        let mut wish = wish_speed(forward, right);
        if cmd.buttons & BUTTON_SPRINT != 0 && forward > 0.0 { wish *= SPRINT_SCALE; }
        if length > 0.0 && wish > 0.0 {
            let (dx, dy) = (wx / length, wy / length);
            let current = self.velocity[0] * dx + self.velocity[1] * dy;
            let add = wish - current;
            if add > 0.0 {
                let accel = add.min(ACCELERATE * dt * wish.max(STOP_SPEED));
                self.velocity[0] += accel * dx;
                self.velocity[1] += accel * dy;
            }
        }
        self.origin[0] += self.velocity[0] * dt;
        self.origin[1] += self.velocity[1] * dt;
        self.origin[2] = self.spawn_z;
        self.velocity[2] = 0.0;
        true
    }

    /// Adopt the client's predicted origin for the command time just run when
    /// it is within 16 units; beyond that the host result stands and corrects
    /// the client. Returns the distance, or None if the report is stale.
    pub fn reconcile(&mut self, origin: [f32; 3], time: u32) -> Option<f32> {
        if time != self.command_time { return None; }
        let dx = origin[0] - self.origin[0];
        let dy = origin[1] - self.origin[1];
        let dz = origin[2] - self.origin[2];
        let distance = (dx * dx + dy * dy + dz * dz).sqrt();
        if distance <= PREDICTION_TOLERANCE {
            self.origin = origin;
            self.reconciled += 1;
        } else {
            self.corrected += 1;
        }
        Some(distance)
    }
}
