use codol_match319::snapshot::Snapshot;

#[test]
fn first_frame_matches_current_319_reference_and_continuation_uses_render_flags() {
    let snapshot = Snapshot::new([100.0, -200.0, 300.0], 90.0).unwrap();
    // snapshot_codec319.py, current hash-bound 246-field definition, zero weapon.
    let expected = "00e80300000008a207601a000000000000c842b100009643000048c3000000002b00000000000000003c004098000070423cf0e9ff0000803f22be00892003deffffffffff3f6c0000803f1fff600100640064000000fc3f05";
    let frame = snapshot.encode(1000, 1000, 0).unwrap();
    assert_eq!(frame.iter().map(|b| format!("{b:02x}")).collect::<String>(), expected);
    for delta in 1..=15 {
        let next = snapshot.encode(1000, 1000, delta).unwrap();
        assert_eq!(&next[..5], &frame[..5]);
        assert_eq!(&next[5..7], &[delta, 0]);
        assert_eq!(&next[7..], &frame[7..]);
    }
}

#[test]
fn invalid_coordinates_times_and_delta_never_emit_a_snapshot() {
    for point in [[f32::NAN, 0.0, 0.0], [0.0, f32::INFINITY, 0.0], [131073.0, 0.0, 0.0]] {
        assert!(Snapshot::new(point, 0.0).is_err());
    }
    assert!(Snapshot::new([0.0; 3], f32::NAN).is_err());
    let snapshot = Snapshot::new([0.0; 3], 0.0).unwrap();
    for (stamp, command, delta) in [(0, 0, 0), (0x80000000, 0, 0), (1000, 0x80000000, 0), (1000, 0, 16)] {
        assert!(snapshot.encode(stamp, command, delta).is_err());
    }
}
