//! Full current snapshots from independent raw-word state.
//! Port of src/match_server/snapshot.py; source attribution in its NOTICE.md.
//! SPDX-License-Identifier: AGPL-3.0-or-later

use super::{Fields, Result};
use super::wire::{Message, angle_word, float, player_value, tables, write_player_fields};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Inventory {
    pub weapon: u32,
    pub ammo_type: u32,
    pub clip_type: u32,
    pub clip: u32,
    pub reserve: u32,
    #[serde(default)]
    pub raised: bool,
}

fn delta(m: &mut Message, bits: i32, value: u64, center: [i32; 3]) -> Result<()> {
    if bits != -94 && value > u32::MAX as u64 { return Err("snapshot field out of range".into()); }
    match bits {
        -83 | -82 | -81 => {
            let lo = center[(bits + 83) as usize] as i64 - 32768;
            let v = (float(value)? + 0.5).floor();
            if v < lo as f64 || v > (lo + 65535) as f64 || lo > 0 || lo + 65535 < 0 {
                return Err("position outside map encoding range".into());
            }
            m.flag(true);
            m.bits(((-lo) ^ (v as i64 - lo)) as u64, 16);
        }
        -79 | -87 | -100 => {
            if bits != -87 { m.bits(0, 2); }
            m.data.extend_from_slice(&angle_word(value)?.to_le_bytes());
        }
        -80 | -78 | -73 | -71 => m.data.extend_from_slice(&(value as u32).to_le_bytes()),
        -74 | -72 => { m.flag(true); m.data.extend_from_slice(&(value as u32).to_le_bytes()); }
        -77 => {
            if value > 255 { return Err("entity type out of range".into()); }
            m.data.push(value as u8);
        }
        -76 => {
            if value > 127 && value < 0xffffff80 { return Err("signed byte out of range".into()); }
            m.flag(false);
            m.data.push(value as u8);
        }
        -96 => {
            if value > 2047 { return Err("entity reference out of range".into()); }
            m.flag(value == 2046);
            if value != 2046 {
                m.flag(value == 0);
                if value != 0 { m.bits(value & 7, 3); m.data.push((value >> 3) as u8); }
            }
        }
        -98 => {
            if value > 0x3fffffff { return Err("entity flags out of range".into()); }
            m.flag(true);
            m.bits(value, 30);
        }
        -55 => {
            if value > 8191 { return Err("packed player flags out of range".into()); }
            m.flag(value & 127 != 0);
            if value & 127 != 0 { m.bits(value & 15, 4); m.bits((value >> 4) & 7, 3); }
            m.flag(value & 0x1f80 != 0);
            if value & 0x1f80 != 0 { m.bits(value >> 12, 1); m.bits((value >> 7) & 31, 5); }
        }
        -94 | -93 => {
            let (event, parameter) = if bits == -94 { ((value & 0xffffffff) as usize, value >> 32) } else { (0, value) };
            let width = *tables().event_widths.get(event).ok_or("event out of range")?;
            if parameter >= 1u64 << width { return Err("event parameter out of range".into()); }
            if bits == -94 {
                m.flag(event != 0);
                if event != 0 {
                    m.data.push(event as u8);
                    if width != 0 {
                        m.flag(width == 32 || parameter != 0);
                        if width < 32 && parameter == 0 { return Ok(()); }
                    }
                }
            }
            if width == 32 { m.data.extend_from_slice(&(parameter as u32).to_le_bytes()); }
            else { m.bits(parameter, width); }
        }
        _ => {
            if bits > 0 && value >= 1u64 << bits { return Err("snapshot bit field out of range".into()); }
            player_value(m, bits, 0, value)?;
        }
    }
    Ok(())
}

fn entity(m: &mut Message, values: &Fields, center: [i32; 3]) -> Result<()> {
    let kind = *values.get(&4).unwrap_or(&1);
    let fields = match kind { 1 => &tables().entity_player, 6 => &tables().entity_script_mover,
        _ => return Err("only player and static mover entities are supported".into()) };
    if values.keys().any(|offset| !fields.iter().any(|f| f.0 == *offset)) {
        return Err("unknown player entity field".into());
    }
    m.bits(2, 3); // Not removed, changed with an explicit type transition.
    m.bits((fields.len() - 1) as u64, 6);
    for &(offset, bits, _) in fields {
        m.flag(true);
        delta(m, bits, if offset == 4 { kind } else { *values.get(&offset).unwrap_or(&0) }, center)?;
    }
    Ok(())
}

pub fn encode_player_entity(values: &Fields, position_base: [i32; 3]) -> Result<Vec<u8>> {
    if *values.get(&4).unwrap_or(&1) != 1 { return Err("expected player entity".into()); }
    let mut m = Message::default();
    entity(&mut m, values, position_base)?;
    m.data.push(6);
    Ok(m.data)
}

