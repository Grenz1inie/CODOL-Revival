use codol_match::protocol;
use protocol::Association;

fn hex(value: &str) -> Vec<u8> {
    value.as_bytes().chunks_exact(2).map(|p| {
        u8::from_str_radix(std::str::from_utf8(p).unwrap(), 16).unwrap()
    }).collect()
}

#[test]
fn data_matches_current_native_writer_and_rejects_tamper_without_consuming_counter() {
    // Literal from ClientTransport423 / shipped 0xa7f960, not this Rust codec.
    let packet = hex("0602c9020100c8877aba5f5fecd41a005d84efd50585ce312e7639b0579ad2bdf57463756526d11578b4");
    let plain = b"\xff\xff\xff\xffchallengeResponse 1234";
    let mut a = Association::new(*b"12345678", [0; 16], "127.0.0.1:42000".parse().unwrap()).unwrap();
    assert!(a.encrypt(plain).is_err());
    assert!(a.handshake(&[]).is_err());
    a.key = Some(std::array::from_fn(|i| i as u8));
    a.local_tag = 713;
    a.remote_tag = 713;
    assert_eq!(a.encrypt(plain).unwrap(), packet);
    for offset in [2, 6, 14, 16] {
        let mut bad = packet.clone();
        bad[offset] ^= 1;
        assert!(a.decrypt(&bad).is_err());
        assert_eq!(a.received, 0);
    }
    assert_eq!(a.decrypt(&packet).unwrap(), plain);
    assert!(a.decrypt(&packet).is_err());
}

#[test]
fn init_is_idempotent_and_invalid_cookie_does_not_open_data() {
    let mut a = Association::new(*b"12345678", [0; 16], "127.0.0.1:42000".parse().unwrap()).unwrap();
    let init = [b"\x01\x02\0\0\0\0\x01\0".as_slice(), b"12345678"].concat();
    let ack = a.handshake(&init).unwrap();
    assert_eq!(ack.len(), 38);
    assert_eq!(&ack[24..], b"\x7f\0\0\x01\x10\xa4".iter().chain(b"12345678").copied().collect::<Vec<_>>());
    assert_eq!(a.handshake(&init).unwrap(), ack);
    let mut cookie = vec![3, 2];
    cookie.extend_from_slice(&a.local_tag.to_le_bytes());
    cookie.extend_from_slice(&[0, 0]);
    cookie.extend_from_slice(&ack);
    cookie.extend_from_slice(&[0; 37]);
    cookie.extend_from_slice(b"12345678");
    cookie.extend_from_slice(&[0; 100]);
    assert!(a.handshake(&cookie).is_err());
    assert!(a.key.is_none());
    assert!(Association::new(*b"12345678", [0; 16], "127.0.0.2:1".parse().unwrap()).is_err());
}

#[test]
fn p224_cookie_uses_current_sha1_shared_x_and_retries_keep_data_counters() {
    use sha1::{Digest,Sha1};
    let security = std::array::from_fn(|i| i as u8);
    let mut a = Association::new(*b"12345678",security,"127.0.0.1:42000".parse().unwrap()).unwrap();
    let init = [b"\x01\x02\0\0\0\0\xc9\x02".as_slice(),b"12345678"].concat();
    let ack = a.handshake(&init).unwrap();
    // P-224 public key for private scalar 1, from Python cryptography.
    let public = hex("30450302070002011c021d00b70e0cbd6bb4bf7f321390b94a03c1d356c21122343280d6115c1d21021d00bd376388b5f723fb4c22dfe6cd4375a05a07476444d5819985007e340000000000000000000000000000000000000000000000000000000000");
    let mut echo = vec![3,2];
    echo.extend_from_slice(&a.local_tag.to_le_bytes());
    echo.extend_from_slice(&[0,0]);
    echo.extend_from_slice(&ack);
    echo.extend_from_slice(&[0;37]);
    echo.extend_from_slice(b"12345678");
    echo.extend_from_slice(&public);
    let mut invalid = echo[..89].to_vec();
    let mut off_curve = vec![0x30,67,3,2,7,0,2,1,28,2,28];
    off_curve.extend_from_slice(&[0;28]);
    off_curve.extend_from_slice(&[2,28]);
    off_curve.extend_from_slice(&[0;28]);
    off_curve.resize(100,0); // Well-formed DER; (0,0) is not a P-224 point.
    invalid.extend(off_curve);
    assert!(a.handshake(&invalid).is_err());
    assert!(a.key.is_none());
    let cookie = a.handshake(&echo).unwrap();
    assert_eq!(cookie.len(),114);
    let size = cookie[16] as usize;
    let x = &cookie[17+size-28..17+size];
    // scalar 1 * server public point has the same X, independently of backend.
    let expected: [u8;20] = Sha1::digest([x,security.as_slice()].concat()).into();
    assert_eq!(a.key,Some(expected));
    a.encrypt(b"first").unwrap();
    assert_eq!(a.handshake(&init).unwrap(),ack);
    assert_eq!(a.handshake(&echo).unwrap(),cookie);
    assert_eq!(a.sent,1);
    let mut changed = echo;
    changed[44] ^= 1;
    assert!(a.handshake(&changed).is_err());
}

