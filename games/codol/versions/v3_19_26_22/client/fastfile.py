"""Verify and decode original FF461 using material in the matching game EXE.

3.19 consumers: 0x483a50 (material), 0x4834f0 (signed blocks), 0x483df0 (version).
No key or decrypted game archive is distributed with this module.
"""
import hashlib
import struct
import zlib

import pefile
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

CLIENT_SHA256 = '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537'
BLOCK = 8192
LIMIT = 256 * 1024 * 1024


def keys(client):
    if hashlib.sha256(client).hexdigest() != CLIENT_SHA256:
        raise ValueError('3.19 client hash mismatch')
    with pefile.PE(data=client, fast_load=True) as image:
        private = serialization.load_der_private_key(image.get_data(0x9ac4b0, 1191), None)
        public = serialization.load_der_public_key(image.get_data(0x9ac958, 270))
    return private, public


def crypt(data, key, iv):
    value = int.from_bytes(iv, 'little')
    counter = b''.join(((value+i) % (1 << 128)).to_bytes(16, 'little')
                       for i in range((len(data)+15)//16))
    encoder = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    stream = (encoder.update(counter) + encoder.finalize())[:len(data)]
    return (int.from_bytes(data, 'little') ^ int.from_bytes(stream, 'little')).to_bytes(len(data), 'little')


def decode(wire, name, private, public):
    if wire[:12] != b'IWff0100\xcd\x01\0\0' or len(wire) < 277+3*BLOCK or (len(wire)-277) % BLOCK:
        raise ValueError('Unsupported or truncated signed FF461')
    material = private.decrypt(wire[21:277], padding.PKCS1v15())
    if len(material) != 40:
        raise ValueError('Invalid FF461 material')
    header = crypt(wire[277:277+BLOCK], material[:24], material[24:])
    if header[:8] != b'IWffs100' or hashlib.sha256(header[300:8144]).digest() != header[12:44]:
        raise ValueError('FF461 header hash mismatch')
    if header[300:332] != name.encode('ascii')[:31].ljust(32, b'\0'):
        raise ValueError('FF461 asset name mismatch')
    try:
        public.verify(header[44:300], header[12:44], padding.PKCS1v15(), utils.Prehashed(hashes.SHA256()))
    except InvalidSignature as error:
        raise ValueError('FF461 header signature mismatch') from error
    position, group = 277+BLOCK, 0
    inflater, zone = zlib.decompressobj(), bytearray()
    while position < len(wire):
        if group >= 244:
            raise ValueError('FF461 hash table count exceeds header')
        expected = header[336+group*32:368+group*32]
        table = crypt(wire[position:position+BLOCK], material[:24], expected[:16])
        if hashlib.sha256(table).digest() != expected:
            raise ValueError('FF461 table hash mismatch')
        position += BLOCK
        for index in range(256):
            if position == len(wire):
                break
            expected = table[index*32:(index+1)*32]
            block = crypt(wire[position:position+BLOCK], material[:24], expected[:16])
            if hashlib.sha256(block).digest() != expected:
                raise ValueError('FF461 data hash mismatch')
            zone.extend(inflater.decompress(block, LIMIT-len(zone)+1))
            if len(zone) > LIMIT or inflater.unconsumed_tail:
                raise ValueError('FF461 zone exceeds size limit')
            position += BLOCK
        group += 1
    if not inflater.eof:
        raise ValueError('Truncated FF461 zlib stream')
    return bytes(zone)


def raw_files(zone):
    # FF461's per-asset records contain serialized sizes. The boot raw-file
    # zones have no script string list, so no engine relocation is needed.
    if len(zone) < 56 or struct.unpack_from('<I', zone)[0] != len(zone)-40:
        raise ValueError('Invalid FF461 zone length')
    strings, pointer, count, array = struct.unpack_from('<4I', zone, 40)
    if strings or pointer or array != 0xffffffff or not 0 < count < 1000:
        raise ValueError('Unsupported FF461 raw-file zone')
    position, stream_offset = 56+count*16, 16+count*16
    result = {}
    for i in range(count):
        if 56+(i+1)*16 > len(zone):
            raise ValueError('Truncated FF461 asset index')
        kind, offset, pointer, size = struct.unpack_from('<4I', zone, 56+i*16)
        if kind != 36 or offset != stream_offset or pointer != 0xffffffff or size < 18 or position+size > len(zone):
            raise ValueError('Invalid FF461 raw-file record')
        row = zone[position:position+size]
        name_pointer, compressed, length, data_pointer = struct.unpack_from('<4I', row)
        end = row.find(b'\0', 16)
        if name_pointer != 0xffffffff or data_pointer != 0xffffffff or end < 17 or length > LIMIT:
            raise ValueError('Invalid FF461 raw-file header')
        name, data = row[16:end].decode('ascii'), row[end+1:]
        if name in result:
            raise ValueError('Duplicate FF461 raw-file name')
        if compressed:
            if len(data) != compressed:
                raise ValueError('FF461 raw-file compressed size mismatch')
            inflater = zlib.decompressobj()
            data = inflater.decompress(data, length+1)
            if len(data) != length or not inflater.eof or inflater.unused_data:
                raise ValueError('FF461 raw-file decoded size mismatch')
        elif len(data) != length+1 or data[-1:] != b'\0':
            raise ValueError('FF461 raw-file size mismatch')
        else:
            data = data[:-1]
        result[name] = data
        position += size
        stream_offset += size
    if position != len(zone):
        raise ValueError('Unconsumed FF461 zone bytes')
    return result
