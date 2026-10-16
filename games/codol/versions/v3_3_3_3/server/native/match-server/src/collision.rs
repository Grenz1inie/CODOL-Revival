// SPDX-License-Identifier: AGPL-3.0-or-later
// Port of src/match_server/collision.py (CODOL-Revival).
// Analytical, two-sided frozen-world queries; missing models remain unresolved.
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::{HashMap, HashSet};

pub type Vec3 = [f64; 3];
pub const PLAYER_MINS: Vec3 = [-15.0, -15.0, 0.0];
pub const PLAYER_MAXS: Vec3 = [15.0, 15.0, 70.0];
pub const PLAYER_MASK: u32 = 0x2001001;
const AXES: [Vec3; 3] = [[1.,0.,0.], [0.,1.,0.], [0.,0.,1.]];

#[derive(Clone, Debug, Serialize)]
pub struct Trace {
    pub hit: bool,
    pub fraction: f64,
    pub position: Vec3,
    pub normal: Option<Vec3>,
    pub kind: Option<&'static str>,
    pub index: Option<usize>,
    pub material: Option<usize>,
    pub start_solid: bool,
    pub complete: bool,
    pub contents_mask: u32,
    pub unresolved_static_models: Vec<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub submodel: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub entity_number: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub surface: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub triangle: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model_reference: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub surface_flags: Option<u32>,
}

#[derive(Clone, Default)]
struct Metadata {
    kind: &'static str,
    index: usize,
    material: Option<usize>,
    placement: Option<(usize, usize)>,
    surface: Option<usize>,
    triangle: Option<usize>,
    model_reference: Option<Value>,
    surface_flags: Option<u32>,
}

impl Trace {
    fn empty(end: Vec3, complete: bool, contents_mask: u32) -> Self {
        Self { hit: false, fraction: 1., position: end, normal: None, kind: None,
            index: None, material: None, start_solid: false, complete, contents_mask,
            unresolved_static_models: Vec::new(), submodel: None, entity_number: None,
            surface: None, triangle: None, model_reference: None, surface_flags: None }
    }

    fn consider(&mut self, start: Vec3, end: Vec3, contact: Contact, meta: &Metadata) {
        let (t, normal, inside) = contact;
        if !self.hit || t < self.fraction {
            self.hit = true;
            self.fraction = t;
            self.position = std::array::from_fn(|i| start[i] + t * (end[i] - start[i]));
            self.normal = normal;
            self.kind = Some(meta.kind);
            self.index = Some(meta.index);
            self.material = meta.material;
            // Replace every optional field, including fields absent on the new hit.
            self.submodel = meta.placement.map(|p| p.0);
            self.entity_number = meta.placement.map(|p| p.1);
            self.surface = meta.surface;
            self.triangle = meta.triangle;
            self.model_reference = meta.model_reference.clone();
            self.surface_flags = meta.surface_flags;
        }
        self.start_solid |= inside;
    }
}

