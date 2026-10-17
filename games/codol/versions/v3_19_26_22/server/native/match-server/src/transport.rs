//! Current 3.19 loopback-proxy transport; native stats sender 0x7f6ec0.
use crate::{NuketownRoom, snapshot::Snapshot};
use flate2::{Decompress, FlushDecompress, Status};
use std::net::SocketAddr;

const STATS_BYTES: usize = 0x8000;
const CHUNK: usize = 0x4d6;
const RESET: u32 = 0x07ff_ffff;

pub struct StatsUpload {
    compressed_length: u16,
    length: usize,
    chunks: Vec<Option<Vec<u8>>>,
    profile: Option<Vec<u8>>,
}

impl StatsUpload {
    pub fn new(compressed_length: u16) -> Result<Self, &'static str> {
        if compressed_length as usize > STATS_BYTES { return Err("invalid stats length"); }
        let length = if compressed_length == 0 { STATS_BYTES } else { compressed_length as usize };
        Ok(Self { compressed_length, length, chunks: vec![None; length.div_ceil(CHUNK)], profile: None })
    }

    pub fn profile(&self) -> Option<&[u8]> { self.profile.as_deref() }

    pub fn accept(&mut self, index: u8, length: u16, payload: &[u8]) -> Result<u32, &'static str> {
        let index = index as usize;
        if length != self.compressed_length || index >= self.chunks.len() {
            return Err("stats length or index changed");
        }
        if payload.len() != CHUNK.min(self.length - index * CHUNK) {
            return Err("invalid stats fragment size");
        }
        if self.chunks[index].as_deref().is_some_and(|old| old != payload) {
            return Err("conflicting stats duplicate");
        }
        self.chunks[index] = Some(payload.to_vec());
        let missing = self.chunks.iter().enumerate().fold(0, |mask, (i, chunk)|
            mask | if chunk.is_none() { 1 << i } else { 0 });
        if missing == 0 && self.profile.is_none() {
            let wire: Vec<u8> = self.chunks.iter().flat_map(|c| c.as_ref().unwrap().iter().copied()).collect();
            let profile = if length == 0 { wire } else {
                let mut profile = vec![0; STATS_BYTES + 1];
                let mut decoder = Decompress::new(true);
                let status = decoder.decompress(&wire, &mut profile, FlushDecompress::Finish)
                    .map_err(|_| "invalid stats zlib stream")?;
                if status != Status::StreamEnd || decoder.total_in() != wire.len() as u64
                    || decoder.total_out() != STATS_BYTES as u64 {
                    return Err("stats must decode to exactly 32768 bytes without trailing data");
                }
                profile.truncate(STATS_BYTES);
                profile
            };
            self.profile = Some(profile);
        }
        Ok(missing)
    }
}

fn oob(text: &str) -> Vec<u8> { [b"\xff\xff\xff\xff", text.as_bytes(), b"\0"].concat() }

/// Unfragmented server envelope consumed by native 0x470a60; no compression flag.
pub fn server_packet(payload: &[u8], sequence: u32, ack: u32, challenge: u32,
                     command: &[u8]) -> Result<Vec<u8>, &'static str> {
    if payload.is_empty() || payload.len() > 1024 || !(1..=0x1fff_ffff).contains(&sequence)
        || ack > 0x7fff_ffff || command.len() > 1023 {
        return Err("unsupported server packet size or flags");
    }
    let command = command.split(|&byte| byte == 0).next().unwrap();
    let mut output = Vec::with_capacity(8 + payload.len());
    output.extend(sequence.to_le_bytes());
    output.extend(ack.to_le_bytes());
    let mut key = (sequence ^ challenge) as u8;
    for (i, byte) in payload.iter().enumerate() {
        if !command.is_empty() { key ^= command[i % command.len()].wrapping_shl((i & 1) as u32); }
        output.push(byte ^ key);
    }
    Ok(output)
}

pub struct ClientControl {
    pub sequence: u32,
    pub ack: u32,
    pub commands: Vec<(u32, Vec<u8>)>,
}