#[test]
fn nat_intro_and_native_data_rollover_keep_existing_boundaries() {
    let mut intro = vec![13,2,0];
    intro.extend(0..26);
    let reply = protocol::nat_reply(&intro).unwrap();
    assert_eq!(reply[0],12);
    assert_eq!(&reply[1..],&intro[1..]);
    assert!(protocol::nat_reply(&intro[..28]).is_none());
    let mut a = Association::new(*b"12345678",[0;16],"127.0.0.1:42000".parse().unwrap()).unwrap();
    a.key = Some(std::array::from_fn(|i| i as u8));
    a.local_tag = 713;
    for (counter,wire) in [(65534,"0602c902feff0b01b0e28062e70105000b7f2ab66c"),
        (65535,"0602c902ffffdecff2b20e66f5800500e4823ef299"),
        (65536,"0602c90200002aa01a814e3d9aa7050054df864d96"),
        (65537,"0602c9020100c43ae113d84ef1710500f581d6e812")] {
        assert_eq!(a.decrypt(&hex(wire)).unwrap(),b"valid");
        assert_eq!(a.received,counter);
        assert!(a.decrypt(&hex(wire)).is_err());
    }
}

#[test]
fn native_usercmd_vectors_preserve_bit_pools_and_reject_truncation() {
    use protocol::input::{decode_move, decode_usercmd};
    for (key, vector) in [
        (0, "8ee8030000e883d50722c00baa7ffdf7ff6817e120e843c50b16"),
        (1, "80e8030000e983d70722400bae5ffdf6bf6916e021e943450b16"),
        (0xfedcba98, "8ee80300007039e5729bfd47cb75ae6ffff08f79b870f9e34717"),
    ] {
        let wire = hex(vector);
        let decoded = decode_usercmd(&wire, key, None).unwrap();
        for (name, expected) in [("time",1000),("buttons",0x220005),("weapon",1023),
            ("offhand",2),("alt",3),("roll",32768),("melee_yaw",16384),
            ("melee_dist",255),("melee_target",2047),("location_x",31),
            ("location_y",128),("location_angle",255),("remote_x",9),("remote_y",200)] {
            assert_eq!(decoded[name], expected, "{key} {name}");
        }
        assert!(decode_usercmd(&wire[..wire.len()-1], key, None).is_err());
    }
    let wire = hex("0101e80300001ab1a7000000000000000000000000e80300000000000003");
    let commands = decode_move(&wire, 55, None).unwrap();
    assert_eq!(commands.len(), 1);
    assert_eq!(commands[0]["weapon"], 7);
    assert_eq!(commands[0]["time"], 1000);
    assert!(decode_move(&wire[..wire.len()-1],55,None).is_err());
}

#[test]
fn packet_and_configstring_writers_keep_python_wire_contract() {
    use protocol::wire::{encode_configstrings, encode_packets};
    assert_eq!(encode_packets(b"\x06", 2, 1, 42, b"s").unwrap()[0], hex("02000000010000005d"));
    let config = encode_configstrings(&[(0,"\\mapname\\mp_nuked".into()),(6415,"0 0 1 1".into())],
        &[(25,7)], &[(26,7,2,3,vec![4,5])]).unwrap();
    assert_eq!(config, hex("02003d5c6d61706e616d655c6d705f6e756b656400e430203020312031000064800302a0010e1038400880020006"));
    assert!(encode_configstrings(&[(24,"bad".into())], &[], &[]).is_err());
    assert!(encode_configstrings(&[(0,"bad%".into())], &[], &[]).is_err());
    assert!(encode_configstrings(&[(0,"ok".into())], &[(0,7)], &[]).is_err());
    let full = encode_packets(&vec![6; 1150], 1, 0, 0, b"").unwrap();
    assert_eq!(full.len(), 1);
    assert_eq!(&full[0][..10], &[1,0,0,128,0,0,130,4,130,4]);
    let fragments = encode_packets(&vec![6; 1151], 1, 0, 0, b"").unwrap();
    assert_eq!(fragments.len(), 2);
    assert_eq!(&fragments[0][..10], &[1,0,0,128,0,1,130,4,130,4]);
    assert_eq!(&fragments[1][..10], &[1,0,0,128,1,1,130,4,1,0]);
}

