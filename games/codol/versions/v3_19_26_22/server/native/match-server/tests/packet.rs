use codol_match319::transport::{server_packet, StatsUpload};
use serde_json::{Value, json};
use std::process::{Command, Stdio};

fn native(input: Value) -> Option<Value> {
    let Ok(python) = std::env::var("CODOL319_NATIVE_PYTHON") else {
        eprintln!("native replay not requested; set CODOL319_NATIVE_PYTHON with local snapshots");
        return None;
    };
    let mut child = Command::new(python).args(["-B", "../../../tests/client_transport319.py"])
        .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn().unwrap();
    serde_json::to_writer(child.stdin.take().unwrap(), &input).unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
    Some(serde_json::from_slice(&output.stdout).unwrap())
}

#[test]
fn native_reader_decodes_server_packets_with_reliable_command_wrap() {
    let plain: Vec<u8> = (0..1024).map(|i| i as u8).collect();
    let mut cases = Vec::new();
    for command in [b"".as_slice(), b"gamestateupdate 6", b"abc", b"x\x80\xff"] {
        let packet = server_packet(&plain, 1234, 519, 123456, command).unwrap();
        assert_eq!(&packet[..8], &[210, 4, 0, 0, 7, 2, 0, 0]);
        cases.push(json!({"packet": packet, "plain": plain, "command": command, "challenge": 123456}));
    }
    if let Some(result) = native(json!(cases)) { assert_eq!(result["decoded"], 4); }
}

#[test]
fn packet_rejects_unsupported_fragment_flags_and_lengths() {
    for (payload, seq, ack) in [(vec![], 1, 0), (vec![0; 1025], 1, 0),
                               (vec![5], 0, 0), (vec![5], 0x20000000, 0),
                               (vec![5], 1, 0x80000000)] {
        assert!(server_packet(&payload, seq, ack, 0, b"").is_err());
    }
}

#[test]
fn native_stats_writer_uploads_raw_and_compressed_profiles() {
    let Some(result) = native(json!("stats")) else { return; };
    let cases: Vec<Vec<Vec<u8>>> = serde_json::from_value(result).unwrap();
    for frames in cases {
        let length = u16::from_le_bytes([frames[0][1], frames[0][2]]);
        let mut upload = StatsUpload::new(length).unwrap();
        for frame in frames { upload.accept(frame[0], length, &frame[3..]).unwrap(); }
        let expected: Vec<u8> = (0..32768).map(|i| (i % 251) as u8).collect();
        assert_eq!(upload.profile(), Some(expected.as_slice()));
    }
}
