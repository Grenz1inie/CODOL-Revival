//! Movement over the real 2026-10-17 moving window: the reference trajectory
//! (work/codol319-move-input/move_reference319.py, live_sim319 integrator plus
//! C1 wish scaling, spawn-relative angle accumulation and 16-unit reconcile)
//! and the byte-level snapshot references from snapshot_codec319.py.
use codol_match319::movement::Movement;
use codol_match319::snapshot::Snapshot;
use codol_match319::transport::{UserCmd, client_control};
use serde_json::Value;

fn hex(bytes: &str) -> Vec<u8> {
    (0..bytes.len()).step_by(2).map(|i| u8::from_str_radix(&bytes[i..i + 2], 16).unwrap()).collect()
}

fn moving_records() -> Vec<Value> {
    serde_json::from_str(include_str!("fixtures/move319-moving.json")).unwrap()
}

fn golden() -> Value {
    serde_json::from_str(include_str!("fixtures/move319-trajectory.json")).unwrap()
}

fn spawn_origin() -> [f32; 3] {
    let value = golden();
    let origin = value["spawn"]["origin"].as_array().unwrap();
    [origin[0].as_f64().unwrap() as f32, origin[1].as_f64().unwrap() as f32, origin[2].as_f64().unwrap() as f32]
}

fn spawn_yaw() -> f32 { golden()["spawn"]["yaw"].as_f64().unwrap() as f32 }

fn near(a: f32, b: f64, tolerance: f32) -> bool { (a - b as f32).abs() <= tolerance }

fn assert_state(movement: &Movement, step: &Value) {
    let origin = step["origin"].as_array().unwrap();
    let velocity = step["velocity"].as_array().unwrap();
    for (got, want) in movement.origin.iter().zip(origin) {
        assert!(near(*got, want.as_f64().unwrap(), 1e-2), "origin {:?}", movement.origin);
    }
    for (got, want) in movement.velocity.iter().zip(velocity) {
        assert!(near(*got, want.as_f64().unwrap(), 1e-2), "velocity {:?}", movement.velocity);
    }
    assert!(near(movement.pitch, step["pitch"].as_f64().unwrap(), 1e-3));
    assert!(near(movement.yaw, step["yaw"].as_f64().unwrap(), 1e-3));
    assert_eq!(movement.command_time as u64, step["t"].as_u64().unwrap());
}

#[test]
fn real_moving_window_reproduces_the_reference_trajectory() {
    let reference = golden();
    let mut movement = Movement::new(spawn_origin(), spawn_yaw()).unwrap();
    let mut baseline: Option<UserCmd> = None;
    let mut step = 0;
    let steps = reference["steps"].as_array().unwrap();
    for record in moving_records() {
        let packet = hex(record["packet"].as_str().unwrap());
        let control = client_control(&packet, 0, baseline.as_ref()).unwrap();
        let mv = control.move_data.unwrap();
        baseline = mv.cmds.last().cloned();
        for cmd in &mv.cmds {
            if movement.apply(cmd) {
                assert_state(&movement, &steps[step]);
                step += 1;
            }
        }
        if let Some((xyz, time)) = mv.predicted {
            movement.reconcile(xyz, time);
        }
    }
    let reconciles = reference["reconciles"].as_array().unwrap();
    assert_eq!(step, steps.len());
    assert_eq!(movement.reconciled as usize, reconciles.iter().filter(|r| r[2].as_bool().unwrap()).count());
    // Pure integration without the static capture's predicted reports.
    let mut solo = Movement::new(spawn_origin(), spawn_yaw()).unwrap();
    let mut baseline = None;
    for record in moving_records() {
        let control = client_control(&hex(record["packet"].as_str().unwrap()), 0, baseline.as_ref()).unwrap();
        let mv = control.move_data.unwrap();
        baseline = mv.cmds.last().cloned();
        for cmd in &mv.cmds { solo.apply(cmd); }
    }
    let end = &reference["noreconcile"];
    assert_eq!(solo.applied as u64, end["steps"].as_u64().unwrap());
    for (got, want) in solo.origin.iter().zip(end["origin"].as_array().unwrap()) {
        assert!(near(*got, want.as_f64().unwrap(), 1e-2));
    }
    for (got, want) in solo.velocity.iter().zip(end["velocity"].as_array().unwrap()) {
        assert!(near(*got, want.as_f64().unwrap(), 1e-2));
    }
    assert!(near(solo.yaw, end["yaw"].as_f64().unwrap(), 1e-3));
    // The user really held LEFT: the movement must be along the yaw-330 left vector.
    let dx = solo.origin[0] - spawn_origin()[0];
    let dy = solo.origin[1] - spawn_origin()[1];
    assert!(dx > 1.0 && dy > 1.0, "expected +x/+y drift for LEFT at yaw 330, got {dx}/{dy}");
    assert!(dx.hypot(dy) > 5.0, "expected a real displacement, got {}", dx.hypot(dy));
}

fn cmd(time: u32, buttons: u32, angles: [u16; 3], class: u8) -> UserCmd {
    UserCmd { server_time: time, buttons, angles, move_class: class, ..UserCmd::default() }
}

