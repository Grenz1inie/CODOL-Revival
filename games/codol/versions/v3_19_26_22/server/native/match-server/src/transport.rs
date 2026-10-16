//! Current 3.19 loopback-proxy transport; native stats sender 0x7f6ec0.
use crate::NuketownRoom;
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

pub struct Session {
    room: NuketownRoom,
    challenge: u32,
    peer: Option<SocketAddr>,
    connected: bool,
    upload: Option<StatsUpload>,
}

impl Session {
    pub fn new(room: NuketownRoom, challenge: u32) -> Self {
        Self { room, challenge, peer: None, connected: false, upload: None }
    }

    pub fn room(&self) -> &NuketownRoom { &self.room }
    pub fn profile(&self) -> Option<&[u8]> { self.upload.as_ref().and_then(StatsUpload::profile) }

    fn accept_stats(&mut self, body: &[u8]) -> Result<u32, &'static str> {
        if body.len() < 3 { return Err("truncated stats header"); }
        let length = u16::from_le_bytes([body[1], body[2]]);
        if self.upload.is_none() { self.upload = Some(StatsUpload::new(length)?); }
        self.upload.as_mut().unwrap().accept(body[0], length, &body[3..])
    }

    pub fn handle(&mut self, peer: SocketAddr, packet: &[u8]) -> Option<Vec<u8>> {
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
        }
        None
    }
}