// Python 3.12+ sum(float) uses Neumaier compensation. Products are rounded
// before summation (this is deliberately not a fused multiply/add dot product).
fn sum(values: impl IntoIterator<Item = f64>) -> f64 {
    let (mut s, mut correction) = (0.0_f64, 0.0_f64);
    for x in values {
        let t = s + x;
        correction += if s.abs() >= x.abs() { (s - t) + x } else { (x - t) + s };
        s = t;
    }
    if correction != 0. && correction.is_finite() { s + correction } else { s }
}
fn dot(a: Vec3, b: Vec3) -> f64 { sum((0..3).map(|i| a[i] * b[i])) }
fn sub(a: Vec3, b: Vec3) -> Vec3 { std::array::from_fn(|i| a[i] - b[i]) }
fn add(a: Vec3, b: Vec3) -> Vec3 { std::array::from_fn(|i| a[i] + b[i]) }
fn cross(a: Vec3, b: Vec3) -> Vec3 {
    [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
}
fn finite(v: Vec3) -> bool { v.iter().all(|x| x.is_finite()) }

#[derive(Clone, Copy)]
struct Bounds { lo: Vec3, hi: Vec3 }
impl Bounds {
    fn overlaps(self, other: Self) -> bool {
        (0..3).all(|i| self.hi[i] >= other.lo[i] && self.lo[i] <= other.hi[i])
    }
    fn segment(self, start: Vec3, end: Vec3, half: Vec3) -> bool {
        let (mut near, mut far) = (0.0_f64, 1.0_f64);
        for i in 0..3 {
            let lo = self.lo[i] - half[i] - 1e-8;
            let hi = self.hi[i] + half[i] + 1e-8;
            let delta = end[i] - start[i];
            if delta == 0. {
                if start[i] < lo || start[i] > hi { return false; }
                continue;
            }
            let a = (lo - start[i]) / delta;
            let b = (hi - start[i]) / delta;
            near = near.max(a.min(b));
            far = far.min(a.max(b));
            if near > far { return false; }
        }
        true
    }
    fn vertices(vertices: &[Vec3]) -> Self {
        Self {
            lo: std::array::from_fn(|i| vertices.iter().map(|v| v[i]).fold(f64::INFINITY, f64::min)),
            hi: std::array::from_fn(|i| vertices.iter().map(|v| v[i]).fold(f64::NEG_INFINITY, f64::max)),
        }
    }
}

// Median-split BVH; stable keys are sorted after querying, preserving Python's
// brush/terrain/instance order and simultaneous-contact tie breaks.
struct SpatialIndex { root: Option<Box<SpatialNode>> }
struct SpatialNode { bounds: Bounds, body: SpatialBody }
enum SpatialBody {
    Leaf(Vec<(Bounds, (usize, usize))>),
    Branch(Box<SpatialNode>, Box<SpatialNode>),
}
impl SpatialIndex {
    fn new(entries: Vec<(Bounds, (usize, usize))>) -> Self {
        fn build(mut rows: Vec<(Bounds, (usize, usize))>) -> Box<SpatialNode> {
            let bounds = Bounds {
                lo: std::array::from_fn(|i| rows.iter().map(|r| r.0.lo[i]).fold(f64::INFINITY,f64::min)),
                hi: std::array::from_fn(|i| rows.iter().map(|r| r.0.hi[i]).fold(f64::NEG_INFINITY,f64::max)),
            };
            let body = if rows.len() <= 8 { SpatialBody::Leaf(rows) } else {
                let spread: Vec3 = std::array::from_fn(|i| {
                    let values = || rows.iter().map(|r| r.0.lo[i] + r.0.hi[i]);
                    values().fold(f64::NEG_INFINITY,f64::max) - values().fold(f64::INFINITY,f64::min)
                });
                let mut axis = 0;
                for i in 1..3 { if spread[i] > spread[axis] { axis = i; } }
                rows.sort_by(|a,b| (a.0.lo[axis]+a.0.hi[axis]).total_cmp(&(b.0.lo[axis]+b.0.hi[axis])));
                let right = rows.split_off(rows.len()/2);
                SpatialBody::Branch(build(rows),build(right))
            };
            Box::new(SpatialNode { bounds, body })
        }
        Self { root: if entries.is_empty() { None } else { Some(build(entries)) } }
    }
    fn query(&self, bounds: Bounds) -> Vec<(usize,usize)> {
        let mut result = Vec::new();
        let mut stack = Vec::new();
        if let Some(root) = &self.root { stack.push(root.as_ref()); }
        while let Some(node) = stack.pop() {
            if !node.bounds.overlaps(bounds) { continue; }
            match &node.body {
                SpatialBody::Leaf(rows) => result.extend(rows.iter().filter(|r| r.0.overlaps(bounds)).map(|r| r.1)),
                SpatialBody::Branch(left,right) => { stack.push(left); stack.push(right); }
            }
        }
        result.sort_unstable();
        result
    }
}

#[derive(Deserialize, Default)]
#[serde(default)]
struct Geometry {
    closure: Closure,
    brushes: Vec<SourceBrush>, planes: Vec<[f64;4]>, sides: Vec<Side>,
    materials: Vec<Material>, world_brushes: Vec<usize>,
    vertices: Vec<Vec3>, triangles: Vec<[usize;3]>, partitions: Vec<Partition>,
    world_partitions: Vec<[usize;2]>, submodels: Vec<Submodel>,
    submodel_instances: Vec<Placement>, static_models: Vec<StaticInstance>,
    xmodels: HashMap<String, XModel>,
}
#[derive(Deserialize, Default)]
struct Closure {
    #[serde(default)] frozen_world_ready: bool,
    #[serde(default)] blockers: Vec<String>,
}
#[derive(Deserialize)]
struct SourceBrush { mins: Vec3, maxs: Vec3, first_side: usize, side_count: usize, axial_materials: [usize;6], contents: u32 }
#[derive(Deserialize)]
struct Side { plane: usize, material: usize }
#[derive(Deserialize)]
struct Material { contents: u32 }
#[derive(Deserialize)]
struct Partition { first_tri: usize, tri_count: usize }
#[derive(Deserialize, Default)]
#[serde(default)]
struct Submodel { brushes: Vec<usize>, partitions: Vec<[usize;2]> }
#[derive(Deserialize)]
struct Placement { submodel: usize, entity_number: usize, origin: Vec3, angles: Vec3 }
#[derive(Deserialize)]
struct StaticInstance {
    mins: Vec3, maxs: Vec3, geometry: Option<String>,
    #[serde(default)] origin: Vec3,
    #[serde(default)] inverse_scaled_axis: [f64;9],
    model_reference: Value,
}
#[derive(Deserialize)]
struct XModel { surfaces: Vec<Surface> }
#[derive(Deserialize)]
struct Surface { contents: u32, surface_flags: u32, triangles: Vec<[Vec3;3]> }

#[derive(Clone, Copy)]
struct Plane { normal: Vec3, dist: f64, material: usize }
#[derive(Clone, Copy)]
struct Projection { axis: Vec3, lo: f64, hi: f64 }
type Contact = (f64, Option<Vec3>, bool);
struct Brush { bounds: Bounds, contents: u32, planes: Vec<Plane>, meta: Metadata, axes: Option<Vec<Projection>> }
struct Triangle { bounds: Bounds, a: Vec3, e1: Vec3, e2: Vec3, normal: Vec3, contents: u32, meta: Metadata, axes: Option<Vec<Projection>> }
struct StaticCache { triangles: Vec<Triangle>, spatial: SpatialIndex }
struct StaticModel { source: StaticInstance, cache: Option<StaticCache> }

fn at<'a, T>(values: &'a [T], index: usize, name: &str) -> Result<&'a T, String> {
    values.get(index).ok_or_else(|| format!("invalid {name} index {index}"))
}

