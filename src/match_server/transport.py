"""Current bdDTLS framing. Source references and attribution: NOTICE.md.

SPDX-License-Identifier: AGPL-3.0-or-later
"""
import hashlib
import hmac
import secrets
import socket
import struct

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def _export_public(key):
    point = key.public_key().public_numbers()
    body = b'\x03\x02\x07\0\x02\x01\x1c'
    for value in (point.x, point.y):
        raw = value.to_bytes(28, 'big')
        raw = (b'\0' if raw[0] & 128 else b'')+raw
        body += b'\x02'+bytes([len(raw)])+raw
    return (b'\x30'+bytes([len(body)])+body).ljust(100, b'\0')


def _import_public(data):
    if len(data) != 100 or data[0] != 0x30 or not 13 <= data[1] <= 69 or data[2:9] != b'\x03\x02\x07\0\x02\x01\x1c':
        raise ValueError('invalid P-224 public key header')
    end, cursor, xy = data[1]+2, 9, []
    for _ in range(2):
        if cursor+2 > end or data[cursor] != 2:
            raise ValueError('invalid P-224 coordinate')
        size = data[cursor+1]
        cursor += 2
        if not 1 <= size <= 29 or cursor+size > end or data[cursor] & 128:
            raise ValueError('invalid P-224 coordinate size')
        if size == 29 and (data[cursor] or not data[cursor+1] & 128):
            raise ValueError('invalid P-224 sign byte')
        xy.append(int.from_bytes(data[cursor:cursor+size], 'big'))
        cursor += size
    if cursor != end or any(data[end:]):
        raise ValueError('invalid P-224 trailing data')
    return ec.EllipticCurvePublicNumbers(*xy, ec.SECP224R1()).public_key()


class Association:
    def __init__(self, security_id, security_key, peer):
        if len(security_id) != 8 or len(security_key) != 16:
            raise ValueError('invalid reservation material')
        if peer[0] != '127.0.0.1' or not 0 < peer[1] <= 65535:
            raise ValueError('only a loopback peer is supported')
        self.sid, self.security, self.peer = security_id, security_key, peer
        self.init = self.init_ack = self.echo = self.cookie_ack = None
        self.private = self.key = None
        self.received = self.sent = 0

    def handshake(self, packet):
        if len(packet) == 16 and packet[:6] == b'\x01\x02'+bytes(4):
            client_tag, = struct.unpack_from('<H', packet, 6)
            if not client_tag or packet[8:] != self.sid:
                raise ValueError('invalid INIT reservation')
            if packet == self.init:
                return self.init_ack
            self.private = ec.generate_private_key(ec.SECP224R1())
            self.local_tag = secrets.randbelow(65535)+1
            self.remote_tag = client_tag
            ack = bytearray(38)
            struct.pack_into('<BBH', ack, 0, 2, 2, client_tag)
            struct.pack_into('<HHH', ack, 14, self.local_tag, self.local_tag, client_tag)
            ack[24:28] = socket.inet_aton(self.peer[0])
            struct.pack_into('<H', ack, 28, self.peer[1])
            ack[30:] = self.sid
            self.init, self.init_ack = packet, bytes(ack)
            self.echo = self.cookie_ack = self.key = None
            self.received = self.sent = 0
            return self.init_ack
        if len(packet) != 189 or self.init is None:
            raise ValueError('invalid handshake message')
        if self.echo is not None:
            if packet != self.echo:
                raise ValueError('COOKIE changed after establishment')
            return self.cookie_ack
        if (packet[:6] != struct.pack('<BBHH', 3, 2, self.local_tag, 0)
                or packet[6:44] != self.init_ack or packet[81:89] != self.sid):
            raise ValueError('invalid COOKIE echo')
        public = _import_public(packet[89:])
        # Client 0xa7af90: SHA-1(shared X || reservation key), AES uses 16 bytes.
        self.key = hashlib.sha1(self.private.exchange(ec.ECDH(), public)+self.security).digest()
        self.cookie_ack = struct.pack('<BBHH', 4, 2, self.remote_tag, 0)+_export_public(self.private)+self.sid
        self.private = None
        self.echo = packet
        return self.cookie_ack

    def _crypt(self, data, counter, tag):
        # DATA writer 0xa7f960 includes the destination tag in the IV seed.
        iv = int.from_bytes(hashlib.sha1(struct.pack('<IH', counter, tag)).digest()[:16], 'little')
        aes = Cipher(algorithms.AES(self.key[:16]), modes.ECB()).encryptor()
        stream = aes.update(b''.join(((iv+i) % (1 << 128)).to_bytes(16, 'little')
                                    for i in range((len(data)+15)//16)))+aes.finalize()
        return bytes(a ^ b for a, b in zip(data, stream))

    def encrypt(self, plain):
        if self.key is None or len(plain) > 65491 or self.sent == 0xffffffff:
            raise ValueError('DATA channel unavailable or payload too large')
        self.sent += 1
        header = struct.pack('<BBHH', 6, 2, self.remote_tag, self.sent & 65535)
        cipher = self._crypt(plain, self.sent, self.remote_tag)
        body = struct.pack('<H', len(cipher))+cipher
        return header+hmac.digest(self.key, header+body, 'sha1')[:8]+body

    def decrypt(self, packet):
        if self.key is None or len(packet) < 16 or packet[:4] != struct.pack('<BBH', 6, 2, self.local_tag):
            raise ValueError('invalid DATA channel')
        if struct.unpack_from('<H', packet, 14)[0] != len(packet)-16:
            raise ValueError('invalid DATA length')
        if not hmac.compare_digest(packet[6:14], hmac.digest(self.key, packet[:6]+packet[14:], 'sha1')[:8]):
            raise ValueError('invalid DATA authentication')
        low, = struct.unpack_from('<H', packet, 4)
        counter = (self.received & ~65535) | low
        if counter+32768 < self.received:
            counter += 65536
        elif counter > self.received+32768 and counter >= 65536:
            counter -= 65536
        if not self.received < counter <= 0xffffffff:
            raise ValueError('replayed DATA record')
        plain = self._crypt(packet[16:], counter, self.local_tag)
        self.received = counter
        return plain
