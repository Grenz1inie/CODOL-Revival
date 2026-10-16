// SPDX-License-Identifier: AGPL-3.0-or-later
// Port of src/match_server/navigation.py (CODOL-Revival).
use crate::collision::{CollisionWorld, Vec3, PLAYER_MASK, PLAYER_MAXS, PLAYER_MINS};
use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap};

#[derive(Clone, Debug)]
pub struct Node {
    pub position: Vec3,
    pub links: Vec<usize>,
    pub standing: bool,
}

pub struct Navigation {
    pub nodes: Vec<Node>,
    // Valid only for the same frozen CollisionWorld used when loading the CSV.
    edges: HashMap<(usize, usize), bool>,
}

#[derive(Clone, Copy)]
struct Pending { score: f64, index: usize }
impl PartialEq for Pending {
    fn eq(&self, other: &Self) -> bool { self.score == other.score && self.index == other.index }
}
impl Eq for Pending {}
impl PartialOrd for Pending {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> { Some(self.cmp(other)) }
}
impl Ord for Pending {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse for a min-heap; Python heapq breaks equal scores by node index.
        other.score.partial_cmp(&self.score).unwrap_or(Ordering::Equal)
            .then_with(|| other.index.cmp(&self.index))
    }
}

// Faithful three-dimensional norm: power-of-two scaling, compensated squares,
// then a square-root residual correction. Matches the algorithm used by
// CPython 3.13 math.dist/vector_norm (Modules/mathmodule.c); plain sqrt(dot)
// loses precision at the strict 256-unit boundary and when ranking equal paths.
fn distance(a: Vec3, b: Vec3) -> f64 {
    fn norm(values: Vec3) -> f64 {
        let max = values.into_iter().fold(0.0_f64,f64::max);
        if max.is_infinite() { return max; }
        if values.iter().any(|v| v.is_nan()) { return f64::NAN; }
        if max == 0. { return 0.; }
        let bits = max.to_bits();
        let exponent = ((bits >> 52) & 0x7ff) as i32;
        let frexp_exponent = if exponent == 0 {
            -1073 + (63 - (bits & ((1_u64 << 52) - 1)).leading_zeros() as i32)
        } else { exponent - 1022 };
        if frexp_exponent < -1023 {
            return f64::MIN_POSITIVE * norm(values.map(|v| v / f64::MIN_POSITIVE));
        }
        let power = -frexp_exponent;
        let scale = if power >= -1022 {
            f64::from_bits(((power + 1023) as u64) << 52)
        } else {
            f64::from_bits(1_u64 << (power + 1074))
        };
        let (mut total,mut products_error,mut sums_error) = (1.0_f64,0.0,0.0);
        for v in values {
            let x = v * scale;
            let square = x*x;
            let next = total + square;
            products_error += x.mul_add(x,-square);
            sums_error += square - (next-total);
            total = next;
        }
        let root = (total-1. + (products_error+sums_error)).sqrt();
        let square = -root*root;
        let next = total+square;
        products_error += (-root).mul_add(root,-square);
        sums_error += square - (next-total);
        let residual = next-1. + (products_error+sums_error);
        (root + residual/(2.*root))/scale
    }
    norm(std::array::from_fn(|i| (a[i]-b[i]).abs()))
}

// The waypoint file uses Python csv.reader's default comma/double-quote dialect.
// Keep trailing empty fields, escaped quotes, CRLF, and quoted record newlines.
fn csv_rows(text: &str) -> Vec<Vec<String>> {
    let mut rows = Vec::new();
    let mut row = Vec::new();
    let mut field = String::new();
    let mut quoted = false;
    let mut field_started = false;
    let mut chars = text.chars().peekable();
    while let Some(c) = chars.next() {
        if quoted {
            if c == '"' {
                if chars.peek() == Some(&'"') { field.push('"'); chars.next(); }
                else { quoted = false; }
            } else { field.push(c); }
        } else {
            match c {
                '"' if !field_started => { quoted = true; field_started = true; }
                ',' => {
                    row.push(std::mem::take(&mut field));
                    field_started = false;
                }
                '\n' | '\r' => {
                    if c == '\r' && chars.peek() == Some(&'\n') { chars.next(); }
                    if field_started || !row.is_empty() { row.push(std::mem::take(&mut field)); }
                    rows.push(std::mem::take(&mut row));
                    field_started = false;
                }
                _ => { field.push(c); field_started = true; }
            }
        }
    }
    if field_started || !row.is_empty() {
        row.push(field);
        rows.push(row);
    }
    rows
}

