use codol_match319::{NuketownRoom, Team};
use serde_json::{Value, json};

fn room() -> Result<Value, Box<dyn std::error::Error>> {
    let request: Value = serde_json::from_reader(std::io::stdin().lock())?;
    let uid = request["uid"].as_u64().ok_or("missing player UID")?;
    let name = request["name"].as_str().ok_or("missing player name")?;
    let (room, joins) = if let Some(value) = request.get("roster") {
        let payload: Vec<u8> = serde_json::from_value(value.clone())?;
        let (room, state) = NuketownRoom::from_host_roster(uid, name, &payload)?;
        let joins = room.bot_join_messages(&state);
        (room, joins)
    } else {
        (NuketownRoom::new(uid, name)?, Vec::new())
    };
    let players: Vec<Value> = room.players().iter().map(|player| {
        let mut value = json!({"uid": player.uid, "slot": player.slot, "name": player.name,
            "team": if player.team == Team::One { 1 } else { 2 }, "bot": player.is_bot});
        if player.is_bot && !joins.is_empty() {
            value["join"] = json!(joins[player.slot as usize - 1]);
        }
        value
    }).collect();
    Ok(json!({"players": players}))
}

fn main() {
    let result = if std::env::args().skip(1).collect::<Vec<_>>() == ["room"] {
        room()
    } else {
        Err("usage: codol-match319 room < request.json".into())
    };
    match result {
        Ok(value) => println!("{value}"),
        Err(error) => { eprintln!("{error}"); std::process::exit(1); }
    }
}
