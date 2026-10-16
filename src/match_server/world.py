# SPDX-License-Identifier: AGPL-3.0-or-later
"""A two-player authoritative world, independent of native engine layouts.

The restricted standing mover follows the reference friction/acceleration,
slide and step algorithms. It does not yet emulate sprint, stance or perks.
Both human and bot use the same movement, line-of-fire and weapon rules.
"""
from dataclasses import dataclass, field
import math
import struct

from .snapshot import Inventory, encode_snapshot

MOVE_MASK = 0x2001001
SHOT_MASK = 0x2806831
SPEED, GRAVITY = 190, 800


def _word(value):
    return struct.unpack('<I',struct.pack('<f',value))[0]


def _dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def _add(a,b,scale=1):
    return [x+y*scale for x,y in zip(a,b)]


def _angle(value):
    return (value+180)%360-180


@dataclass(frozen=True)
class Weapon:
    index: int
    ammo_type: int
    clip_type: int
    clip_size: int
    fire_ms: int
    reload_ms: int
    empty_reload_ms: int
    damage: int
    minimum_damage: int
    full_damage_range: float
    minimum_damage_range: float


@dataclass
class Player:
    number: int
    origin: list = field(default_factory=lambda:[0,0,0])
    velocity: list = field(default_factory=lambda:[0,0,0])
    yaw: float = 0
    pitch: float = 0
    command_time: int = 0
    health: int = 100
    clip: int = 0
    reserve: int = 0
    next_fire: int = 0
    reload_at: int = 0
    respawn_at: int = 0
    last_buttons: int = 0
    ground: int = 2046
    event_sequence: int = 0
    events: list = field(default_factory=lambda:[0]*4)
    animation: int = 0
    kills: int = 0
    deaths: int = 0
    spawn_count: int = 0
    spawn_time: int = 0
    weapon_raised: bool = False
    input_time: int = 0

    def event(self, number, parameter=0):
        self.events[self.event_sequence%4] = number | parameter << 32
        self.event_sequence = (self.event_sequence+1)&255


