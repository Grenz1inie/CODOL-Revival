//! Admission, stats, gamestate and reliable/input state for one human.
//! Port of src/match_server/connection.py. SPDX-License-Identifier: AGPL-3.0-or-later

use super::{Fields, Result, UserCmd};
use super::input::{Reader, default_usercmd, read_move, usercmd_key};
use super::wire::{Recipe, encode_baseline, encode_gamestate, encode_packets};
use flate2::{Decompress, FlushDecompress, Status};
use rand::{Rng, rngs::OsRng};
use serde::de::DeserializeOwned;
use serde_json::Value;
use std::collections::BTreeMap;

#[derive(Default)]
pub struct StatsTransfer {
    pub length: Option<u16>,
    pub fragments: BTreeMap<usize, Vec<u8>>,
    pub profile: Option<Vec<u8>>,
}

impl StatsTransfer {
    pub fn new() -> Self { Self::default() }

    pub fn accept(&mut self, packet: &[u8]) -> Result<u32> {
        if packet.len() < 3 { return Err("truncated stats fragment".into()); }
        let index = packet[0] as usize;
        let compressed = u16::from_le_bytes([packet[1],packet[2]]);
        let length = if compressed == 0 { 32768 } else { compressed as usize };
        let count = length.div_ceil(1238);
        if length > 32768 || index >= count || packet.len()-3 != 1238.min(length-index*1238) {
            return Err("invalid stats fragment range".into());
        }
        if self.length.is_some_and(|n| n != compressed) { return Err("stats size changed during transfer".into()); }
        if self.fragments.get(&index).is_some_and(|data| data != &packet[3..]) {
            return Err("stats duplicate has different content".into());
        }
        let mut fragments = self.fragments.clone();
        fragments.insert(index,packet[3..].to_vec());
        let mask = fragments.keys().fold(0u32,|mask,&i| mask | (1 << i));
        let missing = ((1u32 << count)-1) ^ mask;
        if missing == 0 && self.profile.is_none() {
            let mut profile: Vec<u8> = fragments.values().flatten().copied().collect();
            if compressed != 0 {
                let mut inflater = Decompress::new(true);
                let mut output = vec![0;32769];
                let status = inflater.decompress(&profile,&mut output,FlushDecompress::Finish)
                    .map_err(|_| "invalid compressed stats")?;
                if status != Status::StreamEnd || inflater.total_in() != profile.len() as u64 {
                    return Err("incomplete or trailing compressed stats".into());
                }
                output.truncate(inflater.total_out() as usize);
                profile = output;
            }
            // Current upload retains a CRC computed before native preparation.
            // DATA authenticates it; the lobby save has a separate CRC contract.
            if profile.len() != 32768 { return Err("invalid stats size".into()); }
            self.profile = Some(profile);
        }
        self.length = Some(compressed);
        self.fragments = fragments;
        Ok(missing)
    }
}

pub struct Connection {
    pub uid: u64,
    pub map_name: String,
    pub challenge: u32,
    pub server_id: u8,
    pub checksum_feed: u32,
    pub phase: String,
    pub loading_status: u8,
    pub stats: StatsTransfer,
    pub received: u32,
    pub sent: u32,
    pub reliable: u32,
    pub command: Vec<u8>,
    pub pending_commands: Vec<UserCmd>,
    pub server_commands: BTreeMap<u32,Vec<u8>>,
    pub server_ack: u32,
    pub published_command: u32,
    pub message_ack: u32,
    pub input_bases: BTreeMap<u32,UserCmd>,
    pub default_input: UserCmd,
    pub world_baseline_sent: bool,
    pub position_base: [i32;3],
    pub gamestate: Vec<u8>,
}

fn option<T: DeserializeOwned>(options: &Value, name: &str, default: T) -> Result<T> {
    options.get(name).map_or(Ok(default),|value| serde_json::from_value(value.clone())
        .map_err(|e| format!("invalid {name}: {e}")))
}

