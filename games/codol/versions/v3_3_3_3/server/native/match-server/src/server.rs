// SPDX-License-Identifier: AGPL-3.0-or-later
//! UDP owns admission/ACK/crypto; the simulation worker never blocks this loop.
use std::{io::{self,BufRead}, net::{Ipv4Addr,SocketAddr,UdpSocket}, path::Path,
    sync::{Arc,Mutex,atomic::{AtomicBool,Ordering},mpsc::{self,Receiver,Sender}},
    thread, time::{Duration,Instant}};
use serde_json::{Value,json};
use crate::{runtime::{load_package,Loaded},protocol::{Association,Connection,Fields,UserCmd,nat_reply},world::World};

type Result<T> = std::result::Result<T,String>;
const FRAME:Duration=Duration::from_millis(50);
fn emit(value:Value) {println!("{value}");}

#[derive(Clone)]
struct Frame {wire:Vec<u8>,fields:Fields}
impl Frame {
    fn capture(world:&World)->Result<Self> {let (wire,fields)=world.snapshot()?;Ok(Self{wire,fields})}
}
enum Simulation {Reset(u64),Start(u64),Input(u64,Vec<UserCmd>)}

fn simulate(mut world:World,rx:Receiver<Simulation>,latest:Arc<Mutex<Option<(u64,Frame)>>>,stopping:Arc<AtomicBool>)->Result<()> {
    let (mut epoch,mut deadline,mut pending)=(0,None::<Instant>,Vec::new());
    let mut last_report=Instant::now();let mut health=[0;2];
    let mut frames=Vec::new();
    while !stopping.load(Ordering::Relaxed) {
        let wait=deadline.map(|d|d.saturating_duration_since(Instant::now())).unwrap_or(Duration::from_millis(50));
        match rx.recv_timeout(wait) {
            Ok(Simulation::Reset(generation))=>{epoch=generation;deadline=None;pending.clear();},
            Ok(Simulation::Start(generation)) if generation==epoch=>{deadline=Some(Instant::now()+FRAME);},
            Ok(Simulation::Input(generation,commands)) if generation==epoch=>pending.extend(commands),
            Ok(_)=>{},
            Err(mpsc::RecvTimeoutError::Disconnected)=>return Ok(()),
            Err(mpsc::RecvTimeoutError::Timeout)=>{},
        }
        let Some(due)=deadline else {continue;};
        let now=Instant::now();if now<due {continue;}
        let elapsed=50+(now-due).as_secs_f64().mul_add(1000.,0.).round_ties_even() as u32;
        deadline=Some(now+FRAME);
        world.step(&pending,elapsed)?;pending.clear();
        let snapshot=Frame::capture(&world)?;
        *latest.lock().map_err(|_|"snapshot mailbox poisoned")?=Some((epoch,snapshot));
        frames.push(now.elapsed().as_secs_f64()*1000.);
        let current=[world.players[0].health,world.players[1].health];
        if current!=health || last_report.elapsed()>=Duration::from_secs(5) {
            frames.sort_by(f64::total_cmp);
            let percentile=|p:f64|frames[((frames.len() as f64*p).ceil() as usize).saturating_sub(1)];
            emit(json!({"event":"match_state","engine":"rust","server_time":world.time,
                "players":world.players,"frame_p95_ms":percentile(0.95),"frame_p99_ms":percentile(0.99),
                "frame_max_ms":frames.last()}));
            health=current;last_report=Instant::now();frames.clear();
        }
    }
    Ok(())
}

