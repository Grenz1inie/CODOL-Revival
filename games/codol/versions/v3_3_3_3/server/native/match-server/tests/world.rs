use codol_match::{collision::CollisionWorld, world::{World, Weapon, Spawn}};
use std::collections::BTreeMap;
use serde_json::json;

fn world(bot: bool, wall: bool) -> World {
    let mut brushes = vec![json!({"mins":[-1000,-1000,-100],"maxs":[1000,1000,0],
        "first_side":0,"side_count":0,"axial_materials":[0,0,0,0,0,0],"contents":1})];
    if wall { brushes.push(json!({"mins":[100,-1000,0],"maxs":[110,1000,200],
        "first_side":0,"side_count":0,"axial_materials":[0,0,0,0,0,0],"contents":1})); }
    let geometry = json!({"planes":[],"sides":[],"materials":[{"contents":1}],
        "world_brushes":(0..brushes.len()).collect::<Vec<_>>(),"brushes":brushes,
        "vertices":[],"triangles":[],"partitions":[],"world_partitions":[],
        "static_models":[],"closure":{"blockers":[]}});
    World::new(CollisionWorld::new(&geometry).unwrap(),
        vec![Spawn {origin:[0.,0.,40.],angles:[0.,0.,0.]},Spawn {origin:[200.,0.,40.],angles:[0.,180.,0.]}],
        Weapon {index:5,ammo_type:5,clip_type:5,clip_size:36,fire_ms:90,reload_ms:2000,
            empty_reload_ms:2500,damage:30,minimum_damage:22,full_damage_range:1500.,minimum_damage_range:1501.},
        104,48,bot).unwrap()
}
fn cmd(time:u32,direction:u32,buttons:u32)->BTreeMap<String,u32> {
    [("time",time),("direction",direction),("buttons",buttons),("yaw",0),("pitch",0),("weapon",5)]
        .into_iter().map(|(k,v)|(k.into(),v)).collect()
}

#[test]
fn wall_slide_and_input_replay_do_not_teleport() {
    let mut w=world(false,true);
    for _ in 0..30 { w.step(&[cmd(w.time+50,5,0)],50).unwrap(); }
    let p=&w.players[0];
    assert!(p.origin[0]>80. && p.origin[0]<=85.01);
    assert!(p.origin[1]< -100. && p.origin[2].abs()<1e-4);
    let position=p.origin;
    w.step(&[cmd(w.players[0].command_time,1,0),cmd(w.time+20051,1,0)],50).unwrap();
    assert_eq!(w.players[0].origin,position);
}
#[test]
fn ahead_input_clamps_but_keeps_fire_and_rejects_duplicate_raw_time() {
    let mut w=world(false,false);
    w.step(&[cmd(1800,1,1)],50).unwrap();
    assert_eq!(w.players[0].command_time,1250);
    assert_eq!(w.players[0].clip,35);
    let origin=w.players[0].origin;
    w.step(&[cmd(1800,1,1)],50).unwrap();
    assert_eq!(w.players[0].origin,origin);
    w.step(&[cmd(1850,1,1)],50).unwrap();
    assert_eq!((w.players[0].command_time,w.players[0].clip),(1350,34));
}
#[test]
fn jump_lands_and_elapsed_time_is_not_dropped() {
    let mut w=world(false,false);
    w.step(&[cmd(1050,0,1024)],50).unwrap();
    assert!(w.players[0].origin[2]>0.);
    for _ in 0..30 { w.step(&[cmd(w.time+50,0,0)],50).unwrap(); }
    assert!(w.players[0].origin[2].abs()<0.001);
    let now=w.time;
    w.step(&[],175).unwrap();
    assert_eq!(w.time,now+175);
    assert!(w.step(&[],0).is_err());
}
#[test]
fn fire_rate_damage_death_respawn_and_occlusion_match_existing_rules() {
    let mut w=world(false,false);
    for _ in 0..7 { w.step(&[cmd(w.time+50,0,1)],50).unwrap(); }
    assert_eq!((w.players[0].clip,w.players[1].health,w.players[0].kills),(32,0,1));
    let delay=w.players[1].respawn_at-w.time;
    w.step(&[],delay-1).unwrap(); assert_eq!(w.players[1].health,0);
    w.step(&[],1).unwrap(); assert_eq!(w.players[1].health,100);
    assert_eq!(w.players[1].spawn_count,2);
    let mut blocked=world(false,true);
    for _ in 0..10 { blocked.step(&[cmd(blocked.time+50,0,1)],50).unwrap(); }
    assert_eq!(blocked.players[1].health,100);
}
#[test]
fn reload_conserves_ammo_and_ai_uses_same_damage_path() {
    let mut w=world(false,false);
    w.players[0].clip=1;
    w.step(&[cmd(1050,0,1)],50).unwrap();
    w.step(&[cmd(1100,0,16)],50).unwrap();
    for _ in 0..10 { w.step(&[cmd(w.time+50,0,1)],50).unwrap(); }
    assert_eq!(w.players[0].clip,0);
    w.step(&[],w.players[0].reload_at-w.time).unwrap();
    assert_eq!((w.players[0].clip,w.players[0].reserve),(36,72));
    let mut w=world(true,false);
    for _ in 0..70 { w.step(&[],50).unwrap(); if w.players[0].health==0 {break;} }
    assert_eq!(w.players[0].health,0);
    assert_eq!(w.players[1].kills,1);
}
