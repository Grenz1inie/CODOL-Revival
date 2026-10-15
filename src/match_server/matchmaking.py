# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish and book the independent Killhouse world through the existing lobby."""
import base64
import secrets
import threading

from dw_matchmaking import booking_push, server_result, parse_query, parse_room_message
from .server import MatchServer


class IndependentMatchmaking:
    server_id=0x3333000000000001

    def __init__(self, world, *, netconst_checksum, configstrings=(), aliases=(), recipes=(), port=28970, record=None):
        self.world=world
        self.options=dict(netconst_checksum=netconst_checksum,configstrings=configstrings,
            aliases=aliases,recipes=recipes,position_base=world.position_base,port=port,record=record)
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
                commands=[part.strip().split() for part in text[8:].split(';')]
                maps=[command for command in commands if command and command[0]=='map']
                if maps != [['map','mp_killhouse_sh']]:
                    raise ValueError('this instance only runs mp_killhouse_sh')
                for command in commands:
                    if (len(command)>=2 and command[0]=='set' and command[1]=='g_gametype'
                            and command != ['set','g_gametype','dm']):
                        raise ValueError('this instance only runs dm')
                # Other client text is never executed as console commands.
                return None
            raise ValueError('unsupported local booking command')

    def close(self):
        if self.server is not None:
            self.server.close()