impl Connection {
    pub fn new(uid: u64, options: &Value) -> Result<Self> {
        if uid == 0 { return Err("invalid admitted identity".into()); }
        if !options.is_object() { return Err("connection options must be an object".into()); }
        let map_name: String = option(options,"map_name","mp_killhouse_sh".into())?;
        if !["mp_killhouse_sh","mp_nuked"].contains(&map_name.as_str()) { return Err("unsupported map identity".into()); }
        let netconst_checksum = options.get("netconst_checksum").and_then(Value::as_u64)
            .and_then(|n| u32::try_from(n).ok()).ok_or("netconst_checksum must be uint32")?;
        let position_base: [i32;3] = option(options,"position_base",[0;3])?;
        if position_base.iter().any(|v| !(-32767..=32768).contains(v)) { return Err("invalid map position base".into()); }
        let configstrings: Vec<(usize,String)> = if options.get("configstrings").is_some_and(Value::is_object) {
            let rows: BTreeMap<usize,String> = option(options,"configstrings",BTreeMap::new())?;
            rows.into_iter().collect()
        } else { option(options,"configstrings",Vec::new())? };
        let aliases: Vec<(usize,u32)> = option(options,"aliases",Vec::new())?;
        let recipes: Vec<Recipe> = option(options,"recipes",Vec::new())?;
        let challenge = OsRng.gen_range(1..0x7fffffff);
        let server_id = OsRng.gen_range(1..255);
        let checksum_feed: u32 = OsRng.r#gen();
        let mut rows: BTreeMap<usize,String> = configstrings.into_iter().collect();
        rows.insert(0,format!("\\mapname\\{map_name}\\g_gametype\\dm\\2485\\2"));
        rows.insert(2,"cod".into());
        rows.insert(3,server_id.to_string());
        rows.insert(6415,"0 0 1 1".into());
        rows.insert(16,format!("{} {} {}",position_base[0],position_base[1],position_base[2]));
        let gamestate = encode_gamestate(&map_name,"mp",netconst_checksum,0,0,checksum_feed,
            &rows.into_iter().collect::<Vec<_>>(),&aliases,&recipes)?;
        Ok(Self { uid,map_name,challenge,server_id,checksum_feed,phase:"reserved".into(),
            loading_status:0,stats:StatsTransfer::new(),received:0,sent:0,reliable:0,
            command:Vec::new(),pending_commands:Vec::new(),server_commands:BTreeMap::from([(0,Vec::new())]),
            server_ack:0,published_command:0,message_ack:0,input_bases:BTreeMap::from([(0,UserCmd::new())]),
            default_input:UserCmd::new(),world_baseline_sent:false,position_base,gamestate })
    }

