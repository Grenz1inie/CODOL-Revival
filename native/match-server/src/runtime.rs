// SPDX-License-Identifier: AGPL-3.0-or-later
//! Read the existing verified package without changing resource files or indices.
use std::{collections::BTreeMap, fs, path::Path, time::Instant};
use serde_json::{Value,json};
use sha2::{Digest,Sha256};
use crate::{collision::CollisionWorld,navigation::Navigation,protocol::{UserCmd,snapshot::baseline_entities},world::{World,Weapon,Spawn}};

type Result<T> = std::result::Result<T,String>;
pub struct Loaded { pub world:World, pub options:Value, pub map:String, pub checksum:u32 }

pub fn read_weapon(header:&[u8],index:u32)->Result<Weapon> {
    if header.len()!=0xe28 || !(1..=1022).contains(&index) {return Err("invalid current weapon header or index".into());}
    let integer=|o:usize|u32::from_le_bytes(header[o..o+4].try_into().unwrap());
    let real=|o:usize|f32::from_bits(integer(o)) as f64;
    if [0xd68,0xd69,0xd6a,0xdad].iter().any(|&o|header[o]!=0) || integer(0x6b0)!=0 {
        return Err("minimal rifle requires independent ammo and clip keys".into());
    }
    if [0xbb8,0xbbc,0xbc0,0xbc4,0xbd0,0xbd4,0xbd8,0xbdc].iter().any(|&o|integer(o)!=0) {
        return Err("multi-stage damage curve is outside the minimal loadout".into());
    }
    let w=Weapon{index,ammo_type:index,clip_type:index,clip_size:integer(0xd08),fire_ms:integer(0xd10),
        reload_ms:integer(0x71c),empty_reload_ms:integer(0x728),damage:integer(0x6dc),minimum_damage:integer(0xbc8),
        full_damage_range:real(0xbcc),minimum_damage_range:real(0xbe0)};
    if !(1..=511).contains(&w.clip_size) || [w.fire_ms,w.reload_ms,w.empty_reload_ms].iter().any(|v|!(1..=32767).contains(v))
        || w.minimum_damage==0 || w.minimum_damage>w.damage || w.damage>32767
        || !w.full_damage_range.is_finite() || !w.minimum_damage_range.is_finite()
        || w.full_damage_range<0. || w.full_damage_range>=w.minimum_damage_range {
        return Err("invalid rifle parameters".into());
    }
    Ok(w)
}
fn integer(v:&Value)->Result<u32> {v.as_u64().and_then(|n|n.try_into().ok()).ok_or_else(||"invalid package integer".into())}
fn text(v:&Value)->Result<&str> {v.as_str().ok_or_else(||"invalid package string".into())}