fn placement_axis(angles: Vec3) -> [Vec3;3] {
    let [pitch,yaw,roll] = angles.map(|v| v * (std::f64::consts::PI / 180.));
    let (cp,sp,cy,sy,cr,sr) = (pitch.cos(),pitch.sin(),yaw.cos(),yaw.sin(),roll.cos(),roll.sin());
    [[cp*cy,cp*sy,-sp], [sr*sp*cy-sy*cr,sr*sp*sy+cr*cy,sr*cp],
        [cr*sp*cy+sr*sy,cr*sp*sy-sr*cy,cr*cp]]
}
fn transform(v: Vec3, axis: [Vec3;3]) -> Vec3 {
    std::array::from_fn(|i| sum((0..3).map(|j| v[j]*axis[j][i])))
}
fn brush_planes(g: &Geometry, b: &SourceBrush) -> Result<Vec<Plane>,String> {
    let mut planes = Vec::new();
    for sign in [-1.,1.] {
        for i in 0..3 {
            let mut normal = [0.;3]; normal[i] = sign;
            planes.push(Plane { normal, dist: if sign == -1. { -b.mins[i] } else { b.maxs[i] },
                material: b.axial_materials[if sign == -1. { i } else { 3+i }] });
        }
    }
    for i in b.first_side..b.first_side.checked_add(b.side_count).ok_or("brush side range overflow")? {
        let side = at(&g.sides,i,"side")?;
        let p = at(&g.planes,side.plane,"plane")?;
        planes.push(Plane { normal: [p[0],p[1],p[2]], dist: p[3], material: side.material });
    }
    Ok(planes)
}
impl Triangle {
    fn new([a,b,c]: [Vec3;3], contents: u32, meta: Metadata) -> Option<Self> {
        let (e1,e2) = (sub(b,a),sub(c,a));
        let n = cross(e1,e2);
        let length = dot(n,n).sqrt();
        if length == 0. { return None; }
        Some(Self { bounds: Bounds::vertices(&[a,b,c]), a,e1,e2,normal: n.map(|v| v/length), contents,meta,axes: None })
    }
    fn point(&self, start: Vec3, end: Vec3) -> Option<Contact> {
        let direction = sub(end,start);
        let p = cross(direction,self.e2);
        let det = dot(self.e1,p);
        if det.abs() < 1e-10 { return None; }
        let delta = sub(start,self.a);
        let u = dot(delta,p)/det;
        let q = cross(delta,self.e1);
        let v = dot(direction,q)/det;
        if u < -1e-9 || v < -1e-9 || u+v > 1.+1e-9 { return None; }
        let t = dot(self.e2,q)/det;
        if (0. ..=1.).contains(&t) {
            Some((t,Some(if dot(self.normal,direction) <= 0. { self.normal } else { self.normal.map(|x| -x) }),false))
        } else { None }
    }
    fn box_contact(&mut self, start: Vec3, end: Vec3, half: Vec3) -> Option<Contact> {
        let axes = self.axes.get_or_insert_with(|| {
            let vertices = [self.a,add(self.a,self.e1),add(self.a,self.e2)];
            let mut axes = AXES.to_vec(); axes.push(self.normal);
            for edge in [self.e1,self.e2,sub(self.e2,self.e1)] {
                for axis in AXES { axes.push(cross(edge,axis)); }
            }
            projections(&vertices,axes)
        });
        sweep(start,end,half,axes)
    }
}

