use codol_match319::{NuketownRoom, transport::Session};
use std::net::SocketAddr;

fn connected() -> (Session, SocketAddr) {
    let mut session = Session::new(NuketownRoom::new(1000001, "Player").unwrap(), 0);
    let peer = "127.0.0.1:31999".parse().unwrap();
    session.handle(peer, b"\xff\xff\xff\xffconnect 00000000000f4241 \"\\challenge\\0\"").unwrap();
    (session, peer)
}

fn upload(session: &mut Session, peer: SocketAddr) {
    let wire = include_bytes!("fixtures/stats-zlib.bin");
    let packet = [b"\xff\xff\xff\xffstats\0\0".as_slice(), &(wire.len() as u16).to_le_bytes(), wire].concat();
    assert_eq!(session.handle(peer, &packet).unwrap(), b"\xff\xff\xff\xffstatResponse 0\0");
}

fn client(sequence: u32, ack: u32) -> Vec<u8> {
    // Native 0x5b2c90 header and three-bit EOF; no reliable server command yet.
    [sequence.to_le_bytes().as_slice(), &[0], &ack.to_le_bytes(), &0u32.to_le_bytes(),
        &[3 ^ ack as u8]].concat()
}

#[test]
fn map_waits_for_same_peer_stats_and_current_resource_capture() {
    let (mut session, peer) = connected();
    let other = "127.0.0.1:32000".parse().unwrap();
    assert!(session.handle(peer, &client(1, 0)).is_none());
    upload(&mut session, peer);
    for sequence in 1..=3 {
        let packet = session.handle(peer, &client(sequence, sequence - 1)).unwrap();
        assert_eq!(packet, [sequence.to_le_bytes().as_slice(), &[0; 4], &[5 ^ sequence as u8]].concat());
    }
    assert!(session.handle(peer, &client(4, 3)).is_none());
    let state = [3, 0, 0, 0, 0, b'm', 0, b'c', 0, 1, 2, 3, 4, 4, 0, 0, 0, 5];
    session.set_gamestate(state.to_vec()).unwrap();
    assert!(session.handle(other, &client(5, 3)).is_none());
    let first = session.handle(peer, &client(5, 3)).unwrap();
    assert_eq!(&first[..8], &[4, 0, 0, 0, 0, 0, 0, 0]);
    assert_eq!(first[8..].iter().map(|b| b ^ 4).collect::<Vec<_>>(), state);
    assert_eq!(session.handle(peer, &client(6, 3)).unwrap(), first, "Lost gamestate retransmits the same sequence");
    assert!(session.handle(peer, &client(6, 4)).is_none(), "Duplicate client sequence ignored");
    assert!(session.handle(peer, &client(7, 4)).is_none(), "Acknowledged gamestate must not load twice");
    assert!(!session.map_loaded());
    session.handle(other, b"\xff\xff\xff\xffgamestateupdate 6");
    assert!(!session.map_loaded());
    session.handle(peer, b"\xff\xff\xff\xffgamestateupdate 6");
    assert!(session.map_loaded());
    session.handle(peer, b"\xff\xff\xff\xffdisconnect");
    assert!(!session.map_loaded());
}

#[test]
fn malformed_or_unnegotiated_packets_never_load_a_map() {
    let (mut session, peer) = connected();
    session.handle(peer, b"\xff\xff\xff\xffgamestateupdate 6");
    assert!(!session.map_loaded());
    upload(&mut session, peer);
    for packet in [vec![], vec![0; 13], client(0, 0), client(0x20000001, 0), client(1, 0x80000000)] {
        assert!(session.handle(peer, &packet).is_none());
    }
    for payload in [vec![], vec![5], vec![3; 1025]] {
        assert!(session.set_gamestate(payload).is_err());
    }
}

#[test]
fn render_frames_wait_for_loaded_map_and_spawn_and_keep_the_first_baseline_until_ack() {
    let (mut session, peer) = connected();
    assert!(session.tick(0).is_none());
    upload(&mut session, peer);
    session.set_gamestate(vec![3, 0, 0, 0, 0, b'm', 0, b'c', 0, 1, 2, 3, 4, 5]).unwrap();
    for seq in 1..=4 { session.handle(peer, &client(seq, seq-1)); }
    assert!(session.tick(1).is_none());
    session.handle(peer, b"\xff\xff\xff\xffgamestateupdate 6");
    assert!(session.tick(2).is_none(), "No guessed spawn before resource export");
    session.set_spawn([100.0, -200.0, 300.0], 90.0).unwrap();
    let (target, baseline) = session.tick(10).unwrap();
    assert_eq!(target, peer);
    assert_eq!(&baseline[..8], &[5,0,0,0,0,0,0,0]);
    let plain: Vec<_> = baseline[8..].iter().map(|b| b ^ 5).collect();
    assert_eq!(&plain[5..7], &[0, 8]);
    assert!(session.tick(59).is_none());
    assert_eq!(session.tick(60).unwrap().1, baseline);
    session.handle(peer, &client(5, 5));
    let next = session.tick(110).unwrap().1;
    let plain: Vec<_> = next[8..].iter().map(|b| b ^ 6).collect();
    assert_eq!(&plain[5..7], &[1, 0], "Native CG accepts a continuation, not flag 8");
    assert_eq!(u32::from_le_bytes(plain[1..5].try_into().unwrap()), 1100);
    session.handle(peer, b"\xff\xff\xff\xffgamestateupdate 6");
    assert_eq!(session.tick(160).unwrap().1[0], 7, "Duplicate load notice cannot reset baseline");
    session.handle(peer, b"\xff\xff\xff\xffdisconnect");
    assert!(session.tick(210).is_none());
}