    fn userinfo<'a>(&self, value: &'a str) -> Result<BTreeMap<&'a str,&'a str>> {
        if !value.starts_with('\\') || value.len() >= 1024 || value.bytes().any(|c| !(32..127).contains(&c) || [b'"',b';'].contains(&c)) {
            return Err("invalid userinfo".into());
        }
        let pairs: Vec<&str> = value[1..].split('\\').collect();
        if pairs.len() % 2 != 0 || pairs.iter().step_by(2).any(|key| key.is_empty()) {
            return Err("invalid userinfo pairs".into());
        }
        let fields: BTreeMap<&str,&str> = pairs.chunks_exact(2).map(|pair| (pair[0],pair[1])).collect();
        if fields.len() != pairs.len()/2 { return Err("duplicate userinfo key".into()); }
        if fields.get("xuid").copied().unwrap_or("").to_ascii_lowercase() != format!("{:016x}",self.uid) {
            return Err("userinfo identity does not match reservation".into());
        }
        Ok(fields)
    }

    fn identity(&self, text: &str) -> bool {
        text.len() == 16 && text.bytes().all(|c| c.is_ascii_hexdigit()) && u64::from_str_radix(text,16) == Ok(self.uid)
    }

    fn oob(&mut self, packet: &[u8]) -> Result<Option<Vec<u8>>> {
        if packet.starts_with(b"stats\0") {
            if self.phase == "reserved" { return Err("stats require a connected client".into()); }
            let missing = self.stats.accept(&packet[6..])?;
            return Ok(Some([b"\xff\xff\xff\xff".as_slice(),format!("statResponse {missing}\0").as_bytes()].concat()));
        }
        let packet = packet.strip_suffix(&[0]).unwrap_or(packet);
        if !packet.is_ascii() { return Err("invalid connection text".into()); }
        let text = std::str::from_utf8(packet).map_err(|_| "invalid connection text")?;
        if text == "heartbeat" && self.phase != "reserved" { return Ok(Some(b"\xff\xff\xff\xffheartbeatresponse".to_vec())); }
        if let Some(stage) = text.strip_prefix("gamestateupdate ") {
            if stage.len() == 1 && (b'0'..=b'6').contains(&stage.as_bytes()[0]) {
                if !["primed","active"].contains(&self.phase.as_str()) { return Err("loading update before gamestate".into()); }
                self.loading_status = stage.as_bytes()[0] - b'0';
                return Ok(None);
            }
        }
        if let Some(id) = text.strip_prefix("getchallenge ") {
            let id = id.strip_prefix("0 \"").and_then(|id| id.strip_suffix('"')).unwrap_or(id);
            if !self.identity(id) { return Err("challenge identity does not match reservation".into()); }
            return Ok(Some([b"\xff\xff\xff\xff".as_slice(),format!("challengeResponse {}\0",self.challenge).as_bytes()].concat()));
        }
        let (id, info) = text.strip_prefix("connect ").and_then(|s| s.split_once(" \""))
            .and_then(|(id,info)| info.strip_suffix('"').map(|info| (id,info)))
            .filter(|(id,info)| self.identity(id) && !info.contains(['\0','"']))
            .ok_or("invalid connect identity or command")?;
        debug_assert!(self.identity(id));
        let fields = self.userinfo(info)?;
        if fields.get("challenge").copied() != Some(self.challenge.to_string().as_str()) {
            return Err("connect challenge mismatch".into());
        }
        if self.phase == "reserved" { self.phase = "connected".into(); }
        let response = format!("connectResponse \\mapname\\{}\\gametype\\dm\\sv_maxclients\\2\\protocol\\1\\shortversion\\3.3.3.3\0",self.map_name);
        Ok(Some([b"\xff\xff\xff\xff".as_slice(),response.as_bytes()].concat()))
    }

    pub fn queue_command(&mut self, command: &[u8]) -> Result<u32> {
        if command.is_empty() || command.contains(&0) || command.len() > 1023 {
            return Err("invalid reliable server command".into());
        }
        let sequence = self.server_commands.last_key_value().unwrap().0.checked_add(1)
            .ok_or("server command sequence exhausted")?;
        if sequence - self.server_ack > 32 { return Err("too many unacknowledged server commands".into()); }
        self.server_commands.insert(sequence,command.to_vec());
        Ok(sequence)
    }

    pub fn send(&mut self, payload: &[u8], player_fields: Option<&Fields>) -> Result<Vec<Vec<u8>>> {
        let input = player_fields.map(default_usercmd).transpose()?;
        let mut packets = Vec::new();
        if player_fields.is_some() && !self.world_baseline_sent {
            packets = self.send(&encode_baseline(&Fields::new(),0)?,None)?;
            self.world_baseline_sent = true;
        }
        let mut message = Vec::new();
        for (&number,text) in &self.server_commands {
            if number > self.server_ack {
                message.push(1);
                message.extend_from_slice(&number.to_le_bytes());
                message.extend_from_slice(text);
                message.push(0);
            }
        }
        message.extend_from_slice(payload);
        let sequence = self.sent.checked_add(1).ok_or("sequence out of range")?;
        packets.extend(encode_packets(&message,sequence,self.reliable,self.challenge,&self.command)?);
        self.sent = sequence;
        self.published_command = *self.server_commands.last_key_value().unwrap().0;
        if let Some(input) = input { self.default_input = input; }
        self.input_bases.insert(self.sent,self.default_input.clone());
        let (sent,ack) = (self.sent,self.message_ack);
        self.input_bases.retain(|&n,_| sent < 64 || n > sent-64 || n == ack);
        Ok(packets)
    }

    fn validate_reliable(&self, candidate: &[u8]) -> Result<()> {
        if candidate.starts_with(b"userinfo \"") && candidate.ends_with(b"\"") && candidate.len() >= 11 {
            let text = std::str::from_utf8(&candidate[10..candidate.len()-1]).map_err(|_| "invalid userinfo")?;
            self.userinfo(text)?;
            return Ok(());
        }
        if candidate == b"s" { return Ok(()); }
        if let Ok(text) = std::str::from_utf8(candidate) {
            if let Some(action) = text.strip_prefix("n ") {
                if let Ok(n) = action.parse::<u32>() {
                    if (1..=98).contains(&n) && action == n.to_string() { return Ok(()); }
                }
            }
            if let Some(menu) = text.strip_prefix("mr ") {
                let tokens: Vec<&str> = menu.split(' ').collect();
                if tokens.len() == 3 && tokens[0] == self.server_id.to_string()
                    && tokens[1].parse::<u8>().is_ok_and(|n| n <= 31 && tokens[1] == n.to_string())
                    && (1..=63).contains(&tokens[2].len()) && tokens[2].bytes().all(|c| c.is_ascii_alphanumeric() || c == b'_') {
                    return Ok(());
                }
            }
        }
        Err("unsupported or missing reliable client command".into())
    }

    pub fn receive(&mut self, packet: &[u8], reply: bool) -> Result<Vec<Vec<u8>>> {
        if packet.starts_with(&[255;4]) { return Ok(self.oob(&packet[4..])?.into_iter().collect()); }
        if self.stats.profile.is_none() { return Err("valid stats required before gamestate".into()); }
        if packet.len() < 14 { return Err("truncated client netchan packet".into()); }
        let sequence = u32::from_le_bytes(packet[..4].try_into().unwrap());
        let server_id = packet[4];
        let ack = u32::from_le_bytes(packet[5..9].try_into().unwrap());
        let reliable_ack = u32::from_le_bytes(packet[9..13].try_into().unwrap());
        let initial_epoch = server_id == 0 && ack == 0 && reliable_ack == 0 && ["connected","primed"].contains(&self.phase.as_str());
        if sequence == 0 || sequence >= 0x20000000 || (server_id != 255 && server_id != self.server_id && !initial_epoch) {
            return Err("invalid client sequence or server id".into());
        }
        if ack > self.sent || reliable_ack > self.published_command || !self.server_commands.contains_key(&reliable_ack) {
            return Err("client acknowledged an unsent message".into());
        }
        let base = self.input_bases.get(&ack).ok_or_else(|| format!("expired input base: acknowledged={ack}, sent={}",self.sent))?;
        if sequence <= self.received { return Ok(Vec::new()); }
        let server_command = &self.server_commands[&reliable_ack];
        let mut key = (self.challenge ^ server_id as u32 ^ ack) as u8;
        let body: Vec<u8> = packet[13..].iter().enumerate().map(|(i,&b)| {
            if !server_command.is_empty() { key ^= server_command[i % server_command.len()].wrapping_shl((i & 1) as u32); }
            b ^ key
        }).collect();
        let mut reader = Reader::new(&body);
        let mut reliable = self.reliable;
        let mut command = self.command.clone();
        let mut commands = Vec::new();
        loop {
            match reader.bits(3)? {
                3 => break,
                2 => {
                    let number = reader.number(4)?;
                    let candidate = reader.string()?;
                    if number > reliable {
                        if reliable.checked_add(1) != Some(number) { return Err("unsupported or missing reliable client command".into()); }
                        self.validate_reliable(candidate)?;
                        reliable = number;
                        command = candidate.to_vec();
                    }
                }
                0 | 1 if commands.is_empty() => {
                    commands = read_move(&mut reader,usercmd_key(ack,self.checksum_feed,server_command),base)?;
                }
                _ => return Err("unsupported client message".into()),
            }
        }
        if reader.cursor != body.len() { return Err("trailing client message bytes".into()); }
        self.received = sequence;
        self.reliable = reliable;
        self.command = command;
        self.message_ack = self.message_ack.max(ack);
        self.server_ack = self.server_ack.max(reliable_ack);
        let oldest = self.server_ack.saturating_sub(32);
        self.server_commands.retain(|&n,_| n >= oldest);
        self.pending_commands = commands;
        if self.phase == "connected" || ack == 0 {
            self.phase = "primed".into();
            return self.send(&self.gamestate.clone(),None);
        }
        if reply { self.send(b"\x06",None) } else { Ok(Vec::new()) }
    }
}