fn projections(vertices: &[Vec3], axes: Vec<Vec3>) -> Vec<Projection> {
    let mut result = Vec::new();
    let mut seen = HashSet::new();
    for axis in axes {
        let length = dot(axis,axis).sqrt();
        if length < 1e-10 { continue; }
        let normal = axis.map(|x| x/length);
        // Python round(x,10) rounds the exact binary value to a decimal. Formatting
        // avoids the extra rounding of (x * 1e10).round(), including halfway cases.
        let key: [i64;3] = normal.map(|v| {
            let decimal = format!("{v:.10}");
            decimal.replace('.', "").parse().expect("finite normalized axis")
        });
        if seen.contains(&key) || seen.contains(&key.map(|x| -x)) { continue; }
        seen.insert(key);
        let values = || vertices.iter().map(|v| dot(normal,*v));
        result.push(Projection { axis: normal, lo: values().fold(f64::INFINITY,f64::min),
            hi: values().fold(f64::NEG_INFINITY,f64::max) });
    }
    result
}
fn brush_projections(planes: &[Plane]) -> Result<Vec<Projection>,String> {
    let mut vertices = Vec::new();
    for i in 0..planes.len() {
        for j in i+1..planes.len() {
            for k in j+1..planes.len() {
                let (a,b,c) = (planes[i],planes[j],planes[k]);
                let bc = cross(b.normal,c.normal);
                let det = dot(a.normal,bc);
                if det.abs() < 1e-10 { continue; }
                let (ca,ab) = (cross(c.normal,a.normal),cross(a.normal,b.normal));
                let v = std::array::from_fn(|axis| (a.dist*bc[axis]+b.dist*ca[axis]+c.dist*ab[axis])/det);
                if planes.iter().all(|p| dot(p.normal,v) <= p.dist+1e-5) { vertices.push(v); }
            }
        }
    }
    if vertices.len() < 4 { return Err("brush halfspaces do not form a bounded convex solid".into()); }
    let mut axes = AXES.to_vec(); axes.extend(planes.iter().map(|p| p.normal));
    for i in 0..planes.len() {
        for j in i+1..planes.len() {
            for axis in AXES { axes.push(cross(cross(planes[i].normal,planes[j].normal),axis)); }
        }
    }
    Ok(projections(&vertices,axes))
}
fn sweep(start: Vec3, end: Vec3, half: Vec3, projections: &[Projection]) -> Option<Contact> {
    let (mut enter,mut leave,mut normal,mut inside) = (f64::NEG_INFINITY,1.0_f64,None,true);
    for p in projections {
        let radius = sum((0..3).map(|i| p.axis[i].abs()*half[i]));
        let (lo,hi) = (p.lo-radius,p.hi+radius);
        let (a,b) = (dot(p.axis,start),dot(p.axis,end));
        inside &= lo+1e-8 < a && a < hi-1e-8;
        let speed = b-a;
        if speed.abs() < 1e-12 {
            if a <= lo+1e-8 || a >= hi-1e-8 { return None; }
            continue;
        }
        let (mut t0,mut t1) = ((lo-a)/speed,(hi-a)/speed);
        let n = if speed > 0. { p.axis.map(|v| -v) } else { p.axis };
        if t0 > t1 { std::mem::swap(&mut t0,&mut t1); }
        if t0 >= enter { enter = t0; normal = Some(n); }
        leave = leave.min(t1);
        if enter > leave || leave < 0. { return None; }
    }
    if inside { return Some((0.,None,true)); }
    if normal.is_some() && (-1e-8..=1.).contains(&enter) && leave >= enter {
        return Some((enter.max(0.),normal,false));
    }
    None
}