pub fn load_package(directory:&Path)->Result<Loaded> {
    let directory=directory.canonicalize().map_err(|e|e.to_string())?;
    let manifest:Value=serde_json::from_slice(&fs::read(directory.join("manifest.json")).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;
    if manifest["schema_version"]!=1 || manifest["format_version"]!=423 {return Err("unsupported map package version".into());}
    let map=text(&manifest["map"])?.to_owned();
    if !["mp_killhouse_sh","mp_nuked"].contains(&map.as_str()) || manifest["gametype"]!="dm" {return Err("only Killhouse or Nuketown DM is supported".into());}
    if manifest["physics_ready"]!=true {return Err("map collision is not ready".into());}
    let mut files=BTreeMap::<String,Vec<u8>>::new();
    for (name,expected) in manifest["files"].as_object().ok_or("missing package files")? {
        let path=directory.join(name).canonicalize().map_err(|e|e.to_string())?;
        if !path.starts_with(&directory) {return Err("map package path escapes directory".into());}
        let data=fs::read(path).map_err(|e|e.to_string())?;
        if expected["bytes"].as_u64()!=Some(data.len() as u64) || text(&expected["sha256"])?!=hex::encode(Sha256::digest(&data)) {
            return Err(format!("map package integrity mismatch: {name}"));
        }
        files.insert(name.clone(),data);
    }
    let data=|name:&str|files.get(name).map(Vec::as_slice).ok_or_else(||format!("missing package file: {name}"));
    let json_data=|name:&str|->Result<Value>{serde_json::from_slice(data(name)?).map_err(|e|e.to_string())};
    let baseline=data("baseline.bin")?;
    if baseline.len()<8 || &baseline[..8]!=b"IWCB000\x01" || (baseline.len()-8)%272!=0 || baseline.len()>190408 {
        return Err("invalid baseline header/length".into());
    }
    if manifest["baseline"]["count"].as_u64()!=Some(((baseline.len()-8)/272) as u64) {return Err("baseline count mismatch".into());}
    for state in baseline[8..].chunks_exact(272) {
        let number=i32::from_le_bytes(state[..4].try_into().unwrap());let kind=i32::from_le_bytes(state[4..8].try_into().unwrap());
        if !(0..=2048).contains(&number) || kind<0 {return Err("invalid baseline entity".into());}
    }
    let ncs=json_data("ncs.json")?;let loadout=json_data("loadout.json")?;
    for (key,kind) in [("weapon","13"),("body","0"),("hands","0")] {
        let item=&loadout[key];let row=&ncs["registry"]["kinds"][kind];
        let slot=row["strings"].as_array().ok_or("missing registry strings")?.iter().position(|s|s==&item["name"])
            .ok_or("loadout resource absent from current registry")? as u32+integer(&row["reserved"])?;
        if integer(&item["index"])?!=slot {return Err("loadout resource index differs from current registry".into());}
    }
    let mut collision=CollisionWorld::new(&json_data("geometry.json")?)?;
    let mut navigation=Navigation::from_csv(std::str::from_utf8(data("waypoints.csv")?).map_err(|e|e.to_string())?,&mut collision)?;
    let mut weapon=read_weapon(data(text(&loadout["weapon"]["header"])?)?,integer(&loadout["weapon"]["index"])?)?;
    let registry=&ncs["registry"]["kinds"]["13"];
    let composed=integer(&registry["reserved"])?+registry["strings"].as_array().ok_or("missing weapon registry")?.len() as u32;
    if composed>=integer(&registry["capacity"])? {return Err("no composed weapon slot after the stock registry".into());}
    weapon.index=composed;weapon.clip_type=composed;
    let spawns=json_data("spawns.json")?.as_array().ok_or("invalid spawn list")?.iter()
        .filter(|s|s["classname"]=="mp_dm_spawn").map(|s|serde_json::from_value::<Spawn>(s.clone()).map_err(|e|e.to_string())).collect::<Result<Vec<_>>>()?;
    let mut world=World::new(collision,spawns,weapon,integer(&loadout["body"]["index"])?,integer(&loadout["hands"]["index"])?,true)?;
    world.position_base=serde_json::from_value(json_data("position.json")?["position_base"].clone()).map_err(|e|e.to_string())?;
    world.static_entities=baseline_entities(baseline)?;
    world.bot_path=navigation.route(world.players[1].origin,world.players[0].origin,&mut world.collision)?;
    world.bot_repath_at=world.time+500;world.navigation=Some(navigation);
    let checksum=integer(&ncs["registry"]["checksum"])?;
    let options=json!({"netconst_checksum":checksum,"configstrings":[],"aliases":[],
        "recipes":[[integer(&registry["base"])?+world.weapon.index,world.weapon.ammo_type,0,0,[1690,2683,2385,9641,13370]]],
        "position_base":world.position_base,"map_name":map});
    Ok(Loaded {world,options,map,checksum})
}

pub fn replay(directory:&Path,input:&Path)->Result<Value> {
    let start=Instant::now();let mut loaded=load_package(directory)?;
    let startup=start.elapsed().as_secs_f64()*1000.;
    let inputs:Value=serde_json::from_slice(&fs::read(input).map_err(|e|e.to_string())?).map_err(|e|e.to_string())?;
    let mut states=Vec::new();let mut steps=Vec::new();let mut snapshots=Vec::new();let mut frames=Vec::new();
    for frame in inputs["frames"].as_array().ok_or("missing replay frames")? {
        let commands:Vec<UserCmd>=serde_json::from_value(frame["commands"].clone()).map_err(|e|e.to_string())?;
        let begin=Instant::now();loaded.world.step(&commands,integer(&frame["milliseconds"])?)?;
        let simulated=Instant::now();let (wire,fields)=loaded.world.snapshot()?;let end=Instant::now();
        steps.push((simulated-begin).as_secs_f64()*1000.);snapshots.push((end-simulated).as_secs_f64()*1000.);
        frames.push((end-begin).as_secs_f64()*1000.);
        states.push(json!({"time":loaded.world.time,"players":loaded.world.players,"fields":fields,"wire":hex::encode(wire)}));
    }
    Ok(json!({"engine":"rust","startup_ms":startup,"states":states,"step_ms":steps,"snapshot_ms":snapshots,"frame_ms":frames}))
}
