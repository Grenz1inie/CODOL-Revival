//! Inverse of the current 0x5a1be0 usercmd writer; port of match_server/input.py.
//! SPDX-License-Identifier: AGPL-3.0-or-later

use super::{Fields, Result, UserCmd};

pub const FIELDS: [&str; 17] = ["time", "buttons", "pitch", "yaw", "roll", "direction",
    "weapon", "offhand", "alt", "melee_yaw", "melee_dist", "melee_target",
    "location_x", "location_y", "location_angle", "remote_x", "remote_y"];

pub struct Reader<'a> {
    data: &'a [u8],
    pub cursor: usize,
    bit: usize,
}

impl<'a> Reader<'a> {
    pub fn new(data: &'a [u8]) -> Self { Self { data, cursor: 0, bit: 0 } }

    pub fn raw(&mut self, size: usize) -> Result<&'a [u8]> {
        if size > self.data.len() - self.cursor { return Err("truncated client message".into()); }
        let value = &self.data[self.cursor..self.cursor + size];
        self.cursor += size;
        Ok(value)
    }

    pub fn number(&mut self, size: usize) -> Result<u32> {
        if size > 4 { return Err("invalid integer width".into()); }
        let mut word = [0; 4];
        word[..size].copy_from_slice(self.raw(size)?);
        Ok(u32::from_le_bytes(word))
    }

    pub fn bits(&mut self, width: usize) -> Result<u32> {
        if width > 32 { return Err("invalid bit width".into()); }
        let mut value = 0;
        for i in 0..width {
            if self.bit % 8 == 0 {
                self.bit = self.cursor * 8;
                self.raw(1)?;
            }
            value |= u32::from((self.data[self.bit / 8] >> (self.bit % 8)) & 1) << i;
            self.bit += 1;
        }
        Ok(value)
    }

    pub fn string(&mut self) -> Result<&'a [u8]> {
        let length = self.data[self.cursor..].iter().position(|&b| b == 0)
            .filter(|&n| n <= 1023).ok_or("invalid client command string")?;
        Ok(&self.raw(length + 1)?[..length])
    }
}

fn delta(reader: &mut Reader<'_>, state: &mut UserCmd, name: &str,
         key: u32, width: usize, raw: bool) -> Result<()> {
    if reader.bits(1)? != 0 {
        let value = if raw { reader.number(width / 8)? } else { reader.bits(width)? };
        state.insert(name.into(), value ^ (key & ((1u32 << width) - 1)));
    }
    Ok(())
}

pub fn read_usercmd(reader: &mut Reader<'_>, key: u32, base: &UserCmd) -> Result<UserCmd> {
    let mut state: UserCmd = FIELDS.iter().map(|&n| (n.to_string(), *base.get(n).unwrap_or(&0))).collect();
    let time = if reader.bits(1)? != 0 { state["time"].wrapping_add(reader.number(1)?) }
        else { reader.number(4)? };
    state.insert("time".into(), time);
    let mut expected = 7;
    if reader.bits(1)? ^ (key & 1) != 0 {
        if reader.bits(1)? ^ (key & 1) == 0 {
            expected = 2;
            let k = key ^ time;
            let buttons = (state["buttons"] & !1) | (reader.bits(1)? ^ (k & 1));
            state.insert("buttons".into(), buttons);
            delta(reader, &mut state, "pitch", k, 16, true)?;
            delta(reader, &mut state, "yaw", k, 16, true)?;
            delta(reader, &mut state, "direction", k, 4, false)?;
        } else {
            expected = 5;
            let fire = reader.bits(1)? ^ (key & 1);
            delta(reader, &mut state, "pitch", key, 16, true)?;
            delta(reader, &mut state, "yaw", key, 16, true)?;
            delta(reader, &mut state, "direction", key, 4, false)?;
            let k = key ^ time;
            delta(reader, &mut state, "roll", k, 16, true)?;
            let upper = if reader.bits(1)? != 0 { reader.bits(29)? ^ (k & ((1 << 29) - 1)) }
                else { state["buttons"] >> 1 };
            let buttons = upper * 2 | fire;
            state.insert("buttons".into(), buttons);
            for name in ["weapon", "offhand", "alt"] { delta(reader, &mut state, name, k, 10, false)?; }
            if buttons & 0x20000 != 0 {
                for name in ["location_x", "location_y", "location_angle"] { delta(reader, &mut state, name, k, 8, true)?; }
            }
            if buttons & 0x200000 != 0 {
                for name in ["remote_x", "remote_y"] { delta(reader, &mut state, name, k, 8, true)?; }
            }
            if buttons & 4 != 0 {
                delta(reader, &mut state, "melee_yaw", k, 16, true)?;
                delta(reader, &mut state, "melee_dist", k, 8, false)?;
                delta(reader, &mut state, "melee_target", k, 11, false)?;
            }
        }
    }
    if reader.bits(3)? != expected { return Err("invalid usercmd trailing tag".into()); }
    Ok(state)
}