struct Session {
    uid:u64,sid:[u8;8],key:[u8;16],options:Value,
    connection:Connection,association:Option<Association>,epoch:u64,
}
impl Session {
    fn new(uid:u64,sid:[u8;8],key:[u8;16],options:&Value)->Result<Self> {
        Ok(Self{uid,sid,key,options:options.clone(),connection:Connection::new(uid,options)?,association:None,epoch:0})
    }
    fn reset(&mut self,sim:&Sender<Simulation>)->Result<()> {
        self.connection=Connection::new(self.uid,&self.options)?;self.epoch+=1;
        sim.send(Simulation::Reset(self.epoch)).map_err(|_|"simulation stopped".to_string())?;
        Ok(())
    }
    fn snapshot(&mut self,frame:&Frame)->Result<Vec<Vec<u8>>> {
        self.connection.send(&frame.wire,Some(&frame.fields))
    }
    fn send(&mut self,socket:&UdpSocket,values:Vec<Vec<u8>>)->Result<()> {
        let association=self.association.as_mut().ok_or("DATA before handshake")?;
        for value in values {
            let wire=association.encrypt(&value)?;
            socket.send_to(&wire,association.peer).map_err(|e|e.to_string())?;
        }
        Ok(())
    }
    fn packet(&mut self,packet:&[u8],peer:SocketAddr,socket:&UdpSocket,sim:&Sender<Simulation>,frame:&Frame)->Result<()> {
        if self.association.as_ref().is_some_and(|a|a.peer!=peer) {return Err("reservation already bound to another peer".into());}
        if matches!(packet.first(),Some(1|3)) {
            let mut association=match self.association.take() {Some(a)=>a,None=>Association::new(self.sid,self.key,peer)?};
            let previous=association.init.clone();
            let response=association.handshake(packet);
            let changed=previous!=association.init;
            self.association=Some(association);
            let response=response?;
            if changed {self.reset(sim)?;}
            socket.send_to(&response,peer).map_err(|e|e.to_string())?;
            return Ok(());
        }
        let plain=self.association.as_mut().ok_or("DATA before handshake")?.decrypt(packet)?;
        let previous_phase=self.connection.phase.clone();let previous_sequence=self.connection.received;
        let previous_loading=self.connection.loading_status;
        let mut values=self.connection.receive(&plain,false)?;
        let mut initial=self.connection.phase=="primed" && previous_loading<6 && self.connection.loading_status==6;
        if self.connection.received>previous_sequence && !self.connection.pending_commands.is_empty() {
            if self.connection.phase=="primed" && plain.get(4)==Some(&self.connection.server_id) {
                self.connection.phase="active".into();initial=true;
                sim.send(Simulation::Start(self.epoch)).map_err(|_|"simulation stopped")?;
            }
            sim.send(Simulation::Input(self.epoch,std::mem::take(&mut self.connection.pending_commands))).map_err(|_|"simulation stopped")?;
        }
        if initial {
            if self.connection.published_command==0 {
                self.connection.queue_command(format!("a {}",frame.fields[&39]).as_bytes())?;
            }
            values.extend(self.snapshot(frame)?);
        }
        if previous_phase!=self.connection.phase {
            emit(json!({"event":"match_phase","phase":self.connection.phase,"loading_status":self.connection.loading_status,"peer":peer.to_string()}));
        }
        self.send(socket,values)
    }
}

fn fixed<const N:usize>(v:&Value)->Result<[u8;N]> {
    hex::decode(v.as_str().ok_or("missing reservation material")?).map_err(|_|"invalid reservation material")?
        .try_into().map_err(|_|"invalid reservation material length".into())
}

fn network(socket:UdpSocket,options:Value,controls:Receiver<Value>,sim:Sender<Simulation>,
           latest:Arc<Mutex<Option<(u64,Frame)>>>,mut frame:Frame,stopping:Arc<AtomicBool>)->Result<()> {
    let mut session=None::<Session>;let mut buffer=[0;65535];
    while !stopping.load(Ordering::Relaxed) {
        while let Ok(control)=controls.try_recv() {
            let id=control.get("id").cloned().unwrap_or(Value::Null);
            let response=(||->Result<Value>{
                match control["op"].as_str() {
                    Some("stop")=>{stopping.store(true,Ordering::Relaxed);Ok(json!({"event":"stopped","id":id}))},
                    Some("reserve")=>{
                        let uid=control["uid"].as_u64().filter(|n|*n>0).ok_or("invalid admitted identity")?;
                        let sid=fixed(&control["sid"])?;let key=fixed(&control["key"])?;
                        if let Some(s)=&session {
                            if s.uid!=uid || s.sid!=sid || s.key!=key {return Err("local instance already reserved".into());}
                        } else {session=Some(Session::new(uid,sid,key,&options)?);}
                        Ok(json!({"event":"reserved","id":id,"port":socket.local_addr().map_err(|e|e.to_string())?.port()}))
                    },
                    _=>Err("unsupported match control".into()),
                }
            })();
            emit(response.unwrap_or_else(|error|json!({"event":"error","id":id,"error":error})));
        }
        if let Some((epoch,next))=latest.lock().map_err(|_|"snapshot mailbox poisoned")?.take() {
            if let Some(s)=&mut session {
                if epoch==s.epoch {
                    frame=next;
                    if s.connection.phase=="active" {
                        let values=s.snapshot(&frame)?;
                        if let Err(reason)=s.send(&socket,values) {emit(json!({"event":"match_send_error","reason":reason}));}
                    }
                }
            }
        }
        // A receive burst is bounded so control and ready snapshots still run.
        for _ in 0..64 {
            let (length,peer)=match socket.recv_from(&mut buffer) {
                Ok(packet)=>packet,
                Err(error) if error.kind()==io::ErrorKind::WouldBlock=>break,
                Err(error) if error.kind()==io::ErrorKind::ConnectionReset=>{
                    if let Some(s)=&mut session {s.association=None;s.reset(&sim)?;}
                    emit(json!({"event":"match_peer_reset"}));continue;
                },
                Err(error)=>return Err(error.to_string()),
            };
            let packet=&buffer[..length];
            if peer.ip()!=Ipv4Addr::LOCALHOST {continue;}
            if let Some(reply)=nat_reply(packet) {
                socket.send_to(&reply,peer).map_err(|e|e.to_string())?;
                emit(json!({"event":"match_nat_reply","peer":peer.to_string()}));continue;
            }
            let result=match &mut session {
                Some(s)=>s.packet(packet,peer,&socket,&sim,&frame),
                None=>Err("no live reservation".into()),
            };
            if let Err(reason)=result {emit(json!({"event":"match_rejected","reason":reason,"bytes":length,"peer":peer.to_string()}));}
        }
        thread::sleep(Duration::from_millis(1));
    }
    Ok(())
}