/// Native 0x4709e0 and 0x5b2c90. No server commands are published in this phase.
/// Only the reliable prefix is consumed; movement remains for the simulation phase.
pub fn client_control(packet: &[u8], challenge: u32) -> Option<ClientControl> {
    if packet.len() < 14 || packet[4] > 1 || packet[9..13] != [0; 4] { return None; }
    let sequence = u32::from_le_bytes(packet[..4].try_into().ok()?);
    let ack = u32::from_le_bytes(packet[5..9].try_into().ok()?);
    if !(1..=0x1fff_ffff).contains(&sequence) || ack > 0x1fff_ffff { return None; }
    let key = (ack ^ challenge ^ packet[4] as u32) as u8;
    let plain: Vec<_> = packet[13..].iter().map(|b| b ^ key).collect();
    let (mut read, mut bit) = (0, 0);
    let mut commands = Vec::new();
    loop {
        let mut op = 0;
        for shift in 0..3 {
            if bit % 8 == 0 { bit = read * 8; read += 1; }
            op |= ((plain.get(bit / 8)? >> (bit % 8)) & 1) << shift;
            bit += 1;
        }
        match op {
            0 | 1 | 3 => return Some(ClientControl { sequence, ack, commands }),
            2 => {
                let number = u32::from_le_bytes(plain.get(read..read+4)?.try_into().ok()?);
                if number == 0 || number > 0x7fff_ffff { return None; }
                read += 4;
                let length = plain[read..].iter().take(1024).position(|&b| b == 0)?;
                commands.push((number, plain[read..read+length].to_vec()));
                read += length + 1;
            }
            _ => return None,
        }
    }
}

pub struct Session {
    room: NuketownRoom,
    challenge: u32,
    peer: Option<SocketAddr>,
    connected: bool,
    upload: Option<StatsUpload>,
    gamestate: Option<Vec<u8>>,
    gamestate_packet: Option<Vec<u8>>,
    client_sequence: u32,
    server_sequence: u32,
    loaded: bool,
    snapshot: Option<Snapshot>,
    first_frame: Option<(u32, Vec<u8>)>,
    first_tick: Option<u64>,
    due: u64,
    last_ack: u32,
    command_sequence: u32,
    command: Vec<u8>,
}

impl Session {
    pub fn new(room: NuketownRoom, challenge: u32) -> Self {
        Self { room, challenge, peer: None, connected: false, upload: None,
            gamestate: None, gamestate_packet: None, client_sequence: 0, server_sequence: 0, loaded: false,
            snapshot: None, first_frame: None, first_tick: None, due: 0, last_ack: 0,
            command_sequence: 0, command: Vec::new() }
    }

    pub fn room(&self) -> &NuketownRoom { &self.room }
    pub fn profile(&self) -> Option<&[u8]> { self.upload.as_ref().and_then(StatsUpload::profile) }
    pub fn map_loaded(&self) -> bool { self.loaded }

