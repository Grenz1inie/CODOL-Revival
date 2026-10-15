"""One-human loopback UDP endpoint, owned entirely by the independent server.

SPDX-License-Identifier: AGPL-3.0-or-later
"""
import socket
import threading

from .connection import Connection
from .transport import Association


class MatchServer:
    def __init__(self, uid, security_id, security_key, *, netconst_checksum,
                 configstrings=(), aliases=(), recipes=(), port=0):
        self.uid, self.sid, self.security = uid, security_id, security_key
        self.map_state = dict(netconst_checksum=netconst_checksum,
                             configstrings=configstrings, aliases=aliases, recipes=recipes)
        self.connection = Connection(uid, **self.map_state)
        # Check reservation material before acquiring a socket/thread.
        Association(security_id, security_key, ('127.0.0.1', 1))
        self.association = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1', port))
        self.socket.settimeout(0.1)
        self.port = self.socket.getsockname()[1]
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self._serve, name='codol-independent-match', daemon=True)
        self.last_error = None
        self.rejected_packets = 0

    def _serve(self):
        while not self.stopping.is_set():
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
                    responses = [self.association.encrypt(value) for value in self.connection.receive(plain)]
                for response in responses:
                    self.socket.sendto(response, address)
            except ValueError as error:
                self.last_error = str(error)
                self.rejected_packets += 1

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