pub fn serve(directory:&Path,port:u16)->Result<()> {
    let Loaded{world,options,map,checksum}=load_package(directory)?;
    let first=Frame::capture(&world)?;
    let socket=UdpSocket::bind((Ipv4Addr::LOCALHOST,port)).map_err(|e|e.to_string())?;
    socket.set_nonblocking(true).map_err(|e|e.to_string())?;
    let port=socket.local_addr().map_err(|e|e.to_string())?.port();
    let stopping=Arc::new(AtomicBool::new(false));let latest=Arc::new(Mutex::new(None));
    let (input_tx,input_rx)=mpsc::channel();let (control_tx,control_rx)=mpsc::channel();
    let worker_stop=stopping.clone();let worker_latest=latest.clone();
    let worker=thread::spawn(move||{
        let result=simulate(world,input_rx,worker_latest,worker_stop.clone());
        if let Err(error)=&result {emit(json!({"event":"match_simulation_error","error":error}));worker_stop.store(true,Ordering::Relaxed);}
        result
    });
    let stdin_stop=stopping.clone();
    // EOF means the Python owner stopped, including Stop-Process and crashes.
    thread::spawn(move||{
        for line in io::stdin().lock().lines() {
            let Ok(line)=line else {break;};
            match serde_json::from_str(&line) {
                Ok(value)=>if control_tx.send(value).is_err() {break;},
                Err(_)=>emit(json!({"event":"error","error":"invalid match control JSON"})),
            }
        }
        stdin_stop.store(true,Ordering::Relaxed);
    });
    emit(json!({"event":"ready","engine":"rust","port":port,"map":map,"checksum":checksum}));
    let result=network(socket,options,control_rx,input_tx,latest,first,stopping.clone());
    stopping.store(true,Ordering::Relaxed);
    let simulated=worker.join().map_err(|_|"simulation worker panicked")?;
    result.and(simulated)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn nat_and_control_do_not_wait_for_simulation_and_stop_releases_socket() {
        let socket=UdpSocket::bind((Ipv4Addr::LOCALHOST,0)).unwrap();socket.set_nonblocking(true).unwrap();
        let address=socket.local_addr().unwrap();let (controls,rx)=mpsc::channel();
        // Deliberately no simulation consumer: networking must still reply.
        let (sim,_never_run)=mpsc::channel();let stopping=Arc::new(AtomicBool::new(false));
        let server=thread::spawn(move||network(socket,json!({"netconst_checksum":1}),rx,sim,
            Arc::new(Mutex::new(None)),Frame{wire:vec![],fields:Fields::new()},stopping));
        let client=UdpSocket::bind((Ipv4Addr::LOCALHOST,0)).unwrap();client.set_read_timeout(Some(Duration::from_secs(1))).unwrap();
        let mut packet=[7u8;29];packet[..3].copy_from_slice(&[13,2,0]);
        client.send_to(&packet,address).unwrap();let mut reply=[0;29];client.recv_from(&mut reply).unwrap();
        packet[0]=12;assert_eq!(reply,packet);
        controls.send(json!({"op":"stop","id":1})).unwrap();server.join().unwrap().unwrap();
        assert!(UdpSocket::bind(address).is_ok());
    }
}
