//! Real 3.19 client move packets from the 2026-10-17 Nuketown session capture
//! (work/codol319-map-live-20261017/session.pcapng), decoded by the verified
//! parser (match_host/client_message319.py) with the baseline chained from the
//! session's first move packet. The server published no server commands and
//! used challenge 0 in this run.
use codol_match319::transport::{UserCmd, client_control};
use serde_json::Value;

fn hex(bytes: &str) -> Vec<u8> {
    (0..bytes.len()).step_by(2).map(|i| u8::from_str_radix(&bytes[i..i + 2], 16).unwrap()).collect()
}

fn records(name: &str) -> Vec<Value> {
    serde_json::from_str(match name {
        "head" => include_str!("fixtures/move319-head.json"),
        "moving" => include_str!("fixtures/move319-moving.json"),
        "tail" => include_str!("fixtures/move319-tail.json"),
        _ => unreachable!(),
    }).unwrap()
}

fn usercmd(value: &Value) -> UserCmd {
    UserCmd {
        server_time: value["server_time"].as_u64().unwrap() as u32,
        buttons: value["buttons"].as_u64().unwrap() as u32,
        angles: [value["angles"][0].as_u64().unwrap() as u16,
                 value["angles"][1].as_u64().unwrap() as u16,
                 value["angles"][2].as_u64().unwrap() as u16],
        move_class: value["move_class"].as_u64().unwrap() as u8,
        w14: value["w14"].as_u64().unwrap() as u16,
        w16: value["w16"].as_u64().unwrap() as u16,
        w18: value["w18"].as_u64().unwrap() as u16,
        b20: value["b20"].as_u64().unwrap() as u8,
        w22: value["w22"].as_u64().unwrap() as u16,
        a1c: value["a1c"].as_u64().unwrap() as u16,
        b24: value["b24"].as_u64().unwrap() as u8,
        b25: value["b25"].as_u64().unwrap() as u8,
        b26: value["b26"].as_u64().unwrap() as u8,
        b27: value["b27"].as_u64().unwrap() as u8,
        b28: value["b28"].as_u64().unwrap() as u8,
    }
}

#[test]
fn real_move_packets_decode_to_the_reference_usercmds() {
    for name in ["head", "moving", "tail"] {
        let mut baseline: Option<UserCmd> = None;
        for record in records(name) {
            let packet = hex(record["packet"].as_str().unwrap());
            let control = client_control(&packet, 0, baseline.as_ref())
                .unwrap_or_else(|| panic!("{name} frame {} rejected", record["frame"]));
            assert_eq!(control.sequence as u64, record["sequence"].as_u64().unwrap(), "{name}");
            assert_eq!(control.ack as u64, record["server_ack"].as_u64().unwrap(), "{name}");
            let commands: Vec<_> = control.commands.iter()
                .map(|(n, text)| (*n as u64, String::from_utf8_lossy(text).into_owned())).collect();
            let expected: Vec<_> = record["commands"].as_array().unwrap().iter()
                .map(|c| (c[0].as_u64().unwrap(), c[1].as_str().unwrap().to_owned())).collect();
            assert_eq!(commands, expected, "{name} frame {}", record["frame"]);

            let reference = &record["move"];
            let mv = control.move_data.as_ref()
                .unwrap_or_else(|| panic!("{name} frame {} has no move", record["frame"]));
            assert_eq!(mv.delta, reference["delta"].as_bool().unwrap());
            assert_eq!(mv.cmds.len() as u64, reference["cmds"].as_array().unwrap().len() as u64);
            let want: Vec<UserCmd> = reference["cmds"].as_array().unwrap().iter().map(usercmd).collect();
            assert_eq!(mv.cmds, want, "{name} frame {} usercmds", record["frame"]);
            match (&mv.predicted, reference["predicted"].is_null()) {
                (Some((xyz, time)), false) => {
                    let expected = reference["predicted"].as_array().unwrap();
                    for (got, want) in xyz.iter().zip(expected[0].as_array().unwrap()) {
                        assert!((got - want.as_f64().unwrap() as f32).abs() < 1e-3,
                                "{name} frame {} predicted {xyz:?}", record["frame"]);
                    }
                    assert_eq!(*time as u64, expected[1].as_u64().unwrap());
                }
                (None, true) => {}
                _ => panic!("{name} frame {} predicted mismatch", record["frame"]),
            }
            baseline = mv.cmds.last().cloned();
        }
    }
}

