//! Current MSG bit pools, sparse playerstate, configstrings and netchan framing.
//! Port of src/story_wire423.py. SPDX-License-Identifier: AGPL-3.0-or-later

use super::{Fields, Result};
use serde::Deserialize;
use std::{collections::BTreeSet, sync::OnceLock};

pub type Recipe = (usize, u32, u32, u32, Vec<u32>);
pub(crate) type Field = (usize, i32, u32);

#[derive(Deserialize)]
struct PlayerTable { fields: Vec<Field> }

#[derive(Deserialize)]
pub(crate) struct MatchTables {
    pub entity_player: Vec<Field>,
    pub entity_script_mover: Vec<Field>,
    pub client: Vec<Field>,
    pub event_widths: Vec<usize>,
}

pub(crate) fn player_fields() -> &'static [Field] {
    static TABLE: OnceLock<PlayerTable> = OnceLock::new();
    &TABLE.get_or_init(|| serde_json::from_str(include_str!("../../../../data/story-player-fields423.json"))
        .expect("checked-in 423 player field table")).fields
}

pub(crate) fn tables() -> &'static MatchTables {
    static TABLE: OnceLock<MatchTables> = OnceLock::new();
    TABLE.get_or_init(|| serde_json::from_str(include_str!("../../../../data/match-fields423.json"))
        .expect("checked-in 423 match field tables"))
}

#[derive(Default)]
pub(crate) struct Message { pub data: Vec<u8>, bit: usize }

impl Message {
    // Byte fields append without aligning this pool, exactly as MSG_WriteBits.
    pub fn bits(&mut self, value: u64, width: usize) {
        for i in 0..width {
            if self.bit % 8 == 0 {
                self.bit = self.data.len() * 8;
                self.data.push(0);
            }
            if i < 64 { self.data[self.bit / 8] |= (((value >> i) & 1) as u8) << (self.bit % 8); }
            self.bit += 1;
        }
    }
    pub fn flag(&mut self, value: bool) { self.bits(u64::from(value), 1); }
    fn index(&mut self, index: usize, previous: Option<usize>) {
        let sequential = index == previous.map_or(0, |p| p + 1);
        self.flag(sequential);
        if !sequential { self.bits(index as u64, 13); }
    }
}

pub fn encode_packets(payload: &[u8], sequence: u32, acknowledgement: u32,
                      challenge: u32, command: &[u8]) -> Result<Vec<Vec<u8>>> {
    if sequence == 0 || sequence >= 0x20000000 { return Err("sequence out of range".into()); }
    if acknowledgement > 0x7fffffff { return Err("acknowledgement out of range".into()); }
    if payload.is_empty() || payload.len() > 0x20000 - 8 {
        return Err("packet payload exceeds message buffer".into());
    }
    if command.contains(&0) || command.len() > 1023 { return Err("command exceeds client ring entry".into()); }
    let mut key = (challenge ^ sequence) as u8;
    let mut message = acknowledgement.to_le_bytes().to_vec();
    for (i, &byte) in payload.iter().enumerate() {
        if !command.is_empty() { key ^= command[i % command.len()].wrapping_shl((i & 1) as u32); }
        message.push(byte ^ key);
    }
    const STRIDE: usize = 0x482;
    if message.len() < STRIDE {
        let mut packet = sequence.to_le_bytes().to_vec();
        packet.extend(message);
        return Ok(vec![packet]);
    }
    let count = message.len().div_ceil(STRIDE);
    Ok(message.chunks(STRIDE).enumerate().map(|(index, part)| {
        let mut packet = (sequence | 0x80000000).to_le_bytes().to_vec();
        packet.extend_from_slice(&[index as u8, (count - 1) as u8]);
        packet.extend_from_slice(&(STRIDE as u16).to_le_bytes());
        packet.extend_from_slice(&(part.len() as u16).to_le_bytes());
        packet.extend_from_slice(part);
        packet
    }).collect())
}

pub(crate) fn float(word: u64) -> Result<f64> {
    let word = u32::try_from(word).map_err(|_| "snapshot field out of range")?;
    let value = f32::from_bits(word) as f64;
    if !value.is_finite() { return Err("nonfinite snapshot coordinate".into()); }
    Ok(value)
}

pub(crate) fn angle_word(value: u64) -> Result<u16> {
    Ok((float(value)? * 182.04444885253906).round_ties_even().rem_euclid(65536.0) as u16)
}

