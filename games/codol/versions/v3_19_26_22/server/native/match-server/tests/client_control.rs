use codol_match319::transport::client_control;

fn wire(plain: &[u8]) -> Vec<u8> {
    let mut packet = vec![9, 0, 0, 0, 1, 4, 0, 0, 0, 0, 0, 0, 0];
    packet.extend(plain.iter().map(|b| b ^ 5));
    packet
}

#[test]
fn reliable_prefix_matches_native_decryption_of_real_loading_packet() {
    // PCAP room-ready-echo-live, seq 5; native 0x4709e0 replayed in Unicorn.
    let packet = "05000000010400000000000000cf04050505747164696e2b6d646925352535253525352535253505040544060505016c56b8050505050505050505050505050505050505050506";
    let bytes: Vec<u8> = (0..packet.len()).step_by(2).map(|i| u8::from_str_radix(&packet[i..i+2], 16).unwrap()).collect();
    let control = client_control(&bytes, 0).unwrap();
    assert_eq!((control.sequence, control.ack), (5, 4));
    assert_eq!(control.commands, vec![(1, b"qtalk.hal 0 0 0 0 0 0".to_vec())]);
}

#[test]
fn truncated_command_invalid_opcode_and_unimplemented_server_command_ack_are_rejected() {
    for plain in [vec![], vec![7], vec![2, 1, 0, 0], vec![2, 1, 0, 0, 0, b'x']] {
        assert!(client_control(&wire(&plain), 0).is_none());
    }
    let mut long = vec![2, 1, 0, 0, 0]; long.extend(vec![b'x'; 1024]); long.push(0);
    assert!(client_control(&wire(&long), 0).is_none());
    let mut packet = wire(&[3]); packet[9] = 1;
    assert!(client_control(&packet, 0).is_none());
}