// Bit writer mirroring the native independent byte/bit cursors: byte writes
// advance only the byte cursor, so a following bit group keeps consuming the
// partially read byte (the op byte also carries the first usercmd gate bits).
struct Writer { bytes: Vec<u8>, read: usize, bit: usize }

impl Writer {
    fn new() -> Self { Self { bytes: Vec::new(), read: 0, bit: 0 } }
    fn bits(&mut self, value: u32, count: usize) {
        for shift in 0..count {
            if self.bit % 8 == 0 {
                self.bit = self.read * 8;
                self.bytes.push(0);
                self.read += 1;
            }
            self.bytes[self.bit / 8] |= (((value >> shift) & 1) as u8) << (self.bit % 8);
            self.bit += 1;
        }
    }
    fn raw(&mut self, data: &[u8]) {
        self.bytes.extend_from_slice(data);
        self.read += data.len();
    }
    /// One unchanged (case A) usercmd at absolute time `time`, then the origin trailer.
    /// With ack 4 the usercmd key is 4, so kbit 0: the case A gate reads 0.
    fn plain_move(&mut self, op: u32, count: u8, time: u32, origin: [u32; 4]) {
        self.bits(op, 3);
        self.raw(&[count]);
        self.bits(0, 1);                 // absolute server time
        self.raw(&time.to_le_bytes());
        self.bits(0, 1);                 // case A gate
        self.bits(7, 3);                 // case A terminator
        for word in origin { self.raw(&word.to_le_bytes()); }
    }
    fn packet(self) -> Vec<u8> {
        let mut packet = vec![9, 0, 0, 0, 1, 4, 0, 0, 0, 0, 0, 0, 0];
        packet.extend(self.bytes.iter().map(|b| b ^ 5));
        packet
    }
}

fn spawn_bits(origin: [f32; 3], time: u32) -> [u32; 4] {
    [origin[0].to_bits(), origin[1].to_bits(), origin[2].to_bits(), time]
}

#[test]
fn synthetic_move_payloads_decode_and_bad_terminators_are_rejected() {
    let mut writer = Writer::new();
    writer.plain_move(0, 1, 1000, spawn_bits([-1601.8, 1176.2, -24.0], 1000));
    let control = client_control(&writer.packet(), 0, None).unwrap();
    let mv = control.move_data.unwrap();
    assert_eq!((mv.delta, mv.cmds.len(), mv.cmds[0].server_time), (true, 1, 1000));
    assert_eq!(mv.predicted.unwrap().1, 1000);

    let mut writer = Writer::new();
    writer.plain_move(1, 1, 1000, spawn_bits([0.0; 3], 1000));
    let control = client_control(&writer.packet(), 0, None).unwrap();
    assert!(!control.move_data.as_ref().unwrap().delta, "moveNoDelta chains from zeroed baseline");

    let mut writer = Writer::new();      // case A terminator must be 7
    writer.plain_move(0, 1, 1000, spawn_bits([0.0; 3], 1000));
    writer.bytes[0] = (writer.bytes[0] & !0xe0) | (3 << 5);
    assert!(client_control(&writer.packet(), 0, None).is_none());

    let mut writer = Writer::new();      // count 2 with a single command's payload
    writer.plain_move(0, 2, 1000, spawn_bits([0.0; 3], 1000));
    assert!(client_control(&writer.packet(), 0, None).is_none());

    let mut writer = Writer::new();      // non-finite predicted origin: move kept, trailer dropped
    writer.plain_move(0, 1, 1000, [f32::INFINITY.to_bits(), 0, 0, 1000]);
    let control = client_control(&writer.packet(), 0, None).unwrap();
    assert!(control.move_data.unwrap().predicted.is_none());

    let mut writer = Writer::new();      // trailer truncation keeps the commands and cmds
    writer.plain_move(0, 1, 1000, spawn_bits([0.0; 3], 1000));
    let mut packet = writer.packet();
    packet.truncate(packet.len() - 3);
    let control = client_control(&packet, 0, None).unwrap();
    assert_eq!(control.move_data.unwrap().cmds.len(), 1);
}
