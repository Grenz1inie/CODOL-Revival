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

fn serve(path: &str) -> Result<Value, Box<dyn std::error::Error>> {
    use codol_match319::transport::Session;
    use std::io::{ErrorKind, Write};
    use std::net::UdpSocket;
    use std::path::Path;
    use std::time::Duration;
    let config: Value = serde_json::from_reader(std::fs::File::open(path)?)?;
    let uid = config["uid"].as_u64().ok_or("missing player UID")?;
    let name = config["name"].as_str().ok_or("missing player name")?;
    let roster: Vec<u8> = serde_json::from_value(config["roster"].clone())?;
    let (room, _) = NuketownRoom::from_host_roster(uid, name, &roster)?;
    let port = u16::try_from(config["port"].as_u64().ok_or("missing UDP port")?)?;
    let stop = Path::new(config["stop_file"].as_str().ok_or("missing stop file")?);
    let socket = UdpSocket::bind((std::net::Ipv4Addr::LOCALHOST, port))?;
    socket.set_read_timeout(Some(Duration::from_millis(100)))?;
    let players: Vec<_> = room.players().iter().map(|p| json!({"uid":p.uid,"slot":p.slot,
        "name":p.name,"team":if p.team == Team::One {1} else {2},"bot":p.is_bot})).collect();
    println!("{}", json!({"event":"listening","address":socket.local_addr()?.to_string(),"players":players}));
    std::io::stdout().flush()?;
    // The provided local proxy starts with connect/challenge=0, without getchallenge.
    let mut session = Session::new(room, 0);
    let mut buffer = [0; 65535];
    while !stop.exists() {
        match socket.recv_from(&mut buffer) {
            Ok((size, peer)) => {
                if let Some(response) = session.handle(peer, &buffer[..size]) { socket.send_to(&response, peer)?; }
            }
            Err(error) if matches!(error.kind(), ErrorKind::WouldBlock | ErrorKind::TimedOut) => {}
            Err(error) => return Err(error.into()),
        }
    }
    Ok(json!({"event":"stopped"}))
}

fn main() {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let result = match args.as_slice() {
        [command] if command == "room" => room(),
        [command, config] if command == "serve" => serve(config),
        _ => Err("usage: codol-match319 room < request.json | serve room.json".into()),
    };
    match result {
        Ok(value) => println!("{value}"),
        Err(error) => { eprintln!("{error}"); std::process::exit(1); }
    }
}
