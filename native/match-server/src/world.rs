// SPDX-License-Identifier: AGPL-3.0-or-later
// Behavioral port of CODOL-Revival's independent world.py; see NOTICE.md.
use crate::collision::{CollisionWorld, Vec3, PLAYER_MINS, PLAYER_MAXS, PLAYER_MASK};
use crate::navigation::Navigation;
use crate::protocol::{Fields, UserCmd, Inventory, encode_snapshot};
use serde::{Deserialize, Serialize};

type Result<T> = std::result::Result<T, String>;
const SHOT_MASK: u32 = 0x2806831;
const SPEED: f64 = 190.;
const GRAVITY: f64 = 800.;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Weapon {
    pub index:u32, pub ammo_type:u32, pub clip_type:u32, pub clip_size:u32,
    pub fire_ms:u32, pub reload_ms:u32, pub empty_reload_ms:u32,
    pub damage:u32, pub minimum_damage:u32,
    pub full_damage_range:f64, pub minimum_damage_range:f64,
}

#[derive(Clone, Debug, Deserialize)]
pub struct Spawn { pub origin:Vec3, #[serde(default)] pub angles:Vec3 }

#[derive(Clone, Debug, Default, Serialize)]
pub struct Player {
    pub number:usize, pub origin:Vec3, pub velocity:Vec3, pub yaw:f64, pub pitch:f64,
    pub command_time:u32, pub health:u32, pub clip:u32, pub reserve:u32,
    pub next_fire:u32, pub reload_at:u32, pub respawn_at:u32, pub last_buttons:u32,
    pub ground:u32, pub event_sequence:u32, pub events:[u64;4], pub animation:u32,
    pub kills:u32, pub deaths:u32, pub spawn_count:u8, pub spawn_time:u32,
    pub weapon_raised:bool, pub input_time:u32,
}
impl Player {
    fn event(&mut self, number:u64) {
        self.events[self.event_sequence as usize%4]=number;
        self.event_sequence=(self.event_sequence+1)&255;
    }
}

fn add(a:Vec3,b:Vec3,scale:f64)->Vec3 { std::array::from_fn(|i|a[i]+b[i]*scale) }
fn dot(a:Vec3,b:Vec3)->f64 {
    let (mut sum, mut correction)=(0.0_f64,0.0);
    for i in 0..3 {
        let product=a[i]*b[i]; let next=sum+product;
        correction+=if sum.abs()>=product.abs() {(sum-next)+product} else {(product-next)+sum};
        sum=next;
    }
    sum+correction
}
fn distance(a:Vec3,b:Vec3)->f64 { (a[0]-b[0]).hypot(a[1]-b[1]).hypot(a[2]-b[2]) }
fn horizontal(a:Vec3,b:Vec3)->f64 { (a[0]-b[0]).hypot(a[1]-b[1]) }
fn angle(v:f64)->f64 { (v+180.).rem_euclid(360.)-180. }
fn word(v:f64)->u64 { (v as f32).to_bits() as u64 }
fn value(cmd:&UserCmd,key:&str)->u32 { *cmd.get(key).unwrap_or(&0) }
fn eye(p:&Player)->Vec3 { add(p.origin,[0.,0.,60.],1.) }

pub struct World {
    pub collision:CollisionWorld, pub weapon:Weapon, pub players:[Player;2],
    pub time:u32, pub bot:bool, pub navigation:Option<Navigation>,
    pub bot_path:Vec<Vec3>, pub bot_repath_at:u32, pub bot_visible_since:Option<u32>,
    pub position_base:[i32;3], pub static_entities:Vec<(usize,Fields)>,
    pub body_model:u32, pub hands_model:u32,
    spawns:Vec<(Vec3,f64)>,
}
impl World {
    pub fn new(mut collision:CollisionWorld, authored:Vec<Spawn>, weapon:Weapon,
               body_model:u32,hands_model:u32,bot:bool)->Result<Self> {
        let mut spawns=Vec::new();
        for spawn in authored {
            let hit=collision.trace_box(spawn.origin,add(spawn.origin,[0.,0.,-512.],1.),
                PLAYER_MINS,PLAYER_MAXS,PLAYER_MASK)?;
            if !hit.start_solid && hit.hit && hit.normal.is_some_and(|n|n[2]>=0.7)
                && hit.unresolved_static_models.is_empty() {
                spawns.push((hit.position,spawn.angles[1]));
            }
        }
        if spawns.len()<2 { return Err("two unobstructed authored spawns are required".into()); }
        let mut world=Self {collision,weapon,spawns,players:std::array::from_fn(|number|Player{number,..Default::default()}),
            time:1000,bot,navigation:None,bot_path:Vec::new(),bot_repath_at:0,bot_visible_since:None,
            position_base:[0;3],static_entities:Vec::new(),body_model,hands_model};
        world.spawn(0); world.spawn(1);
        Ok(world)
    }
    fn spawn(&mut self,index:usize) {
        let mut choice=self.spawns[0]; let mut best=-1.0;
        for &(origin,yaw) in &self.spawns {
            let nearest=self.players.iter().filter(|p|p.number!=index && p.command_time>0 && p.health>0)
                .map(|p|distance(origin,p.origin)).reduce(f64::min).unwrap_or(0.);
            if nearest>best { best=nearest;choice=(origin,yaw); }
        }
        let p=&mut self.players[index];
        p.origin=choice.0; p.velocity=[0.;3]; p.yaw=choice.1; p.pitch=0.;
        p.health=100; p.ground=2046; p.clip=self.weapon.clip_size; p.reserve=self.weapon.clip_size*3;
        p.command_time=self.time;p.input_time=self.time;
        p.spawn_count=p.spawn_count.wrapping_add(1);p.spawn_time=self.time;p.weapon_raised=false;
        p.next_fire=self.time;p.reload_at=0;p.respawn_at=0;p.last_buttons=0;p.animation=0;
    }
    fn ground(&mut self,p:&mut Player)->Result<bool> {
        let hit=self.collision.trace_box(add(p.origin,[0.,0.,0.25],1.),add(p.origin,[0.,0.,-0.25],1.),
            PLAYER_MINS,PLAYER_MAXS,PLAYER_MASK)?;
        let grounded=!hit.start_solid && hit.hit && hit.normal.is_some_and(|n|n[2]>=0.7) && p.velocity[2]<=0.;
        p.ground=if grounded {2046} else {2047};
        if grounded {p.origin=hit.position;p.velocity[2]=0.;}
        Ok(grounded)
    }
    fn slide(&mut self,mut origin:Vec3,mut velocity:Vec3,mut seconds:f64)->Result<(Vec3,Vec3)> {
        for _ in 0..4 {
            if dot(velocity,velocity)<1e-10 {break;}
            let hit=self.collision.trace_box(origin,add(origin,velocity,seconds),PLAYER_MINS,PLAYER_MAXS,PLAYER_MASK)?;
            if hit.start_solid {return Ok((origin,[0.;3]));}
            origin=hit.position;
            if !hit.hit {break;}
            seconds*=1.-hit.fraction;
            let normal=hit.normal.ok_or("hit without a normal")?;
            let into=dot(velocity,normal);
            if into<0. {velocity=add(velocity,normal,-into);}
        }
        Ok((origin,velocity))
    }
    fn movement(&mut self,p:&mut Player,cmd:&UserCmd,milliseconds:u32)->Result<()> {
        let dt=milliseconds as f64/1000.;
        let mut grounded=self.ground(p)?;
        if grounded {
            let speed=p.velocity[0].hypot(p.velocity[1]);
            let scale=if speed>0. {(speed-speed.max(100.)*6.*dt).max(0.)/speed} else {0.};
            p.velocity[0]*=scale;p.velocity[1]*=scale;
        }
        let d=value(cmd,"direction");
        let forward=((d&1!=0) as i32-(d&2!=0) as i32) as f64;
        let right=((d&4!=0) as i32-(d&8!=0) as i32) as f64;
        let yaw=p.yaw.to_radians();
        let mut wish=[yaw.cos()*forward+yaw.sin()*right,yaw.sin()*forward-yaw.cos()*right,0.];
        let length=wish[0].hypot(wish[1]);
        if length>0. {
            wish=wish.map(|v|v/length);
            let acceleration=(SPEED-dot(p.velocity,wish)).max(0.).min(dt*if grounded {9.} else {1.}*SPEED);
            p.velocity=add(p.velocity,wish,acceleration);
        }
        if grounded && value(cmd,"buttons")&1024!=0 && p.last_buttons&1024==0 {
            p.velocity[2]=(2.*GRAVITY*39.).sqrt();p.ground=2047;grounded=false;
        }
        if !grounded {p.velocity[2]-=GRAVITY*dt/2.;}
        let (start,velocity)=(p.origin,p.velocity);
        let (mut moved,mut new_velocity)=self.slide(start,velocity,dt)?;
        if grounded && horizontal(moved,add(start,velocity,dt))>0.01 {
            let up=self.collision.trace_box(start,add(start,[0.,0.,18.],1.),PLAYER_MINS,PLAYER_MAXS,PLAYER_MASK)?;
            if !up.hit && !up.start_solid {
                let (stepped,step_velocity)=self.slide(up.position,velocity,dt)?;
                let down=self.collision.trace_box(stepped,add(stepped,[0.,0.,-18.25],1.),PLAYER_MINS,PLAYER_MAXS,PLAYER_MASK)?;
                if down.hit && !down.start_solid && down.normal.is_some_and(|n|n[2]>=0.7)
                    && horizontal(start,down.position)>horizontal(start,moved) {
                    moved=down.position;new_velocity=step_velocity;
                }
            }
        }
        p.origin=moved;p.velocity=new_velocity;
        if !grounded {p.velocity[2]-=GRAVITY*dt/2.;}
        self.ground(p)?;
        Ok(())
    }
    fn visible(&mut self,from:Vec3,to:Vec3)->Result<bool> {
        let hit=self.collision.trace_point(from,to,SHOT_MASK,true)?;
        Ok(!hit.hit && hit.unresolved_static_models.is_empty())
    }
    fn hit_player(start:Vec3,direction:Vec3,p:&Player)->Option<f64> {
        let (mut near,mut far)=(0.0_f64,8192.0_f64);
        for axis in 0..3 {
            let (low,high)=(p.origin[axis]+PLAYER_MINS[axis],p.origin[axis]+PLAYER_MAXS[axis]);
            if direction[axis].abs()<1e-10 {
                if start[axis]<low || start[axis]>high {return None;}
            } else {
                let (a,b)=((low-start[axis])/direction[axis],(high-start[axis])/direction[axis]);
                near=near.max(a.min(b));far=far.min(a.max(b));
                if near>far {return None;}
            }
        }
        (near<=far).then_some(near)
    }
    fn shoot(&mut self,p:&mut Player,now:u32)->Result<()> {
        p.clip-=1;p.next_fire=now+self.weapon.fire_ms;
        p.animation=((p.animation^0x400)&0x400)|2;p.event(if p.clip>0 {36} else {37});
        let (pitch,yaw)=(p.pitch.to_radians(),p.yaw.to_radians());
        let direction=[yaw.cos()*pitch.cos(),yaw.sin()*pitch.cos(),-pitch.sin()];
        let start=eye(p);
        let wall=self.collision.trace_point(start,add(start,direction,8192.),SHOT_MASK,false)?;
        if !wall.unresolved_static_models.is_empty() {return Ok(());}
        let distance=wall.fraction*8192.;let w=&self.weapon;
        for target in &mut self.players {
            if target.number==p.number || target.health==0 {continue;}
            let Some(hit)=Self::hit_player(start,direction,target) else {continue;};
            if hit>=distance {continue;}
            let falloff=((hit-w.full_damage_range)/(w.minimum_damage_range-w.full_damage_range).max(1.)).clamp(0.,1.);
            let damage=(w.damage as f64+(w.minimum_damage as f64-w.damage as f64)*falloff).round_ties_even() as u32;
            target.health=target.health.saturating_sub(damage);
            if target.health==0 {
                target.velocity=[0.;3];target.reload_at=0;target.respawn_at=self.time+3000;
                target.deaths+=1;p.kills+=1;
            }
        }
        Ok(())
    }
    fn command(&mut self,index:usize,cmd:&UserCmd)->Result<()> {
        let mut p=self.players[index].clone();
        let raw=*cmd.get("time").ok_or("missing input time")?;
        if raw<=p.input_time || raw as u64>self.time as u64+20000 {return Ok(());}
        p.input_time=raw;
        let now=raw.min(self.time+200);
        if now<=p.command_time {self.players[index]=p;return Ok(());}
        let mut previous=p.command_time.max(now.saturating_sub(200));p.command_time=now;
        if p.health>0 {
            if cmd.get("weapon")==Some(&self.weapon.index) {p.weapon_raised=true;}
            p.yaw=angle(value(cmd,"yaw") as f64*360./65536.);
            p.pitch=angle(value(cmd,"pitch") as f64*360./65536.).clamp(-85.,85.);
            while previous<now {
                let duration=(now-previous).min(50);
                self.movement(&mut p,cmd,duration)?;previous+=duration;p.last_buttons=value(cmd,"buttons");
            }
            let buttons=value(cmd,"buttons");
            if p.reload_at==0 {
                if buttons&16!=0 && p.reserve>0 && p.clip<self.weapon.clip_size {
                    p.reload_at=now+if p.clip>0 {self.weapon.reload_ms} else {self.weapon.empty_reload_ms};
                    p.event(if p.clip>0 {24} else {25});
                    p.animation=((p.animation^0x400)&0x400)|if p.clip>0 {13} else {15};
                } else if buttons&1!=0 && p.clip>0 && now>=p.next_fire {self.shoot(&mut p,now)?;}
            }
        }
        self.players[index]=p;Ok(())
    }
    fn bot_command(&mut self)->Result<UserCmd> {
        let bot=self.players[1].clone();let target=self.players[0].clone();
        let mut delta=add(eye(&target),eye(&bot),-1.);
        let visible=target.health>0 && self.visible(eye(&bot),eye(&target))?;
        let mut moving=target.health>0 && delta[0].hypot(delta[1])>300.;
        if !visible && target.health>0 {
            if let Some(nav)=&mut self.navigation {
                if self.time>=self.bot_repath_at {
                    self.bot_path=nav.route(bot.origin,target.origin,&mut self.collision)?;
                    self.bot_repath_at=self.time+500;
                }
                while self.bot_path.first().is_some_and(|p|distance(bot.origin,*p)<20.) {self.bot_path.remove(0);}
                moving=!self.bot_path.is_empty();
                if let Some(p)=self.bot_path.first() {delta=add(*p,bot.origin,-1.);}
            }
        }
        let desired_yaw=delta[1].atan2(delta[0]).to_degrees();
        let desired_pitch=-delta[2].atan2(delta[0].hypot(delta[1])).to_degrees();
        let elapsed=self.time.saturating_sub(bot.command_time).min(200) as f64;
        let yaw=bot.yaw+angle(desired_yaw-bot.yaw).clamp(-0.18*elapsed,0.18*elapsed);
        self.bot_visible_since=if visible {Some(self.bot_visible_since.unwrap_or(self.time))} else {None};
        let buttons=if bot.clip==0 {16} else if visible && self.time-self.bot_visible_since.unwrap()>=250
            && angle(desired_yaw-yaw).abs()<3. {1} else {0};
        Ok([("time",self.time),("yaw",((yaw*65536./360.).round_ties_even() as i64&65535) as u32),
            ("pitch",((desired_pitch*65536./360.).round_ties_even() as i64&65535) as u32),
            ("buttons",buttons),("direction",if moving && angle(desired_yaw-yaw).abs()<45. {1} else {0})]
            .into_iter().map(|(k,v)|(k.into(),v)).collect())
    }
    pub fn step(&mut self,commands:&[UserCmd],milliseconds:u32)->Result<()> {
        if milliseconds==0 {return Err("simulation time must advance".into());}
        self.time=self.time.checked_add(milliseconds).ok_or("simulation clock overflow")?;
        for index in 0..2 {
            if self.players[index].respawn_at>0 && self.time>=self.players[index].respawn_at {self.spawn(index);}
            let p=&mut self.players[index];
            if p.reload_at>0 && self.time>=p.reload_at {
                let count=(self.weapon.clip_size-p.clip).min(p.reserve);
                p.clip+=count;p.reserve-=count;p.reload_at=0;p.animation=(p.animation^0x400)&0x400;p.event(27);
            }
        }
        for cmd in commands {self.command(0,cmd)?;}
        if self.bot {let cmd=self.bot_command()?;self.command(1,&cmd)?;}
        Ok(())
    }
    pub fn snapshot(&self)->Result<(Vec<u8>,Fields)> {
        let p=&self.players[0];
        let weapon_time=(if p.reload_at>0 {p.reload_at} else {p.next_fire}).saturating_sub(p.command_time.max(self.time));
        let mut fields:Fields=[(0,p.command_time as u64),(1,p.event_sequence as u64),(3,weapon_time as u64),
            (8,word(p.origin[0])),(9,p.animation as u64),(10,word(p.origin[2])),(11,word(p.origin[1])),
            (13,word(p.velocity[1])),(14,word(p.velocity[0])),(16,word(p.velocity[2])),
            (17,if p.reload_at>0 {8} else if weapon_time>0 {6} else {0}),
            (18,word(p.yaw)),(19,word(p.pitch)),(28,if p.health>0 {0} else {0x20000}),
            (30,word(1.)),(34,word(60.)),(38,60),(39,self.weapon.index as u64),(47,p.ground as u64),
            (54,0x1000),(56,self.hands_model as u64),(59,0),(60,190),(63,800),(68,2047),
            (83,if p.health>0 {0} else {8}),(85,p.spawn_time as u64),(217,word(1.))].into();
        for (i,e) in p.events.iter().enumerate() {fields.insert(21+i,*e);}
        let mut entities=self.static_entities.clone();
        for p in &self.players {
            let mut values:Fields=[(8,if p.health>0 {0} else {0x20000}),(12,1),(16,p.command_time as u64),
                (24,word(p.origin[0])),(28,word(p.origin[1])),(32,word(p.origin[2])),
                (60,word(p.pitch)),(64,word(p.yaw)),(136,p.ground as u64),(156,p.number as u64),
                (172,p.event_sequence as u64),(208,(self.weapon.index|self.weapon.index<<16) as u64)].into();
            for (i,e) in p.events.iter().enumerate() {values.insert(176+i*8,*e);}
            entities.push((p.number,values));
        }
        entities.sort_by_key(|row|row.0);
        let clients:Vec<_>=self.players.iter().map(|p|(p.number,Fields::from([(20,self.body_model as u64)]))).collect();
        let inventory=Inventory{weapon:self.weapon.index,ammo_type:self.weapon.ammo_type,clip_type:self.weapon.clip_type,
            clip:p.clip,reserve:p.reserve,raised:p.weapon_raised};
        let wire=encode_snapshot(&fields,self.time,p.health as u16,Some(&inventory),p.spawn_count,
            &entities,&clients,self.position_base)?;
        Ok((wire,fields))
    }
}