impl Navigation {
    pub fn from_csv(text: &str, collision: &mut CollisionWorld) -> Result<Self,String> {
        let rows = csv_rows(text);
        let count = rows.first().and_then(|row| row.first())
            .and_then(|value| value.trim().parse::<usize>().ok())
            .ok_or("invalid waypoint count")?;
        if !(1..=4096).contains(&count) || rows.len()-1 != count {
            return Err("invalid waypoint count".into());
        }
        let mut nodes = Vec::with_capacity(count);
        for row in &rows[1..] {
            if row.len() < 3 { return Err("truncated waypoint".into()); }
            let coordinates: Vec<f64> = row[0].split_whitespace().map(str::parse)
                .collect::<Result<_,_>>().map_err(|_| "invalid waypoint position or link")?;
            let mut position: Vec3 = coordinates.try_into().map_err(|_| "invalid waypoint position or link")?;
            let links: Vec<usize> = row[1].split_whitespace().map(str::parse)
                .collect::<Result<_,_>>().map_err(|_| "invalid waypoint position or link")?;
            if !position.iter().all(|v| v.is_finite()) || links.len() > 48 || links.iter().any(|&n| n >= count) {
                return Err("invalid waypoint position or link".into());
            }
            let mut standing = matches!(row[2].as_str(),"stand" | "grenade" | "claymore" | "javelin");
            if standing {
                let [x,y,z] = position;
                let ground = collision.trace_box([x,y,z+18.],[x,y,z-18.],PLAYER_MINS,PLAYER_MAXS,PLAYER_MASK)?;
                standing = ground.hit && !ground.start_solid
                    && ground.normal.is_some_and(|n| n[2] >= 0.7)
                    && ground.unresolved_static_models.is_empty();
                if standing { position = [x,y,ground.position[2]+0.125]; }
            }
            nodes.push(Node { position,links,standing });
        }
        Ok(Self { nodes,edges: HashMap::new() })
    }

    fn clear(a: Vec3, b: Vec3, collision: &mut CollisionWorld) -> Result<bool,String> {
        fn sweep(a: Vec3, b: Vec3, world: &mut CollisionWorld) -> Result<bool,String> {
            let trace = world.trace_box(a,b,PLAYER_MINS,PLAYER_MAXS,PLAYER_MASK)?;
            Ok(trace.fraction >= 1. && !trace.start_solid && trace.unresolved_static_models.is_empty())
        }
        if sweep(a,b,collision)? { return Ok(true); }
        let up_a = [a[0],a[1],a[2]+18.];
        let up_b = [b[0],b[1],b[2]+18.];
        Ok(sweep(a,up_a,collision)? && sweep(b,up_b,collision)? && sweep(up_a,up_b,collision)?)
    }

    fn nearest(&self, position: Vec3, collision: &mut CollisionWorld) -> Result<Option<usize>,String> {
        let mut order: Vec<_> = self.nodes.iter().enumerate()
            .map(|(i,n)| (i,distance(position,n.position))).filter(|(_,d)| *d < 256.).collect();
        // Stable sorting leaves equally distant nodes in their exported order.
        order.sort_by(|a,b| a.1.partial_cmp(&b.1).unwrap_or(Ordering::Equal));
        for (i,_) in order {
            if self.nodes[i].standing && Self::clear(position,self.nodes[i].position,collision)? {
                return Ok(Some(i));
            }
        }
        Ok(None)
    }

    pub fn route(&mut self, start: Vec3, goal: Vec3, collision: &mut CollisionWorld) -> Result<Vec<Vec3>,String> {
        if distance(start,goal) < 256. && Self::clear(start,goal,collision)? { return Ok(vec![goal]); }
        let Some(first) = self.nearest(start,collision)? else { return Ok(Vec::new()); };
        let Some(last) = self.nearest(goal,collision)? else { return Ok(Vec::new()); };
        let mut costs = vec![f64::INFINITY;self.nodes.len()];
        let mut parents = vec![None;self.nodes.len()];
        let mut queue = BinaryHeap::new();
        costs[first] = 0.;
        queue.push(Pending { score:0.,index:first });
        while let Some(Pending { index,.. }) = queue.pop() {
            if index == last {
                let mut path = vec![goal];
                let mut cursor = Some(index);
                while let Some(i) = cursor { path.push(self.nodes[i].position); cursor = parents[i]; }
                path.reverse();
                let mut skip = 0;
                while skip+1 < path.len() && distance(start,path[skip+1]) < 256.
                    && Self::clear(start,path[skip+1],collision)? { skip += 1; }
                path.drain(..skip);
                return Ok(path);
            }
            let node = &self.nodes[index];
            for &other in &node.links {
                let target = &self.nodes[other];
                if !target.standing { continue; }
                let edge = (index.min(other),index.max(other));
                let reachable = if let Some(&cached) = self.edges.get(&edge) { cached } else {
                    let clear = Self::clear(node.position,target.position,collision)?;
                    self.edges.insert(edge,clear);
                    clear
                };
                if !reachable { continue; }
                let cost = costs[index]+distance(node.position,target.position);
                if cost >= costs[other] { continue; }
                costs[other] = cost;
                parents[other] = Some(index);
                queue.push(Pending { score:cost+distance(target.position,goal),index:other });
            }
        }
        Ok(Vec::new())
    }
}