#[test]
fn world_snapshot_has_drawable_flags_and_matches_python_inventory_wire() {
    use protocol::{Fields, Inventory, encode_snapshot};
    use protocol::wire::encode_baseline;
    let fields = Fields::new();
    let baseline = encode_baseline(&fields,0).unwrap();
    assert_eq!(baseline,hex("0000000000000846a0000000004600000000ec00000000000000000000000000000000020000000000f87f0006"));
    let inventory = Inventory { weapon:7, ammo_type:4, clip_type:6, clip:30, reserve:120, raised:false };
    let wire = encode_snapshot(&fields,1000,100,Some(&inventory),1,&[],&[],[0;3]).unwrap();
    assert_eq!(wire,hex("00e8030000000046a0000000004600000000ec00000000000000000000000000000000ee00000000640064000160400ffc0000000402f00000fc3f06"));
    assert_eq!(baseline[6],8);
    assert_eq!(wire[6],0);
    assert!(encode_snapshot(&fields,0,32768,None,0,&[],&[],[0;3]).is_err());
    assert!(encode_snapshot(&fields,0,100,None,0,&[(1,Fields::new()),(1,Fields::new())],&[],[0;3]).is_err());
    let invalid = Fields::from([(235,0)]);
    assert!(encode_snapshot(&invalid,0,100,None,0,&[],&[],[0;3]).is_err());
}

#[test]
fn sparse_player_delta_and_two_player_snapshot_match_existing_python_reader_case() {
    use protocol::{Fields,Inventory,encode_snapshot};
    use protocol::wire::encode_playerstate;
    use sha2::{Digest,Sha256};
    let word = |v: f32| v.to_bits() as u64;
    let old = Fields::from([(0,900),(18,word(45.)),(19,word(-10.)),(39,7)]);
    let next = Fields::from([(0,1000),(18,word(60.)),(19,word(-20.)),(39,7)]);
    assert_eq!(encode_playerstate(&next,1000,Some(&old)).unwrap(),
        hex("2936e80300008d0000000000000000d8000000000000000000000000000000001500000000ab2a01c7f10006"));
    // Same state as test_match_snapshot.py's existing native two-player reader case.
    let player = Fields::from([(0,1000),(8,word(100.)),(10,word(25.)),(11,word(-50.)),(39,7),(83,0)]);
    let entities = [(0,Fields::from([(24,word(100.)),(28,word(-50.)),(32,word(25.))])),
        (1,Fields::from([(24,word(200.)),(28,word(80.)),(32,word(25.))]))];
    let clients = [(0,Fields::from([(20,5)])),(1,Fields::from([(20,6)]))];
    let inventory = Inventory { weapon:7,ammo_type:1,clip_type:1,clip:30,reserve:90,raised:false };
    let wire = encode_snapshot(&player,1000,100,Some(&inventory),0,&entities,&clients,[0;3]).unwrap();
    assert_eq!(wire.len(),292);
    assert_eq!(&Sha256::digest(&wire)[..],hex("d096b4f1719b4417113fd9bfa2eb5220103790f19d88d26959c36d54ec8b3cd1"));
}

fn stats_fragments(source: &[u8], compressed: bool) -> Vec<Vec<u8>> {
    source.chunks(1238).enumerate().map(|(i, data)| {
        let mut packet = vec![i as u8];
        packet.extend_from_slice(&(if compressed { source.len() as u16 } else { 0 }).to_le_bytes());
        packet.extend_from_slice(data);
        packet
    }).collect()
}