#[test]
fn commands_are_ordered_capped_and_strafe_follows_the_yaw() {
    let mut movement = Movement::new([0.0, 0.0, 10.0], 0.0).unwrap();
    assert!(movement.apply(&cmd(1000, 0, [0; 3], 0)));
    assert!(!movement.apply(&cmd(1000, 0, [0; 3], 0)), "duplicate time ignored");
    assert!(!movement.apply(&cmd(900, 0, [0; 3], 0)), "older time ignored");
    assert_eq!(movement.command_time, 1000);

    // A 4-second gap integrates at most 200 ms; z is never integrated by the host.
    assert!(movement.apply(&cmd(5000, 0, [0; 3], 1)));
    let speed = movement.velocity[0].hypot(movement.velocity[1]);
    assert!(speed > 0.0 && speed <= 190.0, "speed {speed}");
    let moved = (movement.origin[0].hypot(movement.origin[1]) / 190.0) * 1000.0;
    assert!(moved <= 200.0 + 1.0, "integrated {moved} ms");
    assert_eq!(movement.origin[2], 10.0);
    assert_eq!(movement.velocity[2], 0.0);

    // LEFT at yaw 0 is +y; sprint with forward pushes past the walk speed.
    let mut strafe = Movement::new([0.0; 3], 0.0).unwrap();
    strafe.apply(&cmd(1000, 0, [0; 3], 8));
    for time in (1006..2000).step_by(6) { strafe.apply(&cmd(time, 0, [0; 3], 8)); }
    assert!(strafe.origin[1] > 100.0 && strafe.origin[0].abs() < 1.0,
            "left drift {:?} must be +y", strafe.origin);

    let mut sprint = Movement::new([0.0; 3], 0.0).unwrap();
    sprint.apply(&cmd(1000, 0x2, [0; 3], 1));
    for time in (1006..3000).step_by(6) { sprint.apply(&cmd(time, 0x2, [0; 3], 1)); }
    assert!(sprint.velocity[0] > 250.0, "sprint forward speed {:?}", sprint.velocity);
}

#[test]
fn angles_accumulate_relative_to_the_spawn_and_clamp_the_pitch() {
    let mut movement = Movement::new([0.0; 3], 330.0).unwrap();
    movement.apply(&cmd(1000, 0, [0, 0x7FE8, 0], 0));
    assert_eq!(movement.yaw, 330.0, "spawn yaw kept until the mouse moves");
    movement.apply(&cmd(1006, 0, [0x1555, 0x7FE8, 0], 0));  // +30 degrees pitch
    assert!((movement.pitch - 30.0).abs() < 0.01, "{}", movement.pitch);
    // shorts wrapping across 0x7fff/0x8000 must read as +8 shorts, not a full turn.
    for (i, time) in (1012..1400).step_by(6).enumerate() {
        movement.apply(&cmd(time, 0, [0x1555, 0x7FF0 + 8 * ((i % 4) as u16), 0], 0));
    }
    assert!((movement.yaw - 330.0).abs() < 1.0, "yaw {}", movement.yaw);
    for (time, pitch) in (1400..1600).step_by(6).zip([0x2AAA, 0x4000, 0x4000, 0x4000]) {
        movement.apply(&cmd(time, 0, [pitch, 0, 0], 0));   // 60 then 90 degrees: clamped at 85
    }
    assert_eq!(movement.pitch, 85.0, "pitch clamped");
}

#[test]
fn reconcile_follows_the_client_report_and_z_never_fights_back() {
    // The live 2026-10-17 round: the client fell from the spawn z -24 to its
    // real floor at -63.88 while the host kept sending -24, bouncing the view
    // 2835 times. The host has no clipmap, so a time-matching report always
    // wins and apply never moves z again afterwards.
    let mut movement = Movement::new([0.0, 0.0, 0.0], 0.0).unwrap();
    movement.apply(&cmd(1000, 0, [0; 3], 1));
    assert_eq!(movement.reconcile([3.0, 4.0, 0.0], 999), None, "not this command time");
    let distance = movement.reconcile([3.0, 4.0, 0.0], 1000).unwrap();
    assert!((distance - 5.0).abs() < 0.01);
    assert_eq!(movement.origin, [3.0, 4.0, 0.0]);
    // Far reports win too: the client owns collision, the host cannot correct it.
    assert!(movement.reconcile([200.0, 0.0, -50.0], 1000).unwrap() > 190.0);
    assert_eq!(movement.origin, [200.0, 0.0, -50.0], "client prediction is authoritative");
    // Later commands integrate xy only; the adopted height is kept.
    movement.apply(&cmd(1006, 0, [0; 3], 0));
    movement.apply(&cmd(1012, 0, [0; 3], 0));
    assert_eq!(movement.origin[2], -50.0, "z is never reset to the spawn height");
    assert_eq!(movement.origin[0], 200.0, "no keys: xy unchanged");
    assert_eq!(movement.reconciled, 2);
}