/// Parse caller-provided current baseline records; no resources are bundled here.
pub fn baseline_entities(data: &[u8]) -> Result<Vec<(usize, Fields)>> {
    if data.len() < 8 || &data[..8] != b"IWCB000\x01" || (data.len() - 8) % 272 != 0 || data.len() > 190408 {
        return Err("invalid current baseline length/header".into());
    }
    let mut result = Vec::new();
    for record in data[8..].chunks_exact(272) {
        let number = u32::from_le_bytes(record[..4].try_into().unwrap()) as usize;
        let kind = u32::from_le_bytes(record[4..8].try_into().unwrap());
        if !(2..2047).contains(&number) || ![6,8].contains(&kind) { return Err("unsupported baseline entity".into()); }
        if kind == 8 { continue; } // Ambient FX remain deferred, as in Python.
        let mut values = Fields::new();
        for &(offset, bits, _) in &tables().entity_script_mover {
            let size = if bits == -94 { 8 } else { 4 };
            let mut raw = [0;8];
            raw[..size].copy_from_slice(&record[offset..offset+size]);
            values.insert(offset, u64::from_le_bytes(raw));
        }
        result.push((number, values));
    }
    result.sort_by_key(|row| row.0);
    if result.windows(2).any(|rows| rows[0].0 == rows[1].0) { return Err("duplicate baseline entity".into()); }
    Ok(result)
}

fn inventory(m: &mut Message, health: u16, inventory: Option<&Inventory>, spawn_count: u8) -> Result<()> {
    if health > 32767 { return Err("health out of range".into()); }
    m.flag(true);
    m.bits(13, 4);
    m.data.extend_from_slice(&health.to_le_bytes());
    m.data.extend_from_slice(&100u16.to_le_bytes());
    m.data.push(spawn_count);
    let Some(inventory) = inventory else { m.bits(0,13); return Ok(()); };
    for (value, limit) in [(inventory.weapon,1023),(inventory.ammo_type,1023),
        (inventory.clip_type,1022),(inventory.clip,511),(inventory.reserve,2047)] {
        if value > limit { return Err("inventory field out of range".into()); }
    }
    m.flag(true);
    m.bits(0,4);
    m.bits(inventory.clip_type as u64,10);
    m.flag(true);
    m.bits(inventory.clip as u64,9);
    m.bits(0,2);
    m.bits(7,3);
    m.bits(inventory.weapon as u64,10);
    m.bits(u64::from(inventory.raised),5);
    m.bits(0,14);
    m.flag(true);
    m.bits(0,4);
    m.bits(inventory.ammo_type as u64,10);
    m.bits(inventory.reserve as u64,11);
    m.bits(0,11);
    Ok(())
}

fn number(m: &mut Message, number: usize, previous: i32) {
    let delta = number as i32 - previous;
    m.flag(delta == 1);
    if delta != 1 {
        m.flag(delta >= 512);
        m.bits(if delta >= 512 { number as u64 } else { delta as u64 }, if delta >= 512 { 11 } else { 9 });
    }
}

pub fn encode_snapshot(player: &Fields, server_time: u32, health: u16,
                       inventory_value: Option<&Inventory>, spawn_count: u8,
                       entities: &[(usize, Fields)], clients: &[(usize, Fields)],
                       position_base: [i32; 3]) -> Result<Vec<u8>> {
    for (rows, limit) in [(entities,2047), (clients,32)] {
        if rows.iter().any(|r| r.0 >= limit) || rows.windows(2).any(|r| r[0].0 >= r[1].0) {
            return Err("invalid or unordered snapshot players".into());
        }
    }
    let mut m = Message::default();
    m.data.push(0);
    m.data.extend_from_slice(&server_time.to_le_bytes());
    m.data.extend_from_slice(&[0,0]); // flags 0 against Connection's pinned empty baseline.
    m.flag(false);
    write_player_fields(&mut m, player, &Fields::new())?;
    inventory(&mut m, health, inventory_value, spawn_count)?;
    m.bits(0,2);
    let mut previous = -1;
    for (id, values) in entities {
        number(&mut m,*id,previous);
        entity(&mut m,values,position_base)?;
        previous = *id as i32;
    }
    number(&mut m,2047,previous);
    previous = -1;
    let fields = &tables().client;
    for (id, values) in clients {
        m.flag(true);
        m.flag(*id as i32 == previous+1);
        if *id as i32 != previous+1 { m.bits(*id as u64,5); }
        m.flag(false);
        if values.keys().any(|offset| !fields.iter().any(|f| f.0 == *offset)) {
            return Err("unknown client state field".into());
        }
        let selected: Vec<usize> = fields.iter().enumerate()
            .filter_map(|(i,f)| (*values.get(&f.0).unwrap_or(&0) != 0).then_some(i)).collect();
        m.flag(!selected.is_empty());
        if let Some(&last) = selected.last() {
            m.bits(last as u64,7);
            let mut previous_field: i32 = -1;
            for i in selected {
                m.bits(0,(i as i32-previous_field-1) as usize);
                m.flag(true);
                let (offset,bits,_) = fields[i];
                delta(&mut m,bits,values[&offset],position_base)?;
                previous_field = i as i32;
            }
        }
        previous = *id as i32;
    }
    m.bits(0,2);
    m.data.push(6);
    Ok(m.data)
}