pub fn decode_usercmd(wire: &[u8], key: u32, base: Option<&UserCmd>) -> Result<UserCmd> {
    let mut reader = Reader::new(wire);
    let command = read_usercmd(&mut reader, key, base.unwrap_or(&UserCmd::new()))?;
    if reader.cursor != wire.len() { return Err("trailing usercmd bytes".into()); }
    Ok(command)
}

pub fn read_move(reader: &mut Reader<'_>, key: u32, base: &UserCmd) -> Result<Vec<UserCmd>> {
    let count = reader.number(1)?;
    if !(1..=32).contains(&count) { return Err("invalid usercmd count".into()); }
    let mut commands = Vec::with_capacity(count as usize);
    for _ in 0..count {
        let next = read_usercmd(reader, key, commands.last().unwrap_or(base))?;
        commands.push(next);
    }
    reader.raw(20)?; // Predicted origin/time is not authoritative simulation.
    Ok(commands)
}

pub fn decode_move(wire: &[u8], key: u32, base: Option<&UserCmd>) -> Result<Vec<UserCmd>> {
    let mut reader = Reader::new(wire);
    if reader.bits(3)? > 1 { return Err("expected client move message".into()); }
    let commands = read_move(&mut reader, key, base.unwrap_or(&UserCmd::new()))?;
    if reader.bits(3)? != 3 || reader.cursor != wire.len() {
        return Err("invalid move message terminator".into());
    }
    Ok(commands)
}

pub fn usercmd_key(acknowledgement: u32, checksum: u32, command: &[u8]) -> u32 {
    let value = command.iter().take_while(|&&c| c != 0).take(32).enumerate()
        .fold(0u32, |v, (i, &c)| v.wrapping_add(
            u32::from(if c >= 128 || c == 37 { 46 } else { c }) * (119 + i as u32)));
    acknowledgement ^ checksum ^ value ^ (value >> 10) ^ (value >> 20)
}

pub fn default_usercmd(player: &Fields) -> Result<UserCmd> {
    let mut command: UserCmd = FIELDS.iter().map(|&n| (n.to_string(), 0)).collect();
    let word = |index| -> Result<u32> {
        u32::try_from(*player.get(&index).unwrap_or(&0)).map_err(|_| "player field exceeds its word size".into())
    };
    let angle = |index, offset| -> Result<u32> {
        let value = (f32::from_bits(word(index)?) - f32::from_bits(word(offset)?)) * (65536.0f32 / 360.0);
        if !value.is_finite() { return Err("nonfinite usercmd angle".into()); }
        Ok((value as f64).round_ties_even().rem_euclid(65536.0) as u32)
    };
    for (name, index) in [("weapon",39),("alt",40),("offhand",53)] { command.insert(name.into(), word(index)?); }
    command.insert("pitch".into(), angle(19,70)?);
    command.insert("yaw".into(), angle(18,45)?);
    if word(54)? & 0x1000 != 0 {
        let flags = word(28)?;
        let mut buttons = if flags & 8 != 0 { 0x100 } else if flags & 4 != 0 { 0x200 } else { 0 };
        if f32::from_bits(word(41)?) != 0.0 { buttons |= 0x800; }
        command.insert("buttons".into(), buttons);
        command.insert("melee_target".into(), 2047);
    }
    Ok(command)
}