pub(crate) fn player_value(m: &mut Message, bits: i32, previous: u64, value: u64) -> Result<()> {
    match bits {
        -94 => {
            let event = (value & 0xffffffff) as usize;
            let parameter = value >> 32;
            let old_event = previous & 0xffffffff;
            let old_parameter = previous >> 32;
            let width = *tables().event_widths.get(event).ok_or("event out of range")?;
            if parameter >= 1u64 << width { return Err("event parameter out of range".into()); }
            m.flag(event as u64 != old_event);
            if event as u64 != old_event {
                m.data.push(event as u8);
                if width == 0 { return Ok(()); }
                let changed = width == 32 || old_parameter & ((1u64 << width) - 1) != parameter;
                m.flag(changed);
                if !changed { return Ok(()); }
            }
            if width == 32 { m.data.extend_from_slice(&(parameter as u32).to_le_bytes()); }
            else { m.bits(parameter, width); }
        }
        -87 | -100 => {
            if bits == -100 { m.bits(0, 2); }
            m.data.extend_from_slice(&angle_word(value)?.to_le_bytes());
        }
        -98 => { m.flag(true); m.bits(value, 30); }
        -70 | -97 => { m.flag(true); m.data.extend_from_slice(&(value as u32).to_le_bytes()); }
        -88 => { m.data.extend_from_slice(&((value ^ previous) as u32).to_le_bytes()); }
        0 => {
            m.bits(3, 2);
            m.data.extend_from_slice(&((value ^ previous) as u32).to_le_bytes());
        }
        -57 => m.bits(value, 1),
        -101 => { m.flag(value != previous); if value != previous { m.bits(value, 6); } }
        _ => {
            let width = if bits == -75 { m.flag(false); 8 } else {
                m.flag(value != 0);
                if value == 0 { return Ok(()); }
                bits.unsigned_abs() as usize
            };
            let delta = (value ^ previous) & ((1u64 << width) - 1);
            let remainder = width % 8;
            m.bits(delta, remainder);
            for shift in (remainder..width).step_by(8) { m.data.push((delta >> shift) as u8); }
        }
    }
    Ok(())
}

fn validate_player(state: &Fields) -> Result<()> {
    for (&index, &value) in state {
        let &(_, bits, _) = player_fields().get(index).ok_or("player field index out of range")?;
        if bits != -94 && value > u32::MAX as u64 { return Err("player field exceeds its word size".into()); }
        let valid = match bits {
            -94 => tables().event_widths.get((value & 0xffffffff) as usize)
                .is_some_and(|&width| value >> 32 < 1u64 << width),
            -87 | -100 => float(value).is_ok(),
            -98 => value < 1 << 30,
            -70 | -97 | -88 | 0 => true,
            -75 => value <= 255,
            -57 => value <= 1,
            -101 => value <= 63,
            1..=32 => value < 1u64 << bits,
            -8 | -16 => value < 1u64 << (-bits - 1) || value >= 0x100000000 - (1u64 << (-bits - 1)),
            _ => value == 0,
        };
        if !valid { return Err(format!("player field {index}: unsupported codec or value out of range")); }
    }
    Ok(())
}

pub(crate) fn write_player_fields(m: &mut Message, values: &Fields, base: &Fields) -> Result<()> {
    validate_player(base)?;
    validate_player(values)?;
    let fields = player_fields();
    let selected: Vec<usize> = fields.iter().enumerate().filter_map(|(i, &(_, _, hint))| {
        (hint == 3 || values.get(&i).unwrap_or(&0) != base.get(&i).unwrap_or(&0)).then_some(i)
    }).collect();
    let last = *selected.last().expect("423 always-sent player fields");
    m.flag(true);
    m.bits((last + 1) as u64, 8);
    let mut previous: i32 = -1;
    for index in selected {
        let (_, bits, hint) = fields[index];
        if hint == 2 && index < last { continue; }
        let mut gap = index as i32 - previous;
        m.flag(gap == 1);
        if gap != 1 {
            gap -= 1;
            while gap >= 15 { m.bits(15, 4); gap -= 15; }
            m.bits(gap as u64, 4);
        }
        player_value(m, bits, if hint == 3 { 0 } else { *base.get(&index).unwrap_or(&0) }, *values.get(&index).unwrap_or(&0))?;
        previous = index as i32;
    }
    for (index, &(_, bits, hint)) in fields.iter().enumerate().take(last) {
        if hint == 2 { player_value(m, bits, *base.get(&index).unwrap_or(&0), *values.get(&index).unwrap_or(&0))?; }
    }
    Ok(())
}

pub fn encode_playerstate(values: &Fields, _server_time: u32, base: Option<&Fields>) -> Result<Vec<u8>> {
    let mut m = Message::default();
    write_player_fields(&mut m, values, base.unwrap_or(&Fields::new()))?;
    m.bits(0, 14);
    m.data.push(6);
    Ok(m.data)
}

