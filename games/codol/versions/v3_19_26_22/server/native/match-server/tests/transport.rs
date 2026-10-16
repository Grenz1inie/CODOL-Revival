use codol_match319::{NuketownRoom, transport::{Session, StatsUpload}};
use std::net::SocketAddr;

const OWNER: u64 = 1_000_001;
const CHALLENGE: u32 = 123456;
const CHUNK: usize = 0x4d6;
fn peer(port: u16) -> SocketAddr { ([127, 0, 0, 1], port).into() }
fn oob(text: &str) -> Vec<u8> { [b"\xff\xff\xff\xff", text.as_bytes(), b"\0"].concat() }
fn connect(uid: u64, challenge: u32) -> Vec<u8> {
    oob(&format!("connect {uid:016x} \"\\challenge\\{challenge}\\qport\\123\\protocol\\1\""))
}
fn session() -> Session { Session::new(NuketownRoom::new(OWNER, "Player").unwrap(), CHALLENGE) }
fn stats(index: u8, length: u16, data: &[u8]) -> Vec<u8> {
    [b"\xff\xff\xff\xffstats\0".as_slice(), &[index], &length.to_le_bytes(), data].concat()
}

#[test]
fn challenge_and_identity_gate_the_same_peer_connection() {
    let mut host = session();
    assert!(host.handle(peer(1), &connect(OWNER, CHALLENGE)).is_none());
    assert!(host.handle(peer(1), &oob("getchallenge invalid")).is_none());
    assert_eq!(host.handle(peer(1), &oob("getchallenge 0 \"test319\"")),
               Some(oob("challengeResponse 123456")));
    for (sender, packet) in [(peer(2), connect(OWNER, CHALLENGE)),
                            (peer(1), connect(OWNER + 1, CHALLENGE)),
                            (peer(1), connect(OWNER, CHALLENGE + 1))] {
        assert!(host.handle(sender, &packet).is_none());
    }
    assert_eq!(host.handle(peer(1), &connect(OWNER, CHALLENGE)),
        Some(oob("connectResponse \\mapname\\mp_nuked\\gametype\\cha\\sv_maxclients\\18\\protocol\\1")));
    assert_eq!(host.room().players().len(), 18);
    assert!(host.profile().is_none());
}

#[test]
fn raw_profile_reassembles_out_of_order_without_duplicate_loss() {
    let profile: Vec<u8> = (0..32768).map(|i| (i % 251) as u8).collect();
    let mut upload = StatsUpload::new(0).unwrap();
    let chunks: Vec<_> = profile.chunks(CHUNK).collect();
    for i in (1..chunks.len()).rev() {
        let missing = upload.accept(i as u8, 0, chunks[i]).unwrap();
        assert_eq!(missing & (1 << i), 0);
        assert_eq!(missing & 1, 1);
        assert!(upload.profile().is_none());
        assert_eq!(upload.accept(i as u8, 0, chunks[i]).unwrap(), missing);
    }
    assert_eq!(upload.accept(0, 0, chunks[0]).unwrap(), 0);
    assert_eq!(upload.profile(), Some(profile.as_slice()));
}

#[test]
fn local_proxy_connects_directly_with_zero_challenge_and_no_protocol_field() {
    // Existing 3.19 proxy route, observed raw connect datagram; no getchallenge precedes it.
    let mut host = Session::new(NuketownRoom::new(OWNER, "Player").unwrap(), 0);
    let packet = oob(&format!("connect {OWNER:016x} \"\\name\\UGxheWVy\\xuid\\{OWNER:016x}\\challenge\\0\\statver\\233 1248641861\""));
    assert_eq!(host.handle(peer(1), &packet),
        Some(oob("connectResponse \\mapname\\mp_nuked\\gametype\\cha\\sv_maxclients\\18\\protocol\\1")));
    assert!(host.handle(peer(2), &packet).is_none());
    assert_eq!(host.handle(peer(1), &stats(0, 0, &[0; CHUNK])), Some(oob("statResponse 134217726")));
}

#[test]
fn stats_reject_bad_lengths_indices_and_conflicting_duplicates() {
    assert!(StatsUpload::new(32769).is_err());
    let mut upload = StatsUpload::new(0).unwrap();
    assert!(upload.accept(27, 0, &[0; CHUNK]).is_err());
    assert!(upload.accept(0, 0, &[0; CHUNK - 1]).is_err());
    assert!(upload.accept(0, 100, &[0; CHUNK]).is_err());
    upload.accept(0, 0, &[0; CHUNK]).unwrap();
    assert!(upload.accept(0, 0, &[1; CHUNK]).is_err());
    assert!(upload.profile().is_none());
}

#[test]
fn zlib_requires_exact_output_and_a_complete_stream() {
    // Python zlib fixture; expected uncompressed bytes are independent of Rust's decoder.
    let wire = include_bytes!("fixtures/stats-zlib.bin");
    let mut upload = StatsUpload::new(wire.len() as u16).unwrap();
    assert_eq!(upload.accept(0, wire.len() as u16, wire).unwrap(), 0);
    let expected: Vec<u8> = (0..32768).map(|i| (i % 251) as u8).collect();
    assert_eq!(upload.profile(), Some(expected.as_slice()));
    let mut corrupt = wire.to_vec();
    corrupt[wire.len() - 1] ^= 1;
    let mut trailing = wire.to_vec(); trailing.push(0);
    for invalid in [wire[..wire.len() - 1].to_vec(), corrupt, trailing,
                    include_bytes!("fixtures/stats-short-zlib.bin").to_vec(),
                    include_bytes!("fixtures/stats-long-zlib.bin").to_vec()] {
        let mut upload = StatsUpload::new(invalid.len() as u16).unwrap();
        assert!(upload.accept(0, invalid.len() as u16, &invalid).is_err());
        assert!(upload.profile().is_none());
    }
}

#[test]
fn upload_belongs_to_connected_peer_and_retransmitted_connect_keeps_progress() {
    let mut host = session();
    let first = stats(0, 0, &[0; CHUNK]);
    assert!(host.handle(peer(1), &first).is_none());
    host.handle(peer(1), &oob("getchallenge 0 \"test319\""));
    host.handle(peer(1), &connect(OWNER, CHALLENGE));
    assert!(host.handle(peer(2), &first).is_none());
    assert_eq!(host.handle(peer(1), &first), Some(oob("statResponse 134217726")));
    host.handle(peer(1), &connect(OWNER, CHALLENGE));
    for index in 1..27 {
        let size = CHUNK.min(32768 - index * CHUNK);
        let reply = host.handle(peer(1), &stats(index as u8, 0, &vec![0; size]));
        if index == 26 { assert_eq!(reply, Some(oob("statResponse 0"))); }
    }
    assert_eq!(host.profile(), Some([0; 32768].as_slice()));
    host.handle(peer(1), &oob("disconnect"));
    assert!(host.profile().is_none());
    assert!(host.handle(peer(1), &first).is_none());
}

#[test]
fn malformed_upload_resets_the_native_fragment_mask_without_accepting_profile() {
    let mut host = session();
    host.handle(peer(1), &oob("getchallenge 0 \"test319\""));
    host.handle(peer(1), &connect(OWNER, CHALLENGE));
    assert_eq!(host.handle(peer(1), b"\xff\xff\xff\xffstats\0"),
               Some(oob("statResponse 134217727")));
    assert!(host.profile().is_none());
    assert_eq!(host.handle(peer(1), &stats(0, 0, &[0; CHUNK])),
               Some(oob("statResponse 134217726")));
}