class World:
    def __init__(self, collision, spawns, weapon, *, body_model, hands_model,
                 position_base=(0,0,0), bot=True, navigation=None, static_entities=()):
        self.collision, self.weapon = collision, weapon
        self.body_model, self.hands_model = body_model, hands_model
        self.position_base, self.bot = position_base, bot
        self.time, self.bot_visible_since = 1000, None
        self.navigation,self.bot_path,self.bot_repath_at=navigation,[],0
        self.static_entities=static_entities
        self.spawns = []
        for spawn in spawns:
            origin=list(spawn['origin'])
            trace=collision.trace_box(origin,_add(origin,[0,0,-512]))
            if (not trace['start_solid'] and trace['hit'] and trace['normal'][2] >= .7
                    and not trace.get('unresolved_static_models')):
                self.spawns.append((trace['position'],spawn.get('angles',(0,0,0))[1]))
        if len(self.spawns) < 2:
            raise ValueError('two unobstructed authored spawns are required')
        self.players = [Player(0),Player(1)]
        for player in self.players:
            self._spawn(player)

    def _spawn(self, player):
        others=[p for p in self.players if p is not player and p.command_time and p.health]
        origin,yaw=max(self.spawns,key=lambda s:min((math.dist(s[0],p.origin) for p in others),default=0))
        player.origin=list(origin)
        player.velocity=[0,0,0]
        player.yaw,player.pitch=yaw,0
        player.health,player.ground=100,2046
        player.clip,player.reserve=self.weapon.clip_size,self.weapon.clip_size*3
        player.command_time=self.time
        player.input_time=self.time
        player.spawn_count=(player.spawn_count+1)&255
        player.spawn_time=self.time
        player.weapon_raised=False
        player.next_fire=self.time
        player.reload_at=player.respawn_at=player.last_buttons=0
        player.animation=0

    def _ground(self, player):
        hit=self.collision.trace_box(_add(player.origin,[0,0,.25]),_add(player.origin,[0,0,-.25]))
        on_ground=(not hit['start_solid'] and hit['hit'] and hit['normal'][2] >= .7
                   and player.velocity[2] <= 0)
        player.ground=2046 if on_ground else 2047
        if on_ground:
            player.origin=hit['position']
            player.velocity[2]=0
        return on_ground

    def _slide(self, origin, velocity, seconds):
        origin,velocity=list(origin),list(velocity)
        for _ in range(4):
            if _dot(velocity,velocity) < 1e-10:
                break
            hit=self.collision.trace_box(origin,_add(origin,velocity,seconds))
            if hit['start_solid']:
                return origin,[0,0,0]
            origin=hit['position']
            if not hit['hit']:
                break
            seconds *= 1-hit['fraction']
            normal=hit['normal']
            into=_dot(velocity,normal)
            if into < 0:
                velocity=_add(velocity,normal,-into)
        return origin,velocity

    def _move(self, player, command, milliseconds):
        dt=milliseconds/1000
        grounded=self._ground(player)
        if grounded:
            speed=math.hypot(*player.velocity[:2])
            scale=max(0,speed-max(100,speed)*6*dt)/speed if speed else 0
            player.velocity[0]*=scale
            player.velocity[1]*=scale
        direction=command.get('direction',0)
        forward=int(bool(direction&1))-int(bool(direction&2))
        right=int(bool(direction&4))-int(bool(direction&8))
        yaw=math.radians(player.yaw)
        wish=[math.cos(yaw)*forward+math.sin(yaw)*right,
              math.sin(yaw)*forward-math.cos(yaw)*right,0]
        length=math.hypot(*wish[:2])
        if length:
            wish=[v/length for v in wish]
            acceleration=min(max(0,SPEED-_dot(player.velocity,wish)),dt*(9 if grounded else 1)*SPEED)
            player.velocity=_add(player.velocity,wish,acceleration)
        if grounded and command.get('buttons',0)&1024 and not player.last_buttons&1024:
            player.velocity[2]=math.sqrt(2*GRAVITY*39)
            player.ground=2047
            grounded=False
        if not grounded:
            player.velocity[2]-=GRAVITY*dt/2
        start,velocity=list(player.origin),list(player.velocity)
        moved,new_velocity=self._slide(start,velocity,dt)
        if grounded and math.dist(moved[:2],_add(start,velocity,dt)[:2]) > .01:
            up=self.collision.trace_box(start,_add(start,[0,0,18]))
            if not up['hit'] and not up['start_solid']:
                stepped,step_velocity=self._slide(up['position'],velocity,dt)
                down=self.collision.trace_box(stepped,_add(stepped,[0,0,-18.25]))
                if (down['hit'] and not down['start_solid'] and down['normal'][2] >= .7
                        and math.dist(start[:2],down['position'][:2]) > math.dist(start[:2],moved[:2])):
                    moved,new_velocity=down['position'],step_velocity
        player.origin,player.velocity=moved,new_velocity
        if not grounded:
            player.velocity[2]-=GRAVITY*dt/2
        self._ground(player)

    @staticmethod
    def _eye(player):
        return _add(player.origin,[0,0,60])

    def _visible(self, player, target):
        trace=self.collision.trace_point(self._eye(player),self._eye(target),contents_mask=SHOT_MASK,any_hit=True)
        return not trace['hit'] and not trace.get('unresolved_static_models')

    @staticmethod
    def _hit_player(start, direction, player):
        near,far=0.0,8192.0
        for axis,(lo,hi) in enumerate(((-15,15),(-15,15),(0,70))):
            low,high=player.origin[axis]+lo,player.origin[axis]+hi
            if abs(direction[axis]) < 1e-10:
                if not low <= start[axis] <= high:
                    return None
            else:
                a,b=(low-start[axis])/direction[axis],(high-start[axis])/direction[axis]
                near,far=max(near,min(a,b)),min(far,max(a,b))
                if near > far:
                    return None
        return near if near <= far else None

    def _shoot(self, player, now):
        player.clip-=1
        player.next_fire=now+self.weapon.fire_ms
        player.animation=(player.animation^0x400)&0x400 | 2
        player.event(36 if player.clip else 37)
        pitch,yaw=math.radians(player.pitch),math.radians(player.yaw)
        direction=[math.cos(yaw)*math.cos(pitch),math.sin(yaw)*math.cos(pitch),-math.sin(pitch)]
        start=self._eye(player)
        wall=self.collision.trace_point(start,_add(start,direction,8192),contents_mask=SHOT_MASK)
        # Incomplete export can be exercised in unit tests; an unresolved model
        # in this specific ray must never allow damage through missing geometry.
        if wall.get('unresolved_static_models'):
            return
        distance=wall['fraction']*8192
        for target in self.players:
            if target is player or not target.health:
                continue
            hit=self._hit_player(start,direction,target)
            if hit is None or hit >= distance:
                continue
            weapon=self.weapon
            falloff=max(0,min(1,(hit-weapon.full_damage_range)/max(1,weapon.minimum_damage_range-weapon.full_damage_range)))
            damage=round(weapon.damage+(weapon.minimum_damage-weapon.damage)*falloff)
            target.health=max(0,target.health-damage)
            if not target.health:
                target.velocity=[0,0,0]
                target.reload_at=0
                target.respawn_at=self.time+3000
                target.deaths+=1
                player.kills+=1

    def _command(self, player, command):
        raw_time=command['time']
        if not player.input_time < raw_time <= self.time+20000:
            return
        player.input_time=raw_time
        # ClientThink clamps ahead commands; discarding them loses valid
        # movement/fire while the client's smoothed clock catches up.
        now=min(raw_time,self.time+200)
        if now <= player.command_time:
            return
        previous=max(player.command_time,now-200)
        player.command_time=now
        if not player.health:
            return
        if command.get('weapon') == self.weapon.index:
            player.weapon_raised=True
        player.yaw=_angle(command.get('yaw',0)*360/65536)
        player.pitch=max(-85,min(85,_angle(command.get('pitch',0)*360/65536)))
        while previous < now:
            duration=min(50,now-previous)
            self._move(player,command,duration)
            previous+=duration
            # One jump impulse per button transition, including split commands.
            player.last_buttons=command.get('buttons',0)
        buttons=command.get('buttons',0)
        if not player.reload_at:
            if buttons&16 and player.reserve and player.clip < self.weapon.clip_size:
                player.reload_at=now+(self.weapon.reload_ms if player.clip else self.weapon.empty_reload_ms)
                player.event(24 if player.clip else 25)
                player.animation=(player.animation^0x400)&0x400 | (13 if player.clip else 15)
            elif buttons&1 and player.clip and now >= player.next_fire:
                self._shoot(player,now)

    def _bot_command(self):
        bot,target=self.players[1],self.players[0]
        delta=[b-a for a,b in zip(self._eye(bot),self._eye(target))]
        visible=target.health and self._visible(bot,target)
        moving=bool(target.health and math.hypot(*delta[:2]) > 300)
        if not visible and target.health and self.navigation:
            if self.time >= self.bot_repath_at:
                self.bot_path=self.navigation.route(bot.origin,target.origin)
                self.bot_repath_at=self.time+500
            while self.bot_path and math.dist(bot.origin,self.bot_path[0]) < 20:
                self.bot_path.pop(0)
            moving=bool(self.bot_path)
            if self.bot_path:
                delta=[b-a for a,b in zip(bot.origin,self.bot_path[0])]
        desired_yaw=math.degrees(math.atan2(delta[1],delta[0]))
        desired_pitch=-math.degrees(math.atan2(delta[2],math.hypot(*delta[:2])))
        elapsed=min(200,self.time-bot.command_time)
        turn=max(-.18*elapsed,min(.18*elapsed,_angle(desired_yaw-bot.yaw)))
        yaw=bot.yaw+turn
        self.bot_visible_since=(self.bot_visible_since if self.bot_visible_since is not None else self.time) if visible else None
        buttons=0
        if not bot.clip:
            buttons=16
        elif (visible and self.time-self.bot_visible_since >= 250
              and abs(_angle(desired_yaw-yaw)) < 3):
            buttons=1
        return dict(time=self.time,yaw=round(yaw*65536/360)&65535,
                    pitch=round(desired_pitch*65536/360)&65535,buttons=buttons,
                    direction=1 if moving and abs(_angle(desired_yaw-yaw)) < 45 else 0)

    def step(self, commands=(), *, milliseconds=50):
        if type(milliseconds) is not int or milliseconds <= 0:
            raise ValueError('simulation time must advance')
        self.time+=milliseconds
        for player in self.players:
            if player.respawn_at and self.time >= player.respawn_at:
                self._spawn(player)
            if player.reload_at and self.time >= player.reload_at:
                count=min(self.weapon.clip_size-player.clip,player.reserve)
                player.clip+=count
                player.reserve-=count
                player.reload_at=0
                player.animation=(player.animation^0x400)&0x400
                player.event(27)
        for command in commands:
            self._command(self.players[0],command)
        if self.bot:
            self._command(self.players[1],self._bot_command())

    def snapshot(self):
        player=self.players[0]
        weapon_time=max(0,(player.reload_at or player.next_fire)-max(player.command_time,self.time))
        fields={0:player.command_time,1:player.event_sequence,3:weapon_time,
                8:_word(player.origin[0]),9:player.animation,10:_word(player.origin[2]),11:_word(player.origin[1]),
                13:_word(player.velocity[1]),14:_word(player.velocity[0]),16:_word(player.velocity[2]),
                17:8 if player.reload_at else 6 if weapon_time else 0,
                18:_word(player.yaw),19:_word(player.pitch),28:0 if player.health else 0x20000,
                30:_word(1),34:_word(60),38:60,
                39:self.weapon.index,47:player.ground,54:0x1000,56:self.hands_model,59:0,
                60:SPEED,63:GRAVITY,68:2047,83:0 if player.health else 8,
                85:player.spawn_time,217:_word(1)}
        for i,event in enumerate(player.events):
            fields[21+i]=event
        entities=[]
        for p in self.players:
            values={8:0 if p.health else 0x20000,12:1,16:p.command_time,
                    24:_word(p.origin[0]),28:_word(p.origin[1]),32:_word(p.origin[2]),
                    60:_word(p.pitch),64:_word(p.yaw),136:p.ground,156:p.number,
                    172:p.event_sequence,208:self.weapon.index | self.weapon.index << 16}
            for i,event in enumerate(p.events):
                values[176+i*8]=event
            entities.append((p.number,values))
        entities.extend(self.static_entities)
        entities.sort(key=lambda row:row[0])
        clients=[(p.number,{20:self.body_model}) for p in self.players]
        wire=encode_snapshot(fields,server_time=self.time,health=player.health,spawn_count=player.spawn_count,
            inventory=Inventory(self.weapon.index,self.weapon.ammo_type,self.weapon.clip_type,player.clip,player.reserve,
                                player.weapon_raised),
            entities=entities,clients=clients,position_base=self.position_base)
        return wire,fields