#[test]
fn stats_requires_exact_stream_and_final_size_and_keeps_previous_fragments() {
    use protocol::connection::StatsTransfer;
    use flate2::{write::ZlibEncoder, Compression};
    use std::io::Write;
    let profile = vec![0x42;32768]; // No lobby CRC requirement on match upload.
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(&profile).unwrap();
    let compressed = encoder.finish().unwrap();
    for source in [&compressed[..], &[compressed.as_slice(), b"tail"].concat()[..]] {
        let mut transfer = StatsTransfer::new();
        let mut result = Ok(0);
        for packet in stats_fragments(source,true) { result = transfer.accept(&packet); }
        if source.len() == compressed.len() {
            assert_eq!(result.unwrap(),0);
            assert_eq!(transfer.profile.as_deref(),Some(profile.as_slice()));
        } else {
            assert!(result.is_err());
            assert!(transfer.profile.is_none());
        }
    }
    for size in [32767,32769] {
        let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
        encoder.write_all(&vec![0x42;size]).unwrap();
        let mut transfer = StatsTransfer::new();
        let packets = stats_fragments(&encoder.finish().unwrap(),true);
        assert_eq!(packets.len(),1);
        assert!(transfer.accept(&packets[0]).is_err());
        assert!(transfer.profile.is_none());
        assert!(transfer.fragments.is_empty());
    }
    let mut transfer = StatsTransfer::new();
    let fragments = stats_fragments(&profile,false);
    let remaining = transfer.accept(&fragments[0]).unwrap();
    let mut changed = fragments[0].clone();
    changed[3] ^= 1;
    assert!(transfer.accept(&changed).is_err());
    assert_eq!(transfer.accept(&fragments[0]).unwrap(),remaining);
    let last = fragments.last().unwrap();
    assert!(transfer.accept(&last[..last.len()-1]).is_err());
    for packet in fragments.iter().skip(1).rev() { transfer.accept(packet).unwrap(); }
    assert_eq!(transfer.profile.as_deref(),Some(profile.as_slice()));
}

fn client_packet(c: &protocol::Connection, body: &[u8], sequence: u32, ack: u32, reliable_ack: u32) -> Vec<u8> {
    let mut packet = sequence.to_le_bytes().to_vec();
    packet.push(c.server_id);
    packet.extend_from_slice(&ack.to_le_bytes());
    packet.extend_from_slice(&reliable_ack.to_le_bytes());
    let mut key = (c.challenge ^ c.server_id as u32 ^ ack) as u8;
    let command = &c.server_commands[&reliable_ack];
    for (i,&byte) in body.iter().enumerate() {
        if !command.is_empty() { key ^= command[i % command.len()].wrapping_shl((i & 1) as u32); }
        packet.push(byte ^ key);
    }
    packet
}

fn connected() -> protocol::Connection {
    let mut c = protocol::Connection::new(1,&serde_json::json!({"netconst_checksum":0x11223344,"map_name":"mp_nuked"})).unwrap();
    let request = format!("connect 0000000000000001 \"\\xuid\\0000000000000001\\challenge\\{}\"\0",c.challenge);
    let mut packet = vec![255;4];
    packet.extend_from_slice(request.as_bytes());
    c.receive(&packet,true).unwrap();
    for fragment in stats_fragments(&vec![0;32768],false) {
        let packet = [b"\xff\xff\xff\xffstats\0".as_slice(),fragment.as_slice()].concat();
        c.receive(&packet,true).unwrap();
    }
    c.receive(&client_packet(&c,b"\x03",1,0,0),false).unwrap();
    c
}

#[test]
fn connection_reliable_errors_are_atomic_and_ack_retains_snapshot_base() {
    use protocol::Fields;
    let mut c = connected();
    c.server_id = 17;
    c.checksum_feed = 54; // Native writer key 55 at acknowledged message 1.
    assert_eq!(c.phase,"primed");
    c.receive(b"\xff\xff\xff\xffgamestateupdate 6",false).unwrap();
    assert_eq!(c.loading_status,6);
    let before = (c.received,c.reliable,c.message_ack);
    // Shipped writer: menu reply 1, score poll 2, then a real move in one pool.
    let body = hex("52010000006d72203137203020636c617373000200000073008001e803000046ece9000000000000000000000000e80300000000000000");
    let mut bad = body.clone();
    bad.push(0); // A valid reliable must not be committed before the trailing check.
    assert!(c.receive(&client_packet(&c,&bad,2,1,0),false).is_err());
    assert_eq!((c.received,c.reliable,c.message_ack),before);
    c.receive(&client_packet(&c,&body,2,1,0),false).unwrap();
    assert_eq!(c.reliable,2);
    assert_eq!(c.pending_commands[0]["weapon"],7);
    assert_eq!(c.pending_commands[0]["buttons"],1);
    let fields = Fields::from([(39,5)]);
    assert_eq!(c.send(b"\x06",Some(&fields)).unwrap().len(),2);
    assert!(c.world_baseline_sent);
    let ack = c.sent;
    c.receive(&client_packet(&c,b"\x03",3,ack,0),false).unwrap();
    for _ in 0..80 { c.send(b"\x06",Some(&Fields::from([(39,7)]))).unwrap(); }
    assert_eq!(c.input_bases[&ack]["weapon"],5);
    c.receive(&client_packet(&c,b"\x03",4,c.sent,0),false).unwrap();
    c.send(b"\x06",None).unwrap();
    assert!(c.receive(&client_packet(&c,b"\x03",5,ack,0),false).unwrap_err().contains("expired input base"));
}
