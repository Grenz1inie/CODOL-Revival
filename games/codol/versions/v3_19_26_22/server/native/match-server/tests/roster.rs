use codol_match319::NuketownRoom;
use std::process::Command;

fn human_state() -> [u8; 0x1d0] {
    let mut row = [0; 0x1d0];
    row[0x94..0x98].copy_from_slice(&1000u32.to_le_bytes());
    row[0xac..0xb0].fill(0xff);
    row[0xb0] = 0xff;
    row
}

#[test]
fn roster_matches_the_current_client_native_writer() {
    let mut human = human_state();
    human[0x90] = 1;
    let room = NuketownRoom::new(1_000_001, "Player").unwrap();
    let mut expected = *include_bytes!("fixtures/roster-native.bin");
    for slot in 1..18 {
        let ready_bit = 41 + slot * 545 + 64 + 8;
        expected[ready_bit / 8] &= !(1 << (ready_bit % 8));
    }
    assert_eq!(room.roster_message(&human), expected);
}

#[test]
fn human_readiness_is_not_forced_by_filling_the_room() {
    let room = NuketownRoom::new(1_000_001, "Player").unwrap();
    let mut human = human_state();
    let waiting = room.roster_message(&human);
    human[0x90] = 1;
    let ready = room.roster_message(&human);
    let changed: Vec<_> = waiting.iter().zip(&ready).enumerate()
        .filter(|(_, (a, b))| a != b).map(|(i, (a, b))| (i, a ^ b)).collect();
    // Header 41 bits, UID 64 bits, team 8 bits, then ready.
    assert_eq!(changed, vec![(14, 2)]);
    assert_eq!(waiting.len(), 1232);
}

#[test]
fn current_native_consumer_accepts_the_complete_roster_and_human_fields() {
    let Ok(python) = std::env::var("CODOL319_NATIVE_PYTHON") else {
        eprintln!("native replay not requested; set CODOL319_NATIVE_PYTHON with local snapshots");
        return;
    };
    let room = NuketownRoom::new(1_000_001, "Player").unwrap();
    let mut human = human_state();
    human[0x94..0x98].copy_from_slice(&0x1a0445u32.to_le_bytes());
    human[0x1a8..0x1ac].copy_from_slice(&0x12345678u32.to_le_bytes());
    let hex = |bytes: &[u8]| bytes.iter().map(|b| format!("{b:02x}")).collect::<String>();
    let output = Command::new(python)
        .args(["-B", "../../../tests/client_room319.py", &hex(&room.roster_message(&human)), &hex(&human)])
        .output().unwrap();
    assert!(output.status.success(), "{}{}", String::from_utf8_lossy(&output.stdout), String::from_utf8_lossy(&output.stderr));
}