pub struct CollisionWorld {
    pub complete: bool,
    blockers: Vec<String>,
    brushes: Vec<Brush>,
    triangles: Vec<Triangle>,
    static_models: Vec<StaticModel>,
    xmodels: HashMap<String,XModel>,
    spatial: SpatialIndex,
}

impl CollisionWorld {
    pub fn new(geometry: &Value) -> Result<Self,String> {
        // Deserialize once; all hot query paths use typed geometry and cached SAT.
        let g: Geometry = serde_json::from_value(geometry.clone()).map_err(|e| e.to_string())?;
        let mut brushes = Vec::new();
        let mut triangles = Vec::new();
        let add_brush = |index: usize, placement: Option<&Placement>, brushes: &mut Vec<Brush>| -> Result<(),String> {
            let source = at(&g.brushes,index,"brush")?;
            let mut planes = brush_planes(&g,source)?;
            let mut bounds = Bounds { lo: source.mins, hi: source.maxs };
            if let Some(p) = placement {
                let axis = placement_axis(p.angles);
                for plane in &mut planes {
                    plane.normal = transform(plane.normal,axis);
                    plane.dist += dot(plane.normal,p.origin);
                }
                let mut corners = Vec::new();
                for x in [source.mins[0],source.maxs[0]] {
                    for y in [source.mins[1],source.maxs[1]] {
                        for z in [source.mins[2],source.maxs[2]] { corners.push(add(transform([x,y,z],axis),p.origin)); }
                    }
                }
                bounds = Bounds::vertices(&corners);
            }
            brushes.push(Brush { bounds,contents: source.contents,planes,axes: None,
                meta: Metadata { kind: if placement.is_some() { "submodel_brush" } else { "brush" },
                    index,placement: placement.map(|p| (p.submodel,p.entity_number)), ..Metadata::default() } });
            Ok(())
        };
        let add_partition = |[partition,material]: [usize;2], placement: Option<&Placement>, triangles: &mut Vec<Triangle>| -> Result<(),String> {
            let part = at(&g.partitions,partition,"partition")?;
            let contents = at(&g.materials,material,"material")?.contents;
            for index in part.first_tri..part.first_tri.checked_add(part.tri_count).ok_or("triangle range overflow")? {
                let indices = at(&g.triangles,index,"triangle")?;
                let mut vertices = [*at(&g.vertices,indices[0],"vertex")?,*at(&g.vertices,indices[1],"vertex")?,*at(&g.vertices,indices[2],"vertex")?];
                if let Some(p) = placement {
                    let axis = placement_axis(p.angles);
                    vertices = vertices.map(|v| add(transform(v,axis),p.origin));
                }
                let meta = Metadata { kind: if placement.is_some() { "submodel_triangle" } else { "triangle" },
                    index,material: Some(material),placement: placement.map(|p| (p.submodel,p.entity_number)), ..Metadata::default() };
                if let Some(t) = Triangle::new(vertices,contents,meta) { triangles.push(t); }
            }
            Ok(())
        };
        for &index in &g.world_brushes { add_brush(index,None,&mut brushes)?; }
        for &part in &g.world_partitions { add_partition(part,None,&mut triangles)?; }
        for p in &g.submodel_instances {
            let model = at(&g.submodels,p.submodel,"submodel")?;
            for &index in &model.brushes { add_brush(index,Some(p),&mut brushes)?; }
            for &part in &model.partitions { add_partition(part,Some(p),&mut triangles)?; }
        }
        let static_models: Vec<_> = g.static_models.into_iter().map(|source| StaticModel { source,cache: None }).collect();
        let mut entries = Vec::new();
        entries.extend(brushes.iter().enumerate().map(|(i,b)| (b.bounds,(0,i))));
        entries.extend(triangles.iter().enumerate().map(|(i,t)| (t.bounds,(1,i))));
        entries.extend(static_models.iter().enumerate().map(|(i,m)| (Bounds { lo:m.source.mins,hi:m.source.maxs },(2,i))));
        Ok(Self { complete: g.closure.frozen_world_ready && g.closure.blockers.is_empty(),
            blockers: g.closure.blockers,brushes,triangles,static_models,xmodels:g.xmodels,spatial:SpatialIndex::new(entries) })
    }

