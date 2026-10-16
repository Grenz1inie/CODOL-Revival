//! Current bdDTLS: P-224, SHA-1, AES-128-CTR and length-authenticated DATA.
//! Port of src/match_server/transport.py; see its NOTICE.md for attribution.
//! SPDX-License-Identifier: AGPL-3.0-or-later

use super::Result;
use aes::Aes128;
use ctr::cipher::{KeyIvInit, StreamCipher};
use hmac::{Hmac, Mac};
use super::p224::KeyPair;
use rand::{rngs::OsRng, Rng};
use sha1::{Digest, Sha1};
use std::net::{IpAddr, Ipv4Addr, SocketAddr};

/// Handle bdNAT INTRO before association lookup; preserve its opaque MAC/endpoints.
pub fn nat_reply(packet: &[u8]) -> Option<Vec<u8>> {
    if packet.len() != 29 || packet[..3] != [13, 2, 0] {
        return None;
    }
    let mut reply = packet.to_vec();
    reply[0] = 12;
    Some(reply)
}

fn export_public(key: &KeyPair) -> Result<Vec<u8>> {
    let point = key.public()?;
    let mut body = vec![3, 2, 7, 0, 2, 1, 28];
    for raw in [&point[..28], &point[28..]] {
        let sign = raw[0] & 128 != 0;
        body.extend_from_slice(&[2, 28 + u8::from(sign)]);
        if sign { body.push(0); }
        body.extend_from_slice(raw);
    }
    let mut result = vec![48, body.len() as u8];
    result.extend(body);
    result.resize(100, 0);
    Ok(result)
}

fn import_public(data: &[u8]) -> Result<[u8;56]> {
    if data.len() != 100 || data[0] != 48 || !(13..=69).contains(&data[1])
        || data[2..9] != [3, 2, 7, 0, 2, 1, 28] {
        return Err("invalid P-224 public key header".into());
    }
    let end = data[1] as usize + 2;
    let mut cursor = 9;
    let mut coordinates = [0u8; 56];
    for coordinate in 0..2 {
        if cursor + 2 > end || data[cursor] != 2 {
            return Err("invalid P-224 coordinate".into());
        }
        let size = data[cursor + 1] as usize;
        cursor += 2;
        if !(1..=29).contains(&size) || cursor + size > end || data[cursor] & 128 != 0 {
            return Err("invalid P-224 coordinate size".into());
        }
        if size == 29 && (data[cursor] != 0 || data[cursor + 1] & 128 == 0) {
            return Err("invalid P-224 sign byte".into());
        }
        let raw = &data[cursor + usize::from(size == 29)..cursor + size];
        let finish = (coordinate + 1) * 28;
        coordinates[finish - raw.len()..finish].copy_from_slice(raw);
        cursor += size;
    }
    if cursor != end || data[end..].iter().any(|&b| b != 0) {
        return Err("invalid P-224 trailing data".into());
    }
    Ok(coordinates)
}

pub struct Association {
    pub sid: [u8; 8],
    pub security: [u8; 16],
    pub peer: SocketAddr,
    pub init: Option<Vec<u8>>,
    pub init_ack: Option<Vec<u8>>,
    pub echo: Option<Vec<u8>>,
    pub cookie_ack: Option<Vec<u8>>,
    private: Option<KeyPair>,
    pub key: Option<[u8; 20]>,
    pub local_tag: u16,
    pub remote_tag: u16,
    pub received: u32,
    pub sent: u32,
}

impl Association {
    pub fn new(security_id: [u8; 8], security_key: [u8; 16], peer: SocketAddr) -> Result<Self> {
        if peer.ip() != IpAddr::V4(Ipv4Addr::LOCALHOST) || peer.port() == 0 {
            return Err("only a loopback peer is supported".into());
        }
        Ok(Self { sid: security_id, security: security_key, peer, init: None, init_ack: None,
            echo: None, cookie_ack: None, private: None, key: None,
            local_tag: 0, remote_tag: 0, received: 0, sent: 0 })
    }