#[test]
fn snapshot_bytes_match_the_python_codec_for_moving_player_states() {
    let reference = golden();
    for state in reference["snapshots"].as_array().unwrap() {
        let floats = |name: &str| -> [f32; 3] {
            let values = state[name].as_array().unwrap();
            [values[0].as_f64().unwrap() as f32, values[1].as_f64().unwrap() as f32,
             values[2].as_f64().unwrap() as f32]
        };
        let mut snapshot = Snapshot::new(spawn_origin(), spawn_yaw()).unwrap();
        snapshot.set_player(floats("origin"), floats("velocity"),
                            state["pitch"].as_f64().unwrap() as f32,
                            state["yaw"].as_f64().unwrap() as f32).unwrap();
        let frame = snapshot.encode(state["stamp"].as_u64().unwrap() as u32,
                                    state["command"].as_u64().unwrap() as u32, 0).unwrap();
        let hex = frame.iter().map(|b| format!("{b:02x}")).collect::<String>();
        assert_eq!(hex, state["hex"].as_str().unwrap(), "stamp {}", state["stamp"]);
    }
    let mut snapshot = Snapshot::new([0.0; 3], 0.0).unwrap();
    assert!(snapshot.set_player([f32::NAN, 0.0, 0.0], [0.0; 3], 0.0, 0.0).is_err());
    assert!(snapshot.set_player([0.0; 3], [131073.0, 0.0, 0.0], 0.0, 0.0).is_err());
    assert!(snapshot.set_player([0.0; 3], [0.0; 3], 0.0, f32::INFINITY).is_err());
}

#[test]
fn session_feeds_real_moves_into_the_snapshot_state() {
    use codol_match319::transport::Session;
    use codol_match319::NuketownRoom;
    let mut session = Session::new(NuketownRoom::new(1000001, "Player").unwrap(), 0);
    let peer = "127.0.0.1:31999".parse().unwrap();
    session.handle(peer, b"\xff\xff\xff\xffconnect 00000000000f4241 \"\\challenge\\0\"").unwrap();
    let wire = include_bytes!("fixtures/stats-zlib.bin");
    let stats = [b"\xff\xff\xff\xffstats\0\0".as_slice(), &(wire.len() as u16).to_le_bytes(), wire].concat();
    session.handle(peer, &stats).unwrap();
    session.set_gamestate(vec![3, 0, 0, 0, 0, b'm', 0, b'c', 0, 1, 2, 3, 4, 5]).unwrap();
    let client = |sequence: u32, ack: u32| -> Vec<u8> {
        [sequence.to_le_bytes().as_slice(), &[0], &ack.to_le_bytes(), &0u32.to_le_bytes(),
            &[3 ^ ack as u8]].concat()
    };
    for sequence in 1..=5 { session.handle(peer, &client(sequence, sequence - 1)); }
    session.handle(peer, b"\xff\xff\xff\xffgamestateupdate 6");
    session.set_spawn(spawn_origin(), spawn_yaw()).unwrap();
    session.tick(1).unwrap();
    session.handle(peer, &client(6, 5));
    for k in 1..=410 { session.tick(k * 50); }        // server sequence 415 covers the window's acks
    // The exact acceptance and decode chain load_map applies, fed directly: the
    // window is mid-session, so the strict reliable-command numbering (here
    // 18..21 with 1..17 never seen) and the cold baseline drop some packets and
    // delta-encoded times. The full-chain trajectory is covered above.
    let mut expected = Movement::new(spawn_origin(), spawn_yaw()).unwrap();
    let mut chain: Option<UserCmd> = None;
    let (mut client_seq, mut command_seq) = (6u32, 0u32);
    for record in moving_records() {
        let control = client_control(&hex(record["packet"].as_str().unwrap()), 0, chain.as_ref());
        let Some(control) = control else { continue };
        let mut accepted = control.sequence > client_seq && control.ack <= 415;
        let mut number = command_seq;
        for next in control.commands.iter().map(|(next, _)| *next) {
            if next <= number { continue; }
            if next != number + 1 { accepted = false; break; }
            number = next;
        }
        if !accepted { continue; }
        client_seq = control.sequence;
        command_seq = number;
        if let Some(mv) = &control.move_data {
            if let Some(last) = mv.cmds.last() { chain = Some(last.clone()); }
            for cmd in &mv.cmds { expected.apply(cmd); }
            if let Some((origin, time)) = mv.predicted { expected.reconcile(origin, time); }
        }
    }
    assert!(expected.applied > 0);
    for record in moving_records() {
        session.handle(peer, &hex(record["packet"].as_str().unwrap()));
    }
    let movement = session.movement().expect("moves reached the session movement");
    assert_eq!(movement.applied, expected.applied);
    assert_eq!(movement.reconciled, expected.reconciled);
    for (got, want) in movement.origin.iter().zip(expected.origin.iter()) {
        assert!((got - want).abs() < 1e-3, "session origin {:?} vs {:?}", movement.origin, expected.origin);
    }
    assert_eq!(movement.command_time, expected.command_time);
}
