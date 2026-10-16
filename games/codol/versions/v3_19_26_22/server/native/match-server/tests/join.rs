use codol_match319::NuketownRoom;
use std::process::Command;

fn human() -> [u8; 0x1d0] {
    let mut row = [0; 0x1d0];
    row[0x94..0x98].copy_from_slice(&1000u32.to_le_bytes());
    row[0xac..0xb0].fill(0xff);
    row[0xb0] = 0xff;
    row[0x1b0] = 1;
    row
}

#[test]
fn bot_admission_uses_one_native_join_per_bot() {
    let room = NuketownRoom::new(1_000_001, "Player").unwrap();
    let messages = room.bot_join_messages(&human());
    assert_eq!(messages.len(), 17);
    assert!(messages.iter().all(|message| message.len() == 91));
    assert_eq!(messages[0], include_bytes!("fixtures/join-native.bin"));
    // Each request contains its own UID and team, not 17 identical copies.
    let distinct: std::collections::HashSet<_> = messages.iter().collect();
    assert_eq!(distinct.len(), 17);
}

#[test]
fn native_join_reader_recovers_bot_identity_team_and_compatibility_fields() {
    let Ok(python) = std::env::var("CODOL319_NATIVE_PYTHON") else {
        eprintln!("native replay not requested; set CODOL319_NATIVE_PYTHON with local snapshots");
        return;
    };
    let room = NuketownRoom::new(1_000_001, "Player").unwrap();
    let hex = |bytes: &[u8]| bytes.iter().map(|b| format!("{b:02x}")).collect::<String>();
    let messages = room.bot_join_messages(&human());
    let output = Command::new(python)
        .args(["-B", "../../../tests/client_room319.py", "join", &hex(&human())])
        .args(messages.iter().map(|message| hex(message)))
        .output().unwrap();
    assert!(output.status.success(), "{}{}", String::from_utf8_lossy(&output.stdout), String::from_utf8_lossy(&output.stderr));
}
