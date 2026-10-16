use codol_match319::{NuketownRoom, Team};

fn host(team: u8) -> Vec<u8> {
    // Native message 14 with one human; constructed from the existing native fixture.
    let original = include_bytes!("fixtures/roster-native.bin");
    let mut payload = original[..74].to_vec();
    // Count starts at bit 9; native team byte starts at bit 105.
    for (start, width, value) in [(9, 32, 1u64), (105, 8, team as u64)] {
        for bit in 0..width {
            let index = start + bit;
            payload[index / 8] = (payload[index / 8] & !(1 << (index % 8)))
                | ((((value >> bit) & 1) as u8) << (index % 8));
        }
    }
    payload[73] &= 3; // 586 meaningful bits.
    payload
}

#[test]
fn native_host_team_is_preserved_with_nine_members_on_each_side() {
    for (value, team) in [(1, Team::One), (2, Team::Two)] {
        let (room, state) = NuketownRoom::from_host_roster(1_000_001, "Player", &host(value)).unwrap();
        assert_eq!(room.players()[0].team, team);
        assert_eq!(state[0x88], value);
        for side in [Team::One, Team::Two] {
            assert_eq!(room.players().iter().filter(|p| p.team == side).count(), 9);
        }
    }
}

#[test]
fn invalid_or_unrelated_rosters_cannot_create_admissions() {
    let valid = host(1);
    for payload in [&[][..], &valid[..73], &host(0), &host(6)] {
        assert!(NuketownRoom::from_host_roster(1_000_001, "Player", payload).is_err());
    }
    assert!(NuketownRoom::from_host_roster(42, "Player", &valid).is_err());
    let mut wrong_type = valid;
    wrong_type[0] = 12;
    assert!(NuketownRoom::from_host_roster(1_000_001, "Player", &wrong_type).is_err());
}
