//! Version 3.19.26.22 match rules and room state.

mod room_wire;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Team {
    One,
    Two,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Player {
    pub uid: u64,
    pub slot: u8,
    pub name: String,
    pub team: Team,
    pub is_bot: bool,
}

pub struct Rules {
    pub playlist: u32,
    pub map: &'static str,
    pub gametype: &'static str,
    pub score_limit: u32,
    pub time_limit_seconds: u32,
    pub team_size: usize,
}

// Current 3.19 publisher playlist 110; not the modified 3.3 DM playlist.
const NUKETOWN: Rules = Rules {
    playlist: 110,
    map: "mp_nuked",
    gametype: "cha",
    score_limit: 150,
    time_limit_seconds: 1200,
    team_size: 9,
};

pub struct NuketownRoom {
    players: Vec<Player>,
}

impl NuketownRoom {
    pub fn new(human_uid: u64, name: &str) -> Result<Self, &'static str> {
        if human_uid == 0 || name.is_empty() || name.chars().any(char::is_control) {
            return Err("invalid player identity");
        }
        let mut players = vec![Player {
            uid: human_uid,
            slot: 0,
            name: name.to_owned(),
            team: Team::One,
            is_bot: false,
        }];
        let mut bot_uid = 0x600000001;
        for slot in 1..18 {
            if bot_uid == human_uid {
                bot_uid += 1;
            }
            players.push(Player {
                uid: bot_uid,
                slot,
                name: format!("Bot{slot:02}"),
                team: if slot < 9 { Team::One } else { Team::Two },
                is_bot: true,
            });
            bot_uid += 1;
        }
        Ok(Self { players })
    }

    pub fn players(&self) -> &[Player] {
        &self.players
    }

    pub fn rules(&self) -> &Rules {
        &NUKETOWN
    }

    /// Message 14; channel membership supplies names separately.
    pub fn roster_message(&self, human_state: &[u8; 0x1d0]) -> Vec<u8> {
        room_wire::roster(self.players(), human_state)
    }
}
