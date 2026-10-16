// SPDX-License-Identifier: AGPL-3.0-or-later
// Regression cases ported from tests/test_match_collision.py and test_match_navigation.py.
#[path = "../src/collision.rs"]
mod collision;
#[path = "../src/navigation.rs"]
mod navigation;

use collision::CollisionWorld;
use serde_json::{json, Value};
use navigation::Navigation;

fn room(obstacles: &[([f64; 3], [f64; 3])]) -> Value {
    let brushes: Vec<_> = obstacles.iter().map(|(lo, hi)| json!({
        "mins": lo, "maxs": hi, "first_side": 0, "side_count": 0,
        "axial_materials": [0,0,0,0,0,0], "contents": 1
    })).collect();
    json!({"brushes": brushes, "world_brushes": (0..brushes.len()).collect::<Vec<_>>(),
        "sides": [], "planes": [], "materials": [{"contents": 1}],
        "world_partitions": [], "static_models": [],
        "closure": {"frozen_world_ready": true, "blockers": []}})
}

#[test]
fn nearest_shot_and_early_visibility_keep_masks_and_hit_metadata() {
    let g = room(&[([120.,-50.,0.],[130.,50.,100.]), ([60.,-50.,0.],[70.,50.,100.])]);
    let mut world = CollisionWorld::new(&g).unwrap();
    let a = [0.,0.,40.];
    let b = [200.,0.,40.];
    let shot = world.trace_point(a,b,1,false).unwrap();
    assert_eq!(serde_json::to_value(&shot).unwrap(), json!({
        "hit": true, "fraction": 0.3, "position": [60.,0.,40.], "normal": [-1.,0.,0.],
        "kind": "brush", "index": 1, "material": 0, "start_solid": false,
        "complete": true, "contents_mask": 1, "unresolved_static_models": []
    }));
    assert_eq!(world.trace_point(a,b,1,true).unwrap().fraction, 0.6);
    assert!(!world.trace_point(a,b,2,true).unwrap().hit);
    assert!(!world.trace_point(a,[0.,200.,40.],1,true).unwrap().hit);
    assert_eq!(world.trace_point(a,b,1,false).unwrap().fraction, 0.3);
    assert!(world.trace_point([f64::NAN,0.,0.],b,1,false).is_err());
}

#[test]
fn box_contact_slides_and_small_negative_slope_time_does_not_tunnel() {
    let mut world = CollisionWorld::new(&room(&[([-1000.,-1000.,-100.],[1000.,1000.,0.])])).unwrap();
    let mins = [-15.,-15.,0.];
    let maxs = [15.,15.,70.];
    let t = world.trace_box([0.,0.,10.],[0.,0.,-10.],mins,maxs,0x2001001).unwrap();
    assert_eq!(t.position,[0.,0.,0.]);
    assert_eq!(t.normal,Some([0.,0.,1.]));
    assert!(!world.trace_box([0.,0.,0.],[10.,0.,0.],mins,maxs,0x2001001).unwrap().hit);
    assert!(world.trace_box([0.,0.,-1.],[10.,0.,-1.],mins,maxs,0x2001001).unwrap().start_solid);
    assert!(world.trace_box([0.;3],[1.;3],[0.;3],[0.;3],1).is_err());
    let g = json!({"materials":[{"contents":1}], "world_brushes":[],
        "vertices":[[701,817.533203125,-64],[406.75,844,-62],[1179.9996337890625,1084.26708984375,-64]],
        "triangles":[[0,1,2]],"partitions":[{"first_tri":0,"tri_count":1}],
        "world_partitions":[[0,0]],"closure":{"blockers":[]}});
    let mut slope = CollisionWorld::new(&g).unwrap();
    let a = [801.3170703001568,879.5982372168976,-63.689413269572164];
    let t = slope.trace_box(a,[798.3848270720862,878.8140310831764,-64.],mins,maxs,0x2001001).unwrap();
    assert!(t.hit && !t.start_solid);
    assert_eq!(t.fraction,0.);
    assert!(t.normal.unwrap()[2] > 0.99);
    assert!(!slope.trace_box(a,[a[0],a[1],a[2]+1.],mins,maxs,0x2001001).unwrap().hit);
}

