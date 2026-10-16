"""Full current snapshots from independent state, without a legacy layout.

Wire algorithms adapted from codol_2697_{arrays,entities,clients,delta}.c in
the archived 423 adaptation; SPDX-License-Identifier: AGPL-3.0-or-later.
"""
from dataclasses import dataclass
import math
import struct

from story_wire423 import MATCH_FIELDS as TABLES, _Message, _player_value, _write_player_fields


@dataclass(frozen=True)
class Inventory:
    weapon: int
    ammo_type: int
    clip_type: int
    clip: int
    reserve: int
    raised: bool = False


def _float(word):
    value = struct.unpack('<f',struct.pack('<I',word))[0]
    if not math.isfinite(value):
        raise ValueError('nonfinite snapshot coordinate')
    return value


def _delta(m, bits, value, center):
    if type(value) is not int or not 0 <= value < 1 << (64 if bits == -94 else 32):
        raise ValueError('snapshot field out of range')
    if bits in (-83,-82,-81):
        lo = center[{-83:0,-82:1,-81:2}[bits]]-32768
        v = math.floor(_float(value)+0.5)
        if not lo <= v <= lo+65535 or not lo <= 0 <= lo+65535:
            raise ValueError('position outside map encoding range')
        m.bits(1,1)
        m.bits(int(-lo) ^ int(v-lo),16)
    elif bits in (-79,-87,-100):
        if bits != -87:
            m.bits(0,2)
        m.data.extend(struct.pack('<H',round(_float(value)*182.04444885253906)&65535))
    elif bits in (-80,-78,-73,-71):
        m.data.extend(struct.pack('<I',value))
    elif bits in (-74,-72):
        m.bits(1,1)
        m.data.extend(struct.pack('<I',value))
    elif bits == -77:
        if value > 255:
            raise ValueError('entity type out of range')
        m.data.append(value)
    elif bits == -76:
        if value > 127 and value < 0xffffff80:
            raise ValueError('signed byte out of range')
        m.bits(0,1)
        m.data.append(value&255)
    elif bits == -96:
        if value > 2047:
            raise ValueError('entity reference out of range')
        m.bits(value == 2046,1)
        if value != 2046:
            m.bits(value == 0,1)
            if value:
                m.bits(value&7,3)
                m.data.append(value>>3)
    elif bits == -98:
        if value > 0x3fffffff:
            raise ValueError('entity flags out of range')
        m.bits(1,1)
        m.bits(value,30)
    elif bits == -55:
        if value > 8191:
            raise ValueError('packed player flags out of range')
        m.bits(bool(value&127),1)
        if value&127:
            m.bits(value&15,4)
            m.bits((value>>4)&7,3)
        m.bits(bool(value&0x1f80),1)
        if value&0x1f80:
            m.bits(value>>12,1)
            m.bits((value>>7)&31,5)
    elif bits in (-94,-93):
        event,parameter = (value&0xffffffff,value>>32) if bits == -94 else (0,value)
        if event >= len(TABLES['event_widths']):
            raise ValueError('event out of range')
        width = TABLES['event_widths'][event]
        if parameter >= 1 << width:
            raise ValueError('event parameter out of range')
        if bits == -94:
            m.bits(event != 0,1)
            if event:
                m.data.append(event)
                if width:
                    m.bits(width == 32 or parameter != 0,1)
                    if width < 32 and not parameter:
                        return
        if width == 32:
            m.data.extend(struct.pack('<I',parameter))
        else:
            m.bits(parameter,width)
    else:
        if bits > 0 and value >= 1 << bits:
            raise ValueError('snapshot bit field out of range')
        _player_value(m,bits,0,value)


def _entity(m, values, center):
    kind=values.get(4,1)
    if kind not in (1,6):
        raise ValueError('only player and static mover entities are supported')
    fields = TABLES['entity_player' if kind==1 else 'entity_script_mover']
    if any(offset not in {f[0] for f in fields} for offset in values):
        raise ValueError('unknown player entity field')
    m.bits(0,1)  # Not removed.
    m.bits(1,1)  # Changed, with an explicit type transition from the zero base.
    m.bits(0,1)
    m.bits(len(fields)-1,6)
    for offset,bits,_ in fields:
        m.bits(1,1)  # Consecutive field; no omitted delta fields.
        _delta(m,bits,kind if offset == 4 else values.get(offset,0),center)


def encode_player_entity(values, *, position_base=(0,0,0)):
    m = _Message()
    if values.get(4,1)!=1:
        raise ValueError('expected player entity')
    _entity(m,values,position_base)
    m.data.append(6)
    return bytes(m.data)


