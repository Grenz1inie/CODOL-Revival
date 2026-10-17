//! Initial unarmed player and render continuations. Current 3.19 fields only.
use std::sync::OnceLock;

fn fields() -> &'static Vec<[i32; 3]> {
    static FIELDS: OnceLock<Vec<[i32; 3]>> = OnceLock::new();
    FIELDS.get_or_init(|| {
        let value: serde_json::Value = serde_json::from_str(include_str!(
            "../../../match_host/snapshot_fields319.json")).unwrap();
        serde_json::from_value(value["player"].clone()).unwrap()
    })
}

#[derive(Default)]
struct Message { bytes: Vec<u8>, bit: usize }

impl Message {
    fn raw(&mut self, value: u32, count: usize) { self.bytes.extend(&value.to_le_bytes()[..count]); }
    fn bits(&mut self, value: u32, count: usize) {
        for shift in 0..count {
            if self.bit % 8 == 0 {
                self.bit = self.bytes.len() * 8;
                self.bytes.push(0);
            }
            self.bytes[self.bit / 8] |= (((value >> shift) & 1) as u8) << (self.bit % 8);
            self.bit += 1;
        }
    }
    fn gap(&mut self, distance: usize) {
        self.bits(u32::from(distance == 1), 1);
        if distance == 1 { return; }
        let mut left = distance - 1;
        while left >= 15 { self.bits(15, 4); left -= 15; }
        self.bits(left as u32, 4);
    }
    fn value(&mut self, codec: i32, value: u32, stamp: u32) {
        match codec {
            -97 | -70 => {
                let short = stamp.checked_sub(value).filter(|&d| d < 256);
                self.bits(u32::from(short.is_none()), 1);
                if let Some(delta) = short { self.bits(delta, 8); } else { self.raw(value, 4); }
            }
            -88 => self.raw(value, 4),
            -87 => self.raw((f32::from_bits(value) * 182.04445).round_ties_even() as i32 as u32 & 65535, 2),
            0 => {
                if value & 0x7fff_ffff == 0 { self.bits(0, 1); self.bits(value >> 31, 1); }
                else { self.bits(3, 2); self.raw(value, 4); }
            }
            -57 => self.bits(value, 1),
            -101 if value == 0 => self.bits(0, 1),
            width if (1..=32).contains(&width.abs()) => {
                self.bits(u32::from(value != 0), 1);
                if value != 0 {
                    let width = width.unsigned_abs() as usize;
                    self.bits(value, width % 8);
                    for shift in (width % 8..width).step_by(8) { self.raw((value >> shift) & 255, 1); }
                }
            }
            _ => unreachable!("unsupported field in fixed initial player: {codec}/{value}"),
        }
    }
}

pub struct Snapshot { values: Vec<u32> }

impl Snapshot {
    pub fn new(origin: [f32; 3], yaw: f32) -> Result<Self, &'static str> {
        if origin.iter().chain([yaw].iter()).any(|v| !v.is_finite() || v.abs() > 131072.0) {
            return Err("invalid map spawn");
        }
        let mut values = vec![0; fields().len()];
        let definition: serde_json::Value = serde_json::from_str(include_str!(
            "../../../match_host/snapshot_fields319.json")).unwrap();
        for row in definition["living"].as_array().unwrap() {
            values[row[0].as_u64().unwrap() as usize] = row[2].as_u64().unwrap() as u32;
        }
        for (index, value) in [(8, origin[0]), (11, origin[1]), (10, origin[2]), (18, yaw)] {
            values[index] = value.to_bits();
        }
        Ok(Self { values })
    }

    pub fn encode(&self, stamp: u32, command_time: u32, delta: u8) -> Result<Vec<u8>, &'static str> {
        if !(1..=0x7fff_ffff).contains(&stamp) || command_time > 0x7fff_ffff || delta > 15 {
            return Err("invalid snapshot time or delta");
        }
        let mut values = self.values.clone();
        values[0] = command_time;
        let fields = fields();
        let selected: Vec<_> = (0..values.len()).filter(|&i| values[i] != 0 || fields[i][2] == 3).collect();
        let last = selected.last().unwrap() + 1;
        let mut message = Message::default();
        message.raw(0, 1); message.raw(stamp, 4);
        message.raw(delta as u32, 1); message.raw(if delta == 0 { 8 } else { 0 }, 1);
        message.bits(0, 1); // player state is encoded against the zero baseline
        message.bits(1, 1); message.bits(last as u32, 8);
        let mut previous = -1;
        for index in selected {
            if fields[index][2] == 2 && index < last - 1 { continue; }
            message.gap((index as i32 - previous) as usize);
            message.value(fields[index][1], values[index], stamp);
            previous = index as i32;
        }
        for index in 0..last - 1 {
            if fields[index][2] == 2 { message.value(fields[index][1], values[index], stamp); }
        }
        message.bits(1, 1); message.bits(5, 17); // health and maximum health
        message.raw(100, 2); message.raw(100, 2);
        message.bits(0, 3); message.bits(0, 15); // no weapon/ammo changes
        message.bits(0, 1); message.bits(1, 1); message.bits(2047, 11); // entity terminator
        message.bits(0, 2); message.raw(5, 1); // no client/glass changes, EOF
        Ok(message.bytes)
    }
}