fn floor(obstacles: &[([f64;3],[f64;3])]) -> Value {
    let mut boxes = vec![([-1000.,-1000.,-100.],[2000.,2000.,0.])];
    boxes.extend_from_slice(obstacles);
    room(&boxes)
}

#[test]
fn navigation_keeps_step_height_and_rejects_walls_and_low_ceilings() {
    let curb = ([80.,-100.,0.],[90.,100.,12.]);
    let cases = [
        (vec![curb],true),
        (vec![([80.,-100.,0.],[90.,100.,18.])],true),
        (vec![([80.,-100.,0.],[90.,100.,19.])],false),
        (vec![curb,([-100.,-100.,80.],[300.,100.,90.])],false),
        (vec![([-10.,-10.,0.],[10.,10.,20.])],false),
    ];
    for (obstacles,clear) in cases {
        let mut world = CollisionWorld::new(&floor(&obstacles)).unwrap();
        // A non-standing node leaves the direct-route seam isolated.
        let mut nav = Navigation::from_csv("1\n900 900 0,,crouch\n",&mut world).unwrap();
        let path = nav.route([0.;3],[200.,0.,0.],&mut world).unwrap();
        assert_eq!(path,if clear { vec![[200.,0.,0.]] } else { vec![] },"{obstacles:?}");
    }
}

#[test]
fn navigation_uses_strict_local_range_and_current_ground() {
    let mut world = CollisionWorld::new(&floor(&[])).unwrap();
    let mut nav = Navigation::from_csv("1\n900 900 0,,crouch\n",&mut world).unwrap();
    assert_eq!(nav.route([0.;3],[255.999,0.,0.],&mut world).unwrap(),vec![[255.999,0.,0.]]);
    assert!(nav.route([0.;3],[256.,0.,0.],&mut world).unwrap().is_empty());
    let text = "3\n0 0 -.5,1,stand,,,\n200 0 -.25,0,stand,,,\n400 0 0,1,stand,,,\n";
    let mut world = CollisionWorld::new(&floor(&[([390.,-20.,0.],[410.,20.,100.])])).unwrap();
    let nav = Navigation::from_csv(text,&mut world).unwrap();
    assert_eq!(nav.nodes[0].position,[0.,0.,0.125]);
    assert_eq!(nav.nodes[1].position,[200.,0.,0.125]);
    assert!(!nav.nodes[2].standing);
    for bad in ["0\n", "2\n0 0 0,,stand\n", "1\n0 0 0,1,stand\n", "1\nnan 0 0,,stand\n", "1\n0 0 0,\n"] {
        assert!(Navigation::from_csv(bad,&mut world).is_err(),"{bad}");
    }
}

#[test]
fn navigation_routes_around_cover_and_replanning_does_not_backtrack() {
    let csv = "4\n200 0 .125,1 3,stand,,,\n200 160 .125,0 2,stand,,,\n0 160 .125,1 3,stand,,,\n0 0 .125,0 2,stand,,,\n";
    let mut world = CollisionWorld::new(&floor(&[([80.,-100.,0.],[90.,100.,200.])])).unwrap();
    let mut nav = Navigation::from_csv(csv,&mut world).unwrap();
    let path = nav.route([200.,0.,0.],[0.;3],&mut world).unwrap();
    assert!(path.iter().any(|p| p[1] > 100.));
    assert_eq!(path.last(),Some(&[0.;3]));
    assert_eq!(nav.route([200.,0.,0.],[0.;3],&mut world).unwrap(),path);
    let path = nav.route([150.,160.,0.125],[0.;3],&mut world).unwrap();
    assert!(path[0][0] < 150.);
}

fn compare_json(actual: &Value, expected: &Value, context: &str) {
    match (actual,expected) {
        (Value::Number(a),Value::Number(b)) => {
            let (a,b) = (a.as_f64().unwrap(),b.as_f64().unwrap());
            // Permit only a few binary64 rounding steps; types, field presence,
            // indices, routes and hit semantics are checked separately below.
            let tolerance = 16. * f64::EPSILON * b.abs().max(1.);
            assert!((a-b).abs() <= tolerance,"{context}: {a:.17} != {b:.17}");
        }
        (Value::Array(a),Value::Array(b)) => {
            assert_eq!(a.len(),b.len(),"{context}");
            for (i,(a,b)) in a.iter().zip(b).enumerate() { compare_json(a,b,&format!("{context}[{i}]")); }
        }
        (Value::Object(a),Value::Object(b)) => {
            assert_eq!(a.keys().collect::<Vec<_>>(),b.keys().collect::<Vec<_>>(),"{context}");
            for (key,b) in b { compare_json(&a[key],b,&format!("{context}.{key}")); }
        }
        _ => assert_eq!(actual,expected,"{context}"),
    }
}

