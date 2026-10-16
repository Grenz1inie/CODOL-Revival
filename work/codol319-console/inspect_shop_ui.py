"""Decode the local FF461 UI after checking its signed header and block hashes."""
from pathlib import Path
import hashlib
import json
import re
import struct
import zlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
GAME = ROOT / 'runtime/instances/codol-3.19.26.22-911c42a0027c/game'
rdata = (GAME / 'code319-44184-stage6-rdata-00ca8000.bin').read_bytes()
assert hashlib.sha256(rdata).hexdigest() == '0e24e7a86acb4a13d851bad92935cef4169865082a3aca3153970b7687f309b2'
private = serialization.load_der_private_key(rdata[0x1044b0:0x1044b0+1191], None)
public = serialization.load_der_public_key(rdata[0x104958:0x104958+270])
archive = (GAME / 'IIPS/IIPSDownload/ff_init_common_gfx_V109.ifs').read_bytes()
offset = 11188079
wire = archive[offset:]
assert wire[:12] == b'IWff0100\xcd\x01\0\0'
material = private.decrypt(wire[21:277], padding.PKCS1v15())
assert len(material) == 40

def decrypt(data, iv):
    counter = int.from_bytes(iv, 'little')
    counters = b''.join(((counter+i) % (1 << 128)).to_bytes(16, 'little')
                        for i in range(len(data)//16))
    enc = Cipher(algorithms.AES(material[:24]), modes.ECB()).encryptor()
    stream = enc.update(counters) + enc.finalize()
    return (int.from_bytes(data, 'little') ^ int.from_bytes(stream, 'little')).to_bytes(len(data), 'little')

header = decrypt(wire[277:277+8192], material[24:])
assert header[:8] == b'IWffs100'
assert hashlib.sha256(header[300:8144]).digest() == header[12:44]
assert header[300:332] == b'ui_mp'.ljust(32,b'\0')
public.verify(header[44:300], header[12:44], padding.PKCS1v15(), utils.Prehashed(hashes.SHA256()))
position, group, blocks = 277+8192, 0, 0
inflater = zlib.decompressobj()
zone = bytearray()
while not inflater.eof:
    assert group < 244
    expected = header[336+group*32:368+group*32]
    table = decrypt(wire[position:position+8192], expected[:16])
    assert hashlib.sha256(table).digest() == expected
    position += 8192
    for index in range(256):
        expected = table[index*32:(index+1)*32]
        block = decrypt(wire[position:position+8192], expected[:16])
        assert hashlib.sha256(block).digest() == expected
        position += 8192
        zone.extend(inflater.decompress(block))
        blocks += 1
        assert len(zone) < 256*1024*1024
        if inflater.eof:
            break
    group += 1
(OUT / 'ui-zone319.bin').write_bytes(zone)
swfs=[]
for hit in re.finditer(b'(?:CWS|FWS|CFX|GFX)', zone):
    pos=hit.start()
    length=struct.unpack_from('<I',zone,pos+4)[0]
    if not 8 < length < 40*1024*1024 or zone[pos+3] > 32:
        continue
    try:
        data = bytes(zone[pos:pos+length]) if zone[pos:pos+3] in (b'FWS',b'GFX') else bytes(zone[pos:pos+8])+zlib.decompress(zone[pos+8:])
    except zlib.error:
        continue
    if len(data) != length:
        continue
    matches=[m.group().decode('ascii') for m in re.finditer(rb'[A-Za-z][A-Za-z0-9_.]{4,100}',data)
             if any(s in m.group().lower() for s in (b'owned',b'purchase',b'marketplace',b'buysku'))]
    path = OUT / ('ui-swf-%d.bin' % pos)
    path.write_bytes(data)
    swfs.append(dict(offset=pos,bytes=length,context=bytes(zone[max(0,pos-120):pos]).hex(),matches=matches))
result=dict(archive_sha256=hashlib.sha256(archive).hexdigest(),ff_offset=offset,
            header_signature=True,verified_blocks=blocks,zone_bytes=len(zone),
            zone_sha256=hashlib.sha256(zone).hexdigest(),swfs=swfs)
(OUT / 'ui-shop-evidence.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