def baseline_entities(data):
    if data[:8]!=b'IWCB000\x01' or (len(data)-8)%272 or len(data)>190408:
        raise ValueError('invalid current baseline length/header')
    result=[]
    for start in range(8,len(data),272):
        number,kind=struct.unpack_from('<II',data,start)
        if not 2 <= number < 2047 or kind not in (6,8):
            raise ValueError('unsupported baseline entity')
        # ET_FX (reference entity.h): Nuketown has four ambient effect emitters.
        # Effects are deferred for the frozen DM scope; keep the raw baseline
        # intact and omit these from snapshots, not the static mover geometry.
        if kind==8:
            continue
        values={offset:struct.unpack_from('<Q' if bits==-94 else '<I',data,start+offset)[0]
                for offset,bits,_ in TABLES['entity_script_mover']}
        result.append((number,values))
    result.sort()
    if len({n for n,_ in result})!=len(result):
        raise ValueError('duplicate baseline entity')
    return result


def _inventory(m, health, inventory, spawn_count):
    if type(health) is not int or not 0 <= health <= 32767:
        raise ValueError('health out of range')
    if type(spawn_count) is not int or not 0 <= spawn_count <= 255:
        raise ValueError('spawn count out of range')
    m.bits(1,1)
    m.bits(13,4)  # Health, max health, byte spawn count (0x5a490d..0x5a4967).
    m.data.extend(struct.pack('<hhB',health,100,spawn_count))
    if inventory is None:
        m.bits(0,13)
        return
    for value,limit in ((inventory.weapon,1023),(inventory.ammo_type,1023),
                        (inventory.clip_type,1022),(inventory.clip,511),(inventory.reserve,2047)):
        if type(value) is not int or not 0 <= value <= limit:
            raise ValueError('inventory field out of range')
    m.bits(1,1)  # Clip slot zero, one hand.
    m.bits(0,4)
    m.bits(inventory.clip_type,10)
    m.bits(1,1)
    m.bits(inventory.clip,9)
    m.bits(0,1)
    m.bits(0,1)  # End clip list.
    m.bits(1,1)  # Owned weapon, slot zero. Ownership is separate from its flags.
    m.bits(1,1)
    m.bits(1,1)
    m.bits(inventory.weapon,10)
    # Used-before, dual-wield, fast-mag, and two rechamber flags. The plain
    # single-hand ACR has only used-before after the client first selects it.
    m.bits(int(inventory.raised),5)
    m.bits(0,14)
    m.bits(1,1)  # Reserve slot zero.
    m.bits(0,4)
    m.bits(inventory.ammo_type,10)
    m.bits(inventory.reserve,11)
    m.bits(0,1)
    m.bits(0,10)  # No additional state, objectives or HUD updates.


def _number(m, number, previous):
    delta = number-previous
    m.bits(delta == 1,1)
    if delta != 1:
        m.bits(delta >= 512,1)
        m.bits(number if delta >= 512 else delta,11 if delta >= 512 else 9)


def encode_snapshot(player, *, server_time, health, inventory=None, spawn_count=0, entities=(),clients=(),
                    position_base=(0,0,0)):
    for rows,limit in ((entities,2047),(clients,32)):
        numbers = [number for number,_ in rows]
        if any(type(n) is not int or not 0 <= n < limit for n in numbers) or numbers != sorted(set(numbers)):
            raise ValueError('invalid or unordered snapshot players')
    m = _Message()
    # Full world state against Connection's pinned empty baseline. Flag 8 is
    # reserved for that baseline: the shipped draw path skips flags & 0x0a.
    m.data.extend(b'\0'+struct.pack('<I',server_time)+b'\0\0')
    m.bits(0,1)
    _write_player_fields(m,player,{},server_time)
    _inventory(m,health,inventory,spawn_count)
    m.bits(0,2)  # No animation commands or actors.
    previous = -1
    for number,values in entities:
        _number(m,number,previous)
        _entity(m,values,position_base)
        previous = number
    _number(m,2047,previous)
    previous = -1
    for number,values in clients:
        m.bits(1,1)
        m.bits(number == previous+1,1)
        if number != previous+1:
            m.bits(number,5)
        m.bits(0,1)
        fields=TABLES['client']
        if any(offset not in {f[0] for f in fields} for offset in values):
            raise ValueError('unknown client state field')
        selected=[i for i,(offset,_,_) in enumerate(fields) if values.get(offset,0)]
        m.bits(bool(selected),1)
        if selected:
            m.bits(selected[-1],7)
            last=-1
            for i in selected:
                m.bits(0,i-last-1)
                m.bits(1,1)
                offset,bits,_=fields[i]
                _delta(m,bits,values[offset],position_base)
                last=i
        previous=number
    m.bits(0,2)  # End client list; no glass updates.
    m.data.append(6)
    return bytes(m.data)
