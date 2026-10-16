use std::io::Write;
use std::process::{Command, Stdio};

fn run(input: &str) -> std::process::Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_codol-match319"))
        .arg("room").stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped())
        .spawn().unwrap();
    child.stdin.take().unwrap().write_all(input.as_bytes()).unwrap();
    child.wait_with_output().unwrap()
}

#[test]
fn manifest_preserves_u64_identity_and_emits_joins_only_after_native_host_state() {
    let first = run(r#"{"uid":1000001,"name":"Player"}"#);
    assert!(first.status.success());
    let first = String::from_utf8(first.stdout).unwrap();
    assert!(first.contains("25769803777"));
    assert!(!first.contains("\"join\""));
    // The committed fixture came from the native message-14 writer.
    let roster = include_bytes!("fixtures/roster-native.bin");
    let bytes = roster.iter().map(u8::to_string).collect::<Vec<_>>().join(",");
    let second = run(&format!(r#"{{"uid":1000001,"name":"Player","roster":[{bytes}]}}"#));
    assert!(second.status.success(), "{}", String::from_utf8_lossy(&second.stderr));
    let second = String::from_utf8(second.stdout).unwrap();
    assert_eq!(second.matches("\"join\"").count(), 17);
    assert_eq!(second.matches("\"team\":1").count(), 9);
    assert_eq!(second.matches("\"team\":2").count(), 9);
}

#[test]
fn invalid_host_roster_cannot_emit_a_manifest() {
    for input in [r#"{"uid":1000001,"name":"Player","roster":[28,0]}"#,
                  r#"{"uid":1000001,"name":"Player","roster":[256]}"#] {
        let result = run(input);
        assert!(!result.status.success());
        assert!(result.stdout.is_empty());
        assert!(!result.stderr.is_empty());
    }
}
