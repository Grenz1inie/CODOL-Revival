"""Decode a mid-session capture using the same TCP connection's captured handshake."""
from collections import defaultdict
import hashlib
import hmac
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'games/codol/versions/v3_19_26_22/server'))
from lsg_codec import decode

def packets(path):
    text = subprocess.check_output(['E:/Tools/Wireshark/tshark.exe', '-r', str(path),
        '-Y', f'tcp.port == {client_port} && tcp.port == 31901 && tcp.len > 0', '-T', 'fields',
        '-e', 'frame.number', '-e', 'frame.time_epoch', '-e', 'tcp.srcport',
        '-e', 'tcp.seq_raw', '-e', 'tcp.payload'], text=True)
    return [(int(n), float(t), p, int(s), bytes.fromhex(b.replace(':', '')))
            for n,t,p,s,b in (line.split('\t') for line in text.splitlines())]

def assemble(rows, port):
    parts = sorted((s,b,n,t) for n,t,p,s,b in rows if p == port)
    start = parts[0][0]
    data = bytearray()
    positions = []
    for s,b,n,t in parts:
        offset = s - start
        assert offset <= len(data), 'TCP gap'
        overlap = min(len(data)-offset, len(b))
        assert data[offset:offset+overlap] == b[:overlap], 'conflicting retransmit'
        data.extend(b[overlap:])
        positions.append((offset,n,t))
    return data, positions

def frames(data, offset=0):
    while offset < len(data):
        size = struct.unpack_from('<I', data, offset)[0]
        assert offset+size+4 <= len(data), 'partial frame'
        yield offset, bytes(data[offset:offset+size+4])
        offset += size+4

capture = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('room-admission.pcapng')
client_port = int(sys.argv[2]) if len(sys.argv)>2 else 35690
rows = packets(capture)
client, cpositions = assemble(rows, str(client_port))
server, spositions = assemble(rows, '31901')
hello = client[:28]
auth_size = struct.unpack_from('<I', client, 28)[0]
auth = bytes(client[28:32+auth_size])
greeting_size = struct.unpack_from('<I', server)[0]
greeting = bytes(server[:4+greeting_size])
assert struct.unpack_from('<4I',hello)==(200,200,210,220)
assert auth[4:6]==b'\xab\x82' and greeting[4:6]==b'\xab\x81'
prk = hmac.new(hashlib.sha1(hello[8:]+greeting+auth[:-8]).digest(), b'Local319DiagnosticKey123', hashlib.sha1).digest()
challenge=hmac.new(prk,b'CLIENTCHAL\x01',hashlib.sha1).digest()[:16]
assert auth[-8:]==challenge[:8]
confirmation=next(frames(server,len(greeting)))[1]
assert confirmation[4:]==b'\xab\x83'+challenge[8:]
keys=previous=b''
for i in range(1,5):
 previous=hmac.new(prk,previous+b'BDDATA'+bytes([i]),hashlib.sha1).digest();keys+=previous
reverse=keys[20:40]+keys[:20]+keys[56:72]+keys[40:56]
messages=[]
for data, positions, direction, secret, start in [(client,cpositions,'client',keys,28+len(auth)),(server,spositions,'server',reverse,len(greeting)+len(confirmation))]:
 for offset,frame in frames(data,start):
  if len(frame)==4: continue
  kind,body=decode(frame[4:],secret)
  _,number,time=max(p for p in positions if p[0]<=offset)
  item={'frame':number,'time':time,'direction':direction,'sequence':struct.unpack_from('<I',frame,6)[0],'kind':kind,'hex':body.hex()}
  if kind==0x86: item.update(service=body[0],task=body[2])
  messages.append(item)
result={'version':'3.19.26.22','exe_sha256':'36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537','capture_sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),'handshake_source':'Full hello/auth/confirmation captured in this PCAP','tcp_client_port':client_port,'all_frame_hmacs_verified':True,'messages':sorted(messages,key=lambda m:m['frame'])}
capture.with_suffix('.decoded.json').write_text(json.dumps(result,indent=2))
print('frames',len(messages),'sha256',result['capture_sha256'])
for m in result['messages']:
 if (m.get('service') in [11,21]) or m['kind']==2: print(m)