    pub fn require_ready(&self) -> Result<(),String> {
        if self.complete { Ok(()) } else { Err(format!("collision world incomplete: {}",self.blockers.join("; "))) }
    }

    fn prepare_static(&mut self, index: usize) -> Result<(),String> {
        let instance = &mut self.static_models[index];
        if instance.cache.is_some() { return Ok(()); }
        let source = &instance.source;
        let key = source.geometry.as_ref().ok_or("unresolved static model")?;
        let model = self.xmodels.get(key).ok_or_else(|| format!("missing xmodel {key}"))?;
        let axis = source.inverse_scaled_axis;
        let (a,b,c) = ([axis[0],axis[3],axis[6]],[axis[1],axis[4],axis[7]],[axis[2],axis[5],axis[8]]);
        let (bc,ca,ab) = (cross(b,c),cross(c,a),cross(a,b));
        let det = dot(a,bc);
        let mut triangles = Vec::new();
        for (si,surface) in model.surfaces.iter().enumerate() {
            for (ti,vertices) in surface.triangles.iter().enumerate() {
                if det.abs() < 1e-20 { return Err("singular static model transform".into()); }
                let vertices = vertices.map(|p| std::array::from_fn(|i| source.origin[i]+(p[0]*bc[i]+p[1]*ca[i]+p[2]*ab[i])/det));
                let meta = Metadata { kind: "static_model",index,surface:Some(si),triangle:Some(ti),
                    model_reference:Some(source.model_reference.clone()),surface_flags:Some(surface.surface_flags), ..Metadata::default() };
                if let Some(t) = Triangle::new(vertices,surface.contents,meta) { triangles.push(t); }
            }
        }
        let spatial = SpatialIndex::new(triangles.iter().enumerate().map(|(i,t)| (t.bounds,(0,i))).collect());
        instance.cache = Some(StaticCache { triangles,spatial });
        Ok(())
    }

    fn unresolved(&self, candidates: &[(usize,usize)], start: Vec3, end: Vec3, half: Vec3) -> Vec<usize> {
        candidates.iter().filter_map(|&(kind,i)| {
            if kind != 2 { return None; }
            let m = &self.static_models[i].source;
            (m.geometry.is_none() && (Bounds { lo:m.mins,hi:m.maxs }).segment(start,end,half)).then_some(i)
        }).collect()
    }

