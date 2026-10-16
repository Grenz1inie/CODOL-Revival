# SPDX-License-Identifier: AGPL-3.0-or-later
"""Construct the one-map simulation from a self-contained, verified package."""
import json
from dataclasses import replace
from pathlib import Path

from .collision import CollisionWorld
from .loadout import read_weapon
from .mapdata import load_map
from .navigation import Navigation
from .snapshot import baseline_entities
from .world import World
from .matchmaking import IndependentMatchmaking


def load_world(directory):
    package=load_map(directory)
    manifest,files=package['manifest'],package['files']
    if manifest['map'] not in ('mp_killhouse_sh','mp_nuked') or manifest['gametype']!='dm':
        raise ValueError('only Killhouse or Nuketown DM is supported')
    if not manifest.get('physics_ready') or package['geometry'] is None:
        raise ValueError('map collision is not ready')
    loadout=json.loads(files['loadout.json'])
    for key,kind in (('weapon','13'),('body','0'),('hands','0')):
        item=loadout[key]
        row=package['ncs']['registry']['kinds'][kind]
        if item['index']!=row['reserved']+row['strings'].index(item['name']):
            raise ValueError('loadout resource index differs from current registry')
    collision=CollisionWorld(package['geometry'])
    navigation=Navigation.from_csv(files['waypoints.csv'].decode('ascii'),collision)
    weapon=read_weapon(files[loadout['weapon']['header']],index=loadout['weapon']['index'])
    registry=package['ncs']['registry']['kinds']['13']
    composed=registry['reserved']+len(registry['strings'])
    if composed>=registry['capacity']:
        raise ValueError('no composed weapon slot after the stock registry')
    # 0x42c05a inherits the base ammo key; 0x42c253 gives this rifle its own clip.
    weapon=replace(weapon,index=composed,clip_type=composed)
    world=World(collision,[s for s in package['spawns'] if s['classname']=='mp_dm_spawn'],weapon,
        body_model=loadout['body']['index'],hands_model=loadout['hands']['index'],
        position_base=package['position']['position_base'],navigation=navigation,
        static_entities=baseline_entities(files['baseline.bin']))
    # Resolve the initial route/geometry cache before exposing the UDP endpoint.
    world.bot_path=navigation.route(world.players[1].origin,world.players[0].origin)
    world.bot_repath_at=world.time+500
    return world


def load_matchmaking(directory, *, port=28970, record=None):
    world=load_world(directory)
    manifest=json.loads((Path(directory)/'manifest.json').read_text(encoding='utf-8'))
    ncs=json.loads((Path(directory)/'ncs.json').read_text(encoding='utf-8'))
    # Stock acr_mp renders tag_origin. The native ** recipe selects its model table.
    recipe=(ncs['registry']['kinds']['13']['base']+world.weapon.index,world.weapon.ammo_type,0,0,())
    return IndependentMatchmaking(world,netconst_checksum=ncs['registry']['checksum'],
                                  recipes=(recipe,),port=port,record=record,map_name=manifest['map'])
