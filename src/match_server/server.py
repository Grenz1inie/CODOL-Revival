"""One-human loopback UDP endpoint, owned entirely by the independent server.

SPDX-License-Identifier: AGPL-3.0-or-later
"""
import socket
import threading
import time

from .connection import Connection
from .transport import Association


class MatchServer:
    def __init__(self, uid, security_id, security_key, *, netconst_checksum,
                 configstrings=(), aliases=(), recipes=(), position_base=(0,0,0),
                 world=None, port=0, record=None):
        self.uid, self.sid, self.security = uid, security_id, security_key
        self.map_state = dict(netconst_checksum=netconst_checksum,
                             configstrings=configstrings, aliases=aliases, recipes=recipes,
                             position_base=position_base)
        self.connection = Connection(uid, **self.map_state)
        self.world, self.pending_inputs, self.next_tick = world, [], None
        self.record=record or (lambda *_args,**_fields:None)
        self.last_report=0
        self.reported_health=None
        # Check reservation material before acquiring a socket/thread.
        Association(security_id, security_key, ('127.0.0.1', 1))
        self.association = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1', port))
        self.socket.settimeout(0.01 if world else 0.1)
        self.port = self.socket.getsockname()[1]
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self._serve, name='codol-independent-match', daemon=True)
        self.last_error = None
        self.rejected_packets = 0

    def _serve(self):
        while not self.stopping.is_set():
            self._tick()
            try:
                packet, address = self.socket.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                if self.stopping.is_set():
                    return
                raise
            try:
                if address[0] != '127.0.0.1':
                    raise ValueError('non-loopback peer')
                if self.association is not None and address != self.association.peer:
                    raise ValueError('reservation already bound to another peer')
                if packet[:1] in (b'\x01', b'\x03'):
                    association = self.association or Association(self.sid, self.security, address)
                    previous = association.init
                    response = association.handshake(packet)
                    if previous != association.init:
                        self.connection = Connection(self.uid, **self.map_state)
                    self.association = association
                    responses = [response]
                else:
                    if self.association is None:
                        raise ValueError('DATA before handshake')
                    plain = self.association.decrypt(packet)
                    previous_phase=self.connection.phase
                    previous_sequence=self.connection.received
                    values=self.connection.receive(plain,reply=self.world is None)
                    if (self.world is not None and self.connection.received > previous_sequence
                            and self.connection.pending_commands):
                        self.pending_inputs.extend(self.connection.pending_commands)
                        if self.connection.phase == 'primed' and plain[4] == self.connection.server_id:
                            self.connection.phase='active'
                            self.next_tick=time.monotonic()+.05
                            # Shipped command handler 0x57d560 case 'a' selects
                            # the granted weapon; the following usercmd confirms it.
                            self.connection.queue_command(f'a {self.world.weapon.index}'.encode())
                            payload,fields=self.world.snapshot()
                            values.extend(self.connection.send(payload,player_fields=fields))
                    if self.connection.phase!=previous_phase:
                        self.record('match_phase',phase=self.connection.phase,
                                    loading_status=self.connection.loading_status,peer=address)
                    responses = [self.association.encrypt(value) for value in values]
                for response in responses:
                    self.socket.sendto(response, address)
            except ValueError as error:
                self.last_error = str(error)
                self.rejected_packets += 1
                self.record('match_rejected',reason=str(error),bytes=len(packet),peer=address)

    def _tick(self):
        if self.next_tick is None or self.connection.phase != 'active':
            return
        now=time.monotonic()
        if now < self.next_tick:
            return
        # One owned clock advances both players, including while no packets arrive.
        self.world.step(self.pending_inputs,milliseconds=50)
        self.pending_inputs=[]
        health=tuple(p.health for p in self.world.players)
        if health!=self.reported_health or now-self.last_report>=5:
            self.record('match_state',server_time=self.world.time,players=[dict(number=p.number,
                origin=p.origin[:],health=p.health,clip=p.clip,kills=p.kills,deaths=p.deaths)
                for p in self.world.players])
            self.reported_health,self.last_report=health,now
        self.next_tick=max(self.next_tick+.05,now)
        payload,fields=self.world.snapshot()
        for packet in self.connection.send(payload,player_fields=fields):
            self.socket.sendto(self.association.encrypt(packet),self.association.peer)

    def __enter__(self):
        self.thread.start()
        return self

    def close(self):
        self.stopping.set()
        if self.thread.is_alive():
            self.thread.join(timeout=1)
        self.socket.close()

    def __exit__(self, *unused):
        self.close()
