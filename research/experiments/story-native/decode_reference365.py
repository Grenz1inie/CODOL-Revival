# Research-only copy: FF365 header; same verified client RSA material and all signature/hash checks.
"""Read CODOL 3.3.3.3 signed FF423 using the matching client's embedded material.

REA consumers: 0x4847e0 header, 0x4843f0 material, 0x483e90 block verification.
This restores the zone byte stream; it does not port zone structs or run scripts.
"""
import hashlib
import zlib

import pefile
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

CLIENT_SHA256 = 'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b'
BLOCK = 0x2000


def decode(client, wire, map_name):
    if hashlib.sha256(client).hexdigest() != CLIENT_SHA256:
        raise ValueError('client hash mismatch')
    if wire[:12] != b'IWff0100\x6d\x01\0\0' or len(wire) < 277 + 3 * BLOCK or (len(wire) - 277) % BLOCK:
        raise ValueError('unsupported/truncated signed FF423')
    pe = pefile.PE(data=client, fast_load=True)
    key = serialization.load_der_private_key(pe.get_data(0x859fa0, 0x4a7), None)
    verifier = serialization.load_der_public_key(pe.get_data(0x85a448, 0x10e))
    pe.close()
    material = key.decrypt(wire[21:277], padding.PKCS1v15())
    if len(material) != 40:
        raise ValueError('invalid FF material length')

    def decrypt_block(data, iv):
        counter = int.from_bytes(iv, 'little')
        counters = b''.join(((counter + i) % (1 << 128)).to_bytes(16, 'little')
                            for i in range(len(data) // 16))
        encryptor = Cipher(algorithms.AES(material[:24]), modes.ECB()).encryptor()
        stream = encryptor.update(counters) + encryptor.finalize()
        return (int.from_bytes(stream, 'little') ^ int.from_bytes(data, 'little')).to_bytes(len(data), 'little')

    header = decrypt_block(wire[277:277 + BLOCK], material[24:])
    if header[:8] != b'IWffs100' or hashlib.sha256(header[0x12c:0x1fd0]).digest() != header[12:44]:
        raise ValueError('signed header hash mismatch')
    # Client 0x4844e0 copies at most 31 bytes to its 32-byte comparison buffer.
    if header[0x12c:0x14c] != map_name.encode('ascii')[:31].ljust(32, b'\0'):
        raise ValueError('signed map name mismatch')
    try:
        verifier.verify(header[44:300], header[12:44], padding.PKCS1v15(), utils.Prehashed(hashes.SHA256()))
    except InvalidSignature as error:
        raise ValueError('header signature mismatch') from error
    packed = bytearray()
    position = 277 + BLOCK
    group = 0
    while position < len(wire):
        expected = header[0x150 + group * 32:0x170 + group * 32]
        if group >= 244:
            raise ValueError('hash table count exceeds signed header')
        table = decrypt_block(wire[position:position + BLOCK], expected[:16])
        if hashlib.sha256(table).digest() != expected:
            raise ValueError('hash table mismatch')
        position += BLOCK
        for index in range(256):
            if position == len(wire):
                break
            expected = table[index * 32:(index + 1) * 32]
            block = decrypt_block(wire[position:position + BLOCK], expected[:16])
            if hashlib.sha256(block).digest() != expected:
                raise ValueError('data block hash mismatch')
            packed.extend(block)
            position += BLOCK
        group += 1
    inflater = zlib.decompressobj()
    zone = inflater.decompress(packed, 512 * 1024 * 1024 + 1)
    if not inflater.eof or inflater.unconsumed_tail or len(zone) > 512 * 1024 * 1024:
        raise ValueError('invalid/oversized zone zlib stream')
    return zone
