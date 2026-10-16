use codol_match319::{NuketownRoom, Team};
use std::collections::HashSet;

#[test]
fn joining_populates_both_teams_before_any_start_request() {
    let room = NuketownRoom::new(1_000_001, "Player").unwrap();
    let players = room.players();
    assert_eq!(players.len(), 18);
    assert_eq!(players.iter().filter(|p| p.is_bot).count(), 17);
    for team in [Team::One, Team::Two] {
        assert_eq!(players.iter().filter(|p| p.team == team).count(), 9);
    }
    assert_eq!(players.iter().map(|p| p.uid).collect::<HashSet<_>>().len(), 18);
    assert_eq!(players.iter().map(|p| p.slot).collect::<HashSet<_>>().len(), 18);
    assert_eq!(players[0].uid, 1_000_001);
    assert_eq!(players[0].name, "Player");
    assert!(!players[0].is_bot);
    assert!(players.iter().all(|p| p.slot < 18));
}

#[test]
fn rules_retain_the_current_charge_playlist_not_free_for_all() {
    let room = NuketownRoom::new(1_000_001, "Player").unwrap();
    assert_eq!(room.rules().playlist, 110);
    assert_eq!(room.rules().map, "mp_nuked");
    assert_eq!(room.rules().gametype, "cha");
    assert_eq!(room.rules().score_limit, 150);
    assert_eq!(room.rules().time_limit_seconds, 20 * 60);
    assert_eq!(room.rules().team_size, 9);
}

#[test]
fn roster_is_stable_for_repeated_reads_and_rejoins() {
    let first = NuketownRoom::new(1_000_001, "Player").unwrap();
    let again = NuketownRoom::new(1_000_001, "Player").unwrap();
    assert_eq!(first.players(), again.players());
}

#[test]
fn bot_id_allocation_never_reuses_the_human_identity() {
    for uid in [1, 1_000_001, 0x600000001, u64::MAX] {
        let room = NuketownRoom::new(uid, "Player").unwrap();
        assert_eq!(room.players().iter().filter(|p| p.uid == uid).count(), 1);
        assert_eq!(room.players().iter().map(|p| p.uid).collect::<HashSet<_>>().len(), 18);
    }
}

#[test]
fn invalid_identity_does_not_create_a_partial_room() {
    assert!(NuketownRoom::new(0, "Player").is_err());
    for name in ["", "a\0b", "玩家\n"] {
        assert!(NuketownRoom::new(1_000_001, name).is_err());
    }
}