    pub fn handshake(&mut self, packet: &[u8]) -> Result<Vec<u8>> {
        if packet.len() == 16 && packet[..6] == [1, 2, 0, 0, 0, 0] {
            let tag = u16::from_le_bytes([packet[6], packet[7]]);
            if tag == 0 || packet[8..] != self.sid {
                return Err("invalid INIT reservation".into());
            }
            if self.init.as_deref() == Some(packet) {
                return Ok(self.init_ack.clone().unwrap());
            }
            let private = KeyPair::generate()?;
            let local_tag: u16 = OsRng.gen_range(1..=65535);
            let mut ack = vec![0; 38];
            ack[..4].copy_from_slice(&[2, 2, packet[6], packet[7]]);
            ack[14..16].copy_from_slice(&local_tag.to_le_bytes());
            ack[16..18].copy_from_slice(&local_tag.to_le_bytes());
            ack[18..20].copy_from_slice(&tag.to_le_bytes());
            ack[24..28].copy_from_slice(&[127, 0, 0, 1]);
            ack[28..30].copy_from_slice(&self.peer.port().to_le_bytes());
            ack[30..].copy_from_slice(&self.sid);
            self.private = Some(private);
            self.local_tag = local_tag;
            self.remote_tag = tag;
            self.init = Some(packet.to_vec());
            self.init_ack = Some(ack.clone());
            self.echo = None;
            self.cookie_ack = None;
            self.key = None;
            self.received = 0;
            self.sent = 0;
            return Ok(ack);
        }
        if packet.len() != 189 || self.init.is_none() {
            return Err("invalid handshake message".into());
        }
        if let Some(echo) = &self.echo {
            if packet != echo { return Err("COOKIE changed after establishment".into()); }
            return Ok(self.cookie_ack.clone().unwrap());
        }
        let tag = self.local_tag.to_le_bytes();
        if packet[..6] != [3, 2, tag[0], tag[1], 0, 0]
            || Some(&packet[6..44]) != self.init_ack.as_deref() || packet[81..89] != self.sid {
            return Err("invalid COOKIE echo".into());
        }
        let public = import_public(&packet[89..])?;
        let private = self.private.as_ref().ok_or("missing handshake private key")?;
        let shared = private.exchange(&public)?;
        let mut hash = Sha1::new();
        hash.update(shared);
        hash.update(self.security);
        let key: [u8; 20] = hash.finalize().into();
        let tag = self.remote_tag.to_le_bytes();
        let mut ack = vec![4, 2, tag[0], tag[1], 0, 0];
        ack.extend(export_public(private)?);
        ack.extend_from_slice(&self.sid);
        self.key = Some(key);
        self.private = None;
        self.echo = Some(packet.to_vec());
        self.cookie_ack = Some(ack.clone());
        Ok(ack)
    }

    fn crypt(&self, data: &[u8], counter: u32, tag: u16) -> Vec<u8> {
        let mut seed = [0; 6];
        seed[..4].copy_from_slice(&counter.to_le_bytes());
        seed[4..].copy_from_slice(&tag.to_le_bytes());
        let iv = Sha1::digest(seed);
        let mut cipher = ctr::Ctr128LE::<Aes128>::new_from_slices(
            &self.key.as_ref().unwrap()[..16], &iv[..16]).unwrap();
        let mut result = data.to_vec();
        cipher.apply_keystream(&mut result);
        result
    }

    pub fn encrypt(&mut self, plain: &[u8]) -> Result<Vec<u8>> {
        if self.key.is_none() || plain.len() > 65491 || self.sent == u32::MAX {
            return Err("DATA channel unavailable or payload too large".into());
        }
        let counter = self.sent + 1;
        let mut packet = vec![6, 2];
        packet.extend_from_slice(&self.remote_tag.to_le_bytes());
        packet.extend_from_slice(&(counter as u16).to_le_bytes());
        let mut body = (plain.len() as u16).to_le_bytes().to_vec();
        body.extend(self.crypt(plain, counter, self.remote_tag));
        let mut mac = Hmac::<Sha1>::new_from_slice(self.key.as_ref().unwrap()).unwrap();
        mac.update(&packet);
        mac.update(&body);
        packet.extend_from_slice(&mac.finalize().into_bytes()[..8]);
        packet.extend(body);
        self.sent = counter;
        Ok(packet)
    }

    pub fn decrypt(&mut self, packet: &[u8]) -> Result<Vec<u8>> {
        let tag = self.local_tag.to_le_bytes();
        if self.key.is_none() || packet.len() < 16 || packet[..4] != [6, 2, tag[0], tag[1]] {
            return Err("invalid DATA channel".into());
        }
        if u16::from_le_bytes([packet[14], packet[15]]) as usize != packet.len() - 16 {
            return Err("invalid DATA length".into());
        }
        let mut mac = Hmac::<Sha1>::new_from_slice(self.key.as_ref().unwrap()).unwrap();
        mac.update(&packet[..6]);
        mac.update(&packet[14..]);
        mac.verify_truncated_left(&packet[6..14]).map_err(|_| "invalid DATA authentication")?;
        let low = u16::from_le_bytes([packet[4], packet[5]]) as u64;
        let received = self.received as u64;
        let mut counter = (received & !65535) | low;
        if counter + 32768 < received { counter += 65536; }
        else if counter > received + 32768 && counter >= 65536 { counter -= 65536; }
        if counter <= received || counter > u32::MAX as u64 {
            return Err("replayed DATA record".into());
        }
        let plain = self.crypt(&packet[16..], counter as u32, self.local_tag);
        self.received = counter as u32;
        Ok(plain)
    }
}
