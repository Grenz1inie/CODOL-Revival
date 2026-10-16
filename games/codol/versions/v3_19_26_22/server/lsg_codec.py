import struct,hashlib,hmac,os
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
def decode(packet,keys):
    if packet[:2]!=b'\xab\x85':raise ValueError('Unexpected encrypted frame marker')
    frame=struct.pack('<I',len(packet))+packet
    expected=hmac.new(keys[:20],frame[:-8],hashlib.sha1).digest()[:8]
    if not hmac.compare_digest(expected,packet[-8:]):raise ValueError('Client frame HMAC mismatch')
    decrypt=Cipher(algorithms.AES(keys[40:56]),modes.CBC(packet[6:22])).decryptor()
    plain=decrypt.update(packet[22:-8])+decrypt.finalize()
    size=struct.unpack_from('<I',plain)[0]
    if size>len(plain)-5:raise ValueError('Plain payload size out of bounds')
    return plain[4],plain[5:5+size]
def encode(kind,body,keys,sequence):
    plain=struct.pack('<I',len(body))+bytes([kind])+body
    plain+=bytes((-len(plain))%16)
    iv=os.urandom(16)
    cipher=Cipher(algorithms.AES(keys[56:72]),modes.CBC(iv)).encryptor()
    content=b'\xab\x85'+struct.pack('<I',sequence)+iv+cipher.update(plain)+cipher.finalize()
    frame=struct.pack('<I',len(content)+8)+content
    return frame+hmac.new(keys[20:40],frame,hashlib.sha1).digest()[:8]
def empty_task_reply(task,transaction,error=0):
    return b'\x0a'+struct.pack('<Q',transaction)+b'\x08'+struct.pack('<I',error)+b'\x03'+bytes([task])+b'\x08'+struct.pack('<I',0)
def empty_task_reply_total(task,transaction,error=0):
    # Same as empty_task_reply plus the totalResults field that result-bearing replies carry
    # (numResults 0, totalResults 0). Lobby option --reply-total.
    return empty_task_reply(task,transaction,error)+b'\x08'+struct.pack('<I',0)