#[test]
fn synthetic_python_oracle_preserves_geometry_metadata_routes_and_cached_results() {
    let fixture: Value = serde_json::from_str(include_str!("fixtures/collision_navigation_python.json")).unwrap();
    let vector = |v: &Value| serde_json::from_value::<[f64;3]>(v.clone()).unwrap();
    for scene in fixture["scenes"].as_array().unwrap() {
        let name = scene["name"].as_str().unwrap();
        let mut world = CollisionWorld::new(&scene["geometry"]).unwrap();
        // Run both cold and warm queries through the same public API.
        for _ in 0..2 {
            for q in scene["queries"].as_array().unwrap() {
                let (a,b,mask) = (vector(&q["start"]),vector(&q["end"]),q["mask"].as_u64().unwrap() as u32);
                let trace = if q["kind"] == "point" {
                    world.trace_point(a,b,mask,q["any_hit"].as_bool().unwrap()).unwrap()
                } else {
                    world.trace_box(a,b,vector(&q["mins"]),vector(&q["maxs"]),mask).unwrap()
                };
                compare_json(&serde_json::to_value(trace).unwrap(),&q["expected"],name);
            }
        }
        if let Some(navigation) = scene.get("navigation") {
            let mut nav = Navigation::from_csv(navigation["csv"].as_str().unwrap(),&mut world).unwrap();
            for (node,expected) in nav.nodes.iter().zip(navigation["nodes"].as_array().unwrap()) {
                compare_json(&json!({"position":node.position,"links":node.links,"standing":node.standing}),expected,name);
            }
            for r in navigation["routes"].as_array().unwrap() {
                let route = nav.route(vector(&r["start"]),vector(&r["goal"]),&mut world).unwrap();
                compare_json(&serde_json::to_value(route).unwrap(),&r["expected"],name);
            }
        }
    }
}

#[test]
fn unresolved_models_are_reported_without_substituting_aabb_collision() {
    let mut g = room(&[]);
    g["static_models"] = json!([
        {"mins":[0,5,0],"maxs":[1,6,1],"geometry":null,"model_reference":1},
        {"mins":[4,4,0],"maxs":[6,6,1],"geometry":null,"model_reference":2}
    ]);
    g["closure"] = json!({"frozen_world_ready":false,"blockers":["missing geometry"]});
    let mut world = CollisionWorld::new(&g).unwrap();
    assert!(world.require_ready().unwrap_err().contains("missing geometry"));
    let point = world.trace_point([0.,0.,0.5],[10.,10.,0.5],1,false).unwrap();
    assert!(!point.hit && !point.complete);
    assert_eq!(point.unresolved_static_models,vec![1]);
    let volume = world.trace_box([0.,0.,0.5],[10.,10.,0.5],[-0.1;3],[0.1;3],1).unwrap();
    assert!(!volume.hit);
    assert_eq!(volume.unresolved_static_models,vec![1]);
}

#[test]
fn csv_quoted_fields_crlf_and_standing_kinds_follow_python() {
    let mut world = CollisionWorld::new(&floor(&[])).unwrap();
    let csv = "4\r\n\"0 0 0\",\"1\",stand,\"ignored,quoted\"\r\n100 0 0,0,grenade\r\n200 0 0,,claymore\r\n300 0 0,,javelin\r\n";
    let nav = Navigation::from_csv(csv,&mut world).unwrap();
    assert_eq!(nav.nodes.len(),4);
    assert!(nav.nodes.iter().all(|n| n.standing && n.position[2] == 0.125));
    let overlinked = format!("1\n0 0 0,{},stand\n",vec!["0";49].join(" "));
    assert!(Navigation::from_csv(&overlinked,&mut world).is_err());
}