    pub fn trace_point(&mut self, start: Vec3, end: Vec3, contents_mask: u32, any_hit: bool) -> Result<Trace,String> {
        if !finite(start) || !finite(end) { return Err("point trace requires finite vectors".into()); }
        let bounds = Bounds::vertices(&[start,end]);
        let candidates = self.spatial.query(bounds);
        let mut result = Trace::empty(end,self.complete,contents_mask);
        result.unresolved_static_models = self.unresolved(&candidates,start,end,[0.;3]);
        for (kind,slot) in candidates {
            match kind {
                0 => {
                    let brush = &self.brushes[slot];
                    if brush.contents & contents_mask == 0 || !brush.bounds.segment(start,end,[0.;3]) { continue; }
                    let (mut enter,mut leave,mut normal,mut material) = (0.0_f64,1.0_f64,None,None);
                    let (mut inside,mut intersects) = (true,true);
                    for p in &brush.planes {
                        let (a,b) = (dot(p.normal,start)-p.dist,dot(p.normal,end)-p.dist);
                        inside &= a < 0.;
                        if a > 0. && b > 0. { intersects = false; break; }
                        if a == 0. && b < 0. && enter == 0. { normal = Some(p.normal); material = Some(p.material); }
                        if a <= 0. && b <= 0. { continue; }
                        let t = a/(a-b);
                        if a > b {
                            if t >= enter { enter = t; normal = Some(p.normal); material = Some(p.material); }
                        } else { leave = leave.min(t); }
                        if enter > leave { intersects = false; break; }
                    }
                    if intersects && (inside || normal.is_some()) {
                        let mut meta = brush.meta.clone(); meta.material = material;
                        result.consider(start,end,(if inside { 0. } else { enter },normal,inside),&meta);
                        if any_hit { return Ok(result); }
                    }
                }
                1 => {
                    let t = &self.triangles[slot];
                    if t.contents & contents_mask != 0 && t.bounds.segment(start,end,[0.;3]) {
                        if let Some(contact) = t.point(start,end) {
                            result.consider(start,end,contact,&t.meta);
                            if any_hit { return Ok(result); }
                        }
                    }
                }
                _ => {
                    let m = &self.static_models[slot].source;
                    if m.geometry.is_none() || !(Bounds { lo:m.mins,hi:m.maxs }).segment(start,end,[0.;3]) { continue; }
                    self.prepare_static(slot)?;
                    let cache = self.static_models[slot].cache.as_ref().unwrap();
                    for (_,i) in cache.spatial.query(bounds) {
                        let t = &cache.triangles[i];
                        if t.contents & contents_mask != 0 && t.bounds.segment(start,end,[0.;3]) {
                            if let Some(contact) = t.point(start,end) {
                                result.consider(start,end,contact,&t.meta);
                                if any_hit { return Ok(result); }
                            }
                        }
                    }
                }
            }
        }
        Ok(result)
    }

    pub fn trace_box(&mut self, start: Vec3, end: Vec3, mins: Vec3, maxs: Vec3, contents_mask: u32) -> Result<Trace,String> {
        if ![start,end,mins,maxs].into_iter().all(finite) { return Err("box trace requires finite vectors".into()); }
        if (0..3).any(|i| mins[i] >= maxs[i]) { return Err("box extents must have positive volume".into()); }
        let half = std::array::from_fn(|i| (maxs[i]-mins[i])/2.);
        let offset = std::array::from_fn(|i| (mins[i]+maxs[i])/2.);
        let (a,b) = (add(start,offset),add(end,offset));
        let bounds = Bounds { lo:std::array::from_fn(|i| start[i].min(end[i])+mins[i]),
            hi:std::array::from_fn(|i| start[i].max(end[i])+maxs[i]) };
        let candidates = self.spatial.query(bounds);
        let mut result = Trace::empty(end,self.complete,contents_mask);
        result.unresolved_static_models = self.unresolved(&candidates,a,b,half);
        for (kind,slot) in candidates {
            match kind {
                0 => {
                    let brush = &mut self.brushes[slot];
                    if brush.contents & contents_mask == 0 || !brush.bounds.segment(a,b,half) { continue; }
                    if brush.axes.is_none() { brush.axes = Some(brush_projections(&brush.planes)?); }
                    if let Some(contact) = sweep(a,b,half,brush.axes.as_ref().unwrap()) {
                        result.consider(start,end,contact,&brush.meta);
                    }
                }
                1 => {
                    let t = &mut self.triangles[slot];
                    if t.contents & contents_mask != 0 && t.bounds.segment(a,b,half) {
                        if let Some(contact) = t.box_contact(a,b,half) { result.consider(start,end,contact,&t.meta); }
                    }
                }
                _ => {
                    let m = &self.static_models[slot].source;
                    if m.geometry.is_none() || !(Bounds { lo:m.mins,hi:m.maxs }).segment(a,b,half) { continue; }
                    self.prepare_static(slot)?;
                    let cache = self.static_models[slot].cache.as_mut().unwrap();
                    for (_,i) in cache.spatial.query(bounds) {
                        let t = &mut cache.triangles[i];
                        if t.contents & contents_mask != 0 && t.bounds.segment(a,b,half) {
                            if let Some(contact) = t.box_contact(a,b,half) { result.consider(start,end,contact,&t.meta); }
                        }
                    }
                }
            }
        }
        Ok(result)
    }
}
