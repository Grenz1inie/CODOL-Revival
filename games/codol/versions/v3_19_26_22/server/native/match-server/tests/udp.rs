use serde_json::json;
use std::io::{BufRead, BufReader};
use std::net::{SocketAddr, UdpSocket};
use std::process::{Child, Command, Stdio};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

struct Server(Child);
impl Drop for Server { fn drop(&mut self) { let _ = self.0.kill(); let _ = self.0.wait(); } }

#[test]
fn real_udp_owns_one_room_upload_and_stops_on_request() {
    let dir = std::env::temp_dir().join(format!("codol319-udp-{}-{}", std::process::id(),
        SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos()));
    std::fs::create_dir(&dir).unwrap();
    let stop = dir.join("stop.request");
    let config = dir.join("room.json");
    std::fs::write(&config, json!({"uid":1000001,"name":"Player","port":0,"stop_file":stop,
        "roster":include_bytes!("fixtures/roster-native.bin").as_slice()}).to_string()).unwrap();
    let mut server = Server(Command::new(env!("CARGO_BIN_EXE_codol-match319"))
        .args(["serve", config.to_str().unwrap()]).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn().unwrap());
    let mut line = String::new();
    let mut output = BufReader::new(server.0.stdout.take().unwrap());
    output.read_line(&mut line).unwrap();
    assert!(!line.is_empty(), "server exited before announcing its socket");
    let ready: serde_json::Value = serde_json::from_str(&line).unwrap();
    assert_eq!(ready["event"], "listening");
    assert_eq!(ready["players"].as_array().unwrap().len(), 18);
    let address: SocketAddr = ready["address"].as_str().unwrap().parse().unwrap();
    assert!(address.ip().is_loopback());
    let socket = UdpSocket::bind("127.0.0.1:0").unwrap();
    socket.set_read_timeout(Some(Duration::from_secs(3))).unwrap();
    let exchange = |packet: &[u8]| {
        socket.send_to(packet, address).unwrap();
        let mut response = [0; 2048];
        let (size, sender) = socket.recv_from(&mut response).unwrap();
        assert_eq!(sender, address);
        response[..size].to_vec()
    };
    let reply = exchange(b"\xff\xff\xff\xffconnect 00000000000f4241 \"\\challenge\\0\"");
    assert_eq!(reply, b"\xff\xff\xff\xffconnectResponse \\mapname\\mp_nuked\\gametype\\cha\\sv_maxclients\\18\\protocol\\1\0");
    let wire = include_bytes!("fixtures/stats-zlib.bin");
    let packet = [b"\xff\xff\xff\xffstats\0\0".as_slice(), &(wire.len() as u16).to_le_bytes(), wire].concat();
    assert_eq!(exchange(&packet), b"\xff\xff\xff\xffstatResponse 0\0");
    std::fs::write(&stop, b"").unwrap();
    let deadline = std::time::Instant::now() + Duration::from_secs(3);
    loop {
        if let Some(status) = server.0.try_wait().unwrap() { assert!(status.success()); break; }
        assert!(std::time::Instant::now() < deadline, "server ignored stop.request");
        std::thread::sleep(Duration::from_millis(20));
    }
    std::fs::remove_file(config).unwrap();
    std::fs::remove_file(stop).unwrap();
    std::fs::remove_dir(dir).unwrap();
}