pub fn encode_baseline(values: &Fields, server_time: u32) -> Result<Vec<u8>> {
    let mut m = Message::default();
    m.data.push(0);
    m.data.extend_from_slice(&server_time.to_le_bytes());
    m.data.extend_from_slice(&[0, 8]);
    m.flag(false);
    write_player_fields(&mut m, values, &Fields::new())?;
    m.bits(0, 14);
    m.bits(0, 3); // No animation commands, actors, or sequential entity.
    m.flag(true);
    m.bits(2047, 11);
    m.bits(0, 2); // No clients or glass.
    m.data.push(6);
    Ok(m.data)
}

pub fn encode_configstrings(ordinary: &[(usize, String)], aliases: &[(usize, u32)], recipes: &[Recipe]) -> Result<Vec<u8>> {
    if ordinary.len() > 7058 || aliases.len() > 1023 || recipes.len() > 1023 {
        return Err("configstring count out of range".into());
    }
    let mut used = BTreeSet::new();
    for index in ordinary.iter().map(|r| r.0).chain(aliases.iter().map(|r| r.0)).chain(recipes.iter().map(|r| r.0)) {
        if index >= 7058 { return Err("configstring index out of range".into()); }
        if !used.insert(index) { return Err("duplicate configstring index".into()); }
    }
    let ranges = [(0,24),(344,856),(1975,2047),(6383,6416),(6544,7058)];
    let mut pool = 1usize;
    for (index, text) in ordinary {
        if !ranges.iter().any(|&(start,end)| start <= *index && *index < end) {
            return Err("ordinary string overwrites a registered resource".into());
        }
        if text.contains(['\0','%']) || !text.is_ascii() || text.len() > 8191 {
            return Err("configstring string would be normalized or truncated".into());
        }
        pool += text.len() + 1;
    }
    for (_, weapon) in aliases {
        if *weapon >= 1024 { return Err("weapon index out of range".into()); }
        pool += format!("* {weapon}").len() + 1;
    }
    for (_, weapon, camo, extra9, attachments) in recipes {
        if *weapon >= 1024 || *camo >= 256 || *extra9 >= 512 { return Err("recipe field out of range".into()); }
        if attachments.len() > 15 || attachments.iter().any(|&a| a >= 16384) {
            return Err("recipe attachment count or value out of range".into());
        }
        pool += format!("** {weapon} {camo} {extra9}").len() + 1;
        pool += attachments.iter().map(|a| a.to_string().len() + 1).sum::<usize>();
    }
    if pool > 0x20000 { return Err("configstring pool exceeds 128 KiB".into()); }
    let mut m = Message::default();
    m.data.extend_from_slice(&(ordinary.len() as i16).to_le_bytes());
    let mut previous = None;
    for (index, text) in ordinary {
        m.index(*index, previous);
        m.data.extend_from_slice(text.as_bytes());
        m.data.push(0);
        previous = Some(*index);
    }
    m.bits(aliases.len() as u64, 10);
    previous = None;
    for (index, weapon) in aliases {
        m.index(*index, previous);
        m.bits(*weapon as u64, 10);
        previous = Some(*index);
    }
    m.bits(recipes.len() as u64, 10);
    previous = None;
    for (index, weapon, camo, extra9, attachments) in recipes {
        m.index(*index, previous);
        m.bits(*weapon as u64, 10);
        m.bits(*camo as u64, 8);
        m.flag(*extra9 != 0);
        if *extra9 != 0 { m.bits(*extra9 as u64, 9); }
        m.bits(attachments.len() as u64, 4);
        for &attachment in attachments { m.bits(attachment as u64, 14); }
        previous = Some(*index);
    }
    m.data.push(6);
    Ok(m.data)
}

pub fn encode_gamestate(map_name: &str, category: &str, netconst_checksum: u32,
                        command_sequence: u32, client_number: u32, checksum_feed: u32,
                        ordinary: &[(usize, String)], aliases: &[(usize, u32)], recipes: &[Recipe]) -> Result<Vec<u8>> {
    for name in [map_name, category] {
        if name.is_empty() || name.len() >= 32 || name.contains(['\0','%']) || !name.is_ascii() {
            return Err("map and category must fit the client string buffers".into());
        }
    }
    if client_number >= 19 { return Err("client number must be in 0..18".into()); }
    let configstrings = encode_configstrings(ordinary, aliases, recipes)?;
    let mut wire = vec![3];
    wire.extend_from_slice(&command_sequence.to_le_bytes());
    wire.extend_from_slice(map_name.as_bytes());
    wire.push(0);
    wire.extend_from_slice(category.as_bytes());
    wire.push(0);
    wire.extend_from_slice(&netconst_checksum.to_le_bytes());
    wire.push(4);
    wire.extend(configstrings);
    wire.extend_from_slice(&client_number.to_le_bytes());
    wire.extend_from_slice(&checksum_feed.to_le_bytes());
    wire.push(6);
    if wire.len() > 0x20000 { return Err("gamestate message exceeds 128 KiB".into()); }
    Ok(wire)
}
