# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish and book one independent map through the existing lobby."""
import base64
import secrets
import threading

from dw_matchmaking import booking_push, server_result, parse_query, parse_room_message
from .server import MatchServer


class IndependentMatchmaking:
    server_id=0x3333000000000001

    def __init__(self, world, *, netconst_checksum, configstrings=(), aliases=(), recipes=(), port=28970, record=None,
                 map_name='mp_killhouse_sh'):
        self.world=world
        self.map_name=map_name
        self.options=dict(netconst_checksum=netconst_checksum,configstrings=configstrings,
            aliases=aliases,recipes=recipes,position_base=world.position_base,port=port,record=record,
            map_name=map_name)
        self.security_id,self.security_key=secrets.token_bytes(8),secrets.token_bytes(16)
        self.owner,self.server=None,None
        self.lock=threading.Lock()

    def find(self, owner, parameters):
        offset,maximum=parse_query(parameters)
        if offset or not maximum:
            return ()
        if type(owner) is not int or not 0 < owner < 1 << 64:
            raise ValueError('booking requires the self-profile owner')
        with self.lock:
            if self.owner not in (None,owner):
                raise ValueError('local instance already belongs to another player')
            if self.server is None:
                self.server=MatchServer(owner,self.security_id,self.security_key,world=self.world,**self.options)
                self.server.__enter__()
                self.owner=owner
            if not self.server.thread.is_alive():
                return ()
            return (server_result(port=self.server.port,server_id=self.server_id,
                                  security_id=self.security_id,security_key=self.security_key),)

    def message(self, owner, parameters):
        recipient,text=parse_room_message(parameters)
        with self.lock:
            if (owner is None or owner != self.owner or recipient != self.server_id
                    or self.server is None or not self.server.thread.is_alive()):
                raise ValueError('no live reservation for this sender/recipient')
            if text.startswith('mmbook '):
                fields=text.split()
                if (len(fields)!=4 or not fields[1].isdecimal() or not fields[3].isdecimal()
                        or fields[2] != base64.b64encode(self.security_id).decode()):
                    raise ValueError('invalid booking identity')
                return booking_push(self.server_id,b'mmbook accepted')
            if text.startswith('mmstart '):
                commands=[part.strip().split() for part in text[8:].split(';') if part.strip()]
                maps=[c for c in commands if c[0]=='map']
                playlists=[c for c in commands if c[0]=='playlist']
                rotations=[c for c in commands if c[0]=='start_map_rotate_once']
                if playlists or rotations:
                    # 0x6e6bf0 has a playlist-rotation branch without a map command.
                    # Only our single-map FFA entry (240) has an implemented world.
                    if (self.map_name!='mp_nuked' or maps or playlists!=[['playlist','240']]
                            or len(rotations)!=1 or len(rotations[0])!=2
                            or not rotations[0][1].isdecimal() or not 0<int(rotations[0][1])<1<<32):
                        raise ValueError('only the Nuketown test playlist 240 can rotate')
                elif maps != [['map',self.map_name]]:
                    raise ValueError(f'this instance only runs {self.map_name}')
                for command in commands:
                    setting=command[1:] if command[0]=='set' else command
                    if setting[0:1]==['g_gametype'] and setting!=['g_gametype','dm']:
                        raise ValueError('this instance only runs dm')
                # Other client text is never executed as console commands.
                if self.options['record']:
                    self.options['record']('match_start',map=self.map_name,gametype='dm',command=text)
                return None
            raise ValueError('unsupported local booking command')

    def close(self):
        if self.server is not None:
            self.server.close()
