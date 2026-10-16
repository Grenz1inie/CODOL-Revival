# SPDX-License-Identifier: AGPL-3.0-or-later
"""The fixed 423 weapon header, interpreted directly into simulation values.

Current consumers: 0x4253e0 (fire), 0x4230a0/0x4232d0 (reload),
0x424030/0x424260 (ammo). Offsets also documented by codol_weapon_2697.c.
Only the simple rifle loadout is supported; shared ammo/alternate fire waits.
"""
import math
import struct

from .world import Weapon


def read_weapon(header, *, index):
    if len(header)!=0xe28 or type(index) is not int or not 1 <= index <= 1022:
        raise ValueError('invalid current weapon header or index')
    integer=lambda offset:struct.unpack_from('<I',header,offset)[0]
    real=lambda offset:struct.unpack_from('<f',header,offset)[0]
    if any(header[o] for o in (0xd68,0xd69,0xd6a,0xdad)) or integer(0x6b0):
        raise ValueError('minimal rifle requires independent ammo and clip keys')
    if any(integer(o) for o in (0xbb8,0xbbc,0xbc0,0xbc4,0xbd0,0xbd4,0xbd8,0xbdc)):
        raise ValueError('multi-stage damage curve is outside the minimal loadout')
    weapon=Weapon(index,index,index,integer(0xd08),integer(0xd10),integer(0x71c),integer(0x728),
                  integer(0x6dc),integer(0xbc8),real(0xbcc),real(0xbe0))
    if (not 1 <= weapon.clip_size <= 511 or not 1 <= weapon.fire_ms <= 32767
            or not 1 <= weapon.reload_ms <= 32767 or not 1 <= weapon.empty_reload_ms <= 32767
            or not 0 < weapon.minimum_damage <= weapon.damage <= 32767
            or not all(map(math.isfinite,(weapon.full_damage_range,weapon.minimum_damage_range)))
            or not 0 <= weapon.full_damage_range < weapon.minimum_damage_range):
        raise ValueError('invalid rifle parameters')
    return weapon