    pub fn set_spawn(&mut self, origin: [f32; 3], yaw: f32) -> Result<(), &'static str> {
        self.snapshot = Some(Snapshot::new(origin, yaw)?);
        Ok(())
    }

    pub fn tick(&mut self, now: u64) -> Option<(SocketAddr, Vec<u8>)> {
        if !self.connected || !self.loaded || now < self.due { return None; }
        let snapshot = self.snapshot.as_ref()?;
        let peer = self.peer?;
        self.due = now + 50;
        if let Some((sequence, packet)) = &self.first_frame {
            if self.last_ack < *sequence { return Some((peer, packet.clone())); }
        }
        let first = *self.first_tick.get_or_insert(now);
        let stamp = u32::try_from(1000 + now.saturating_sub(first)).ok()?;
        self.server_sequence += 1;
        let delta = if self.first_frame.is_none() { 0 } else {
            let gap = self.server_sequence - self.last_ack;
            if (1..=15).contains(&gap) { gap as u8 } else { 1 }
        };
        let payload = snapshot.encode(stamp, stamp, delta).ok()?;
        let packet = server_packet(&payload, self.server_sequence, self.command_sequence,
                                   self.challenge, &self.command).ok()?;
        if self.first_frame.is_none() { self.first_frame = Some((self.server_sequence, packet.clone())); }
        Some((peer, packet))
    }

    /// Prepared from this process's NCS capture by the version-specific resource builder.
    pub fn set_gamestate(&mut self, payload: Vec<u8>) -> Result<(), &'static str> {
        if payload.len() < 14 || payload.len() > 1024 || payload[0] != 3 || payload.last() != Some(&5) {
            return Err("unsupported gamestate payload");
        }
        self.gamestate = Some(payload);
        Ok(())
    }

    fn load_map(&mut self, peer: SocketAddr, packet: &[u8]) -> Option<Vec<u8>> {
        if !self.connected || self.peer != Some(peer) || self.profile().is_none() || packet.len() < 14 {
            return None;
        }
        let control = client_control(packet, self.challenge)?;
        let ack = control.ack;
        if control.sequence <= self.client_sequence || ack > self.server_sequence { return None; }
        let (mut number, mut command) = (self.command_sequence, self.command.clone());
        for (next, text) in control.commands {
            if next <= number { continue; }
            if next != number + 1 { return None; }
            number = next; command = text;
        }
        self.client_sequence = control.sequence;
        self.last_ack = self.last_ack.max(ack);
        self.command_sequence = number;
        self.command = command;
        if self.loaded { return None; }
        if let Some(sent) = &self.gamestate_packet {
            return (ack < self.server_sequence).then(|| sent.clone());
        }
        if self.server_sequence < 3 {
            self.server_sequence += 1;
            return server_packet(&[5], self.server_sequence, 0, self.challenge, b"").ok();
        }
        let state = self.gamestate.as_ref()?;
        self.server_sequence += 1;
        let reply = server_packet(state, self.server_sequence, 0, self.challenge, b"").ok()?;
        self.gamestate_packet = Some(reply.clone());
        Some(reply)
    }

    fn accept_stats(&mut self, body: &[u8]) -> Result<u32, &'static str> {
        if body.len() < 3 { return Err("truncated stats header"); }
        let length = u16::from_le_bytes([body[1], body[2]]);
        if self.upload.is_none() { self.upload = Some(StatsUpload::new(length)?); }
        self.upload.as_mut().unwrap().accept(body[0], length, &body[3..])
    }

    pub fn handle(&mut self, peer: SocketAddr, packet: &[u8]) -> Option<Vec<u8>> {
        if !packet.starts_with(b"\xff\xff\xff\xff") { return self.load_map(peer, packet); }
        if let Some(body) = packet.strip_prefix(b"\xff\xff\xff\xffstats\0") {
            if !self.connected || self.peer != Some(peer) { return None; }
            let mask = self.accept_stats(body).unwrap_or_else(|_| { self.upload = None; RESET });
            return Some(oob(&format!("statResponse {mask}")));
        }
        let body = packet.strip_prefix(b"\xff\xff\xff\xff")?;
        let text = std::str::from_utf8(body.strip_suffix(b"\0").unwrap_or(body)).ok()?;
        if !text.is_ascii() || text.bytes().any(|b| !(32..=126).contains(&b)) { return None; }
        if let Some(token) = text.strip_prefix("getchallenge 0 \"").and_then(|s| s.strip_suffix('"')) {
            if token.is_empty() || token.len() > 45 || token.contains('"')
                || (self.connected && self.peer != Some(peer)) { return None; }
            self.peer = Some(peer);
            return Some(oob(&format!("challengeResponse {}", self.challenge)));
        }
        if let Some(connect) = text.strip_prefix("connect ") {
            if self.peer != Some(peer) && (self.peer.is_some() || self.challenge != 0) { return None; }
            let (uid, info) = connect.split_once(' ')?;
            if uid.len() != 16 || !uid.bytes().all(|b| b.is_ascii_hexdigit())
                || u64::from_str_radix(uid, 16).ok()? != self.room.players()[0].uid { return None; }
            let info = info.strip_prefix('"')?.strip_suffix('"')?.strip_prefix('\\')?;
            let fields: Vec<_> = info.split('\\').collect();
            if fields.len() % 2 != 0 { return None; }
            let value = |key| fields.chunks_exact(2).rev().find(|p| p[0] == key).map(|p| p[1]);
            if value("challenge")?.parse::<u32>().ok()? != self.challenge {
                return None;
            }
            self.peer = Some(peer);
            self.connected = true;
            let rules = self.room.rules();
            return Some(oob(&format!("connectResponse \\mapname\\{}\\gametype\\{}\\sv_maxclients\\18\\protocol\\1",
                                    rules.map, rules.gametype)));
        }
        if text == "disconnect" && self.peer == Some(peer) {
            self.connected = false;
            self.upload = None;
            self.peer = None;
            self.gamestate_packet = None;
            self.client_sequence = 0;
            self.server_sequence = 0;
            self.loaded = false;
            self.first_frame = None;
            self.first_tick = None;
            self.due = 0;
            self.last_ack = 0;
            self.command_sequence = 0;
            self.command.clear();
        }
        if text == "gamestateupdate 6" && self.peer == Some(peer) && self.gamestate_packet.is_some() {
            self.loaded = true;
        }
        None
    }
}
