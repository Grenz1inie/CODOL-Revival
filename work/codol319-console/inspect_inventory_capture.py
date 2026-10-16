"""Verify captured loopback framing/HMAC and locate the real 80/230 response."""
from collections import defaultdict
import hashlib
import hmac
import json
from pathlib import Path
import struct
import subprocess
import sys
import zlib

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0,str(REPO/'games/codol/versions/v3_19_26_22/server'))
from lsg_codec import decode

capture = Path(sys.argv[1]).resolve()
rows = subprocess.check_output(['E:/Tools/Wireshark/tshark.exe','-r',str(capture),
    '-Y','tcp.port == 31901 && tcp.len > 0','-T','fields',
    '-e','tcp.stream','-e','tcp.srcport','-e','tcp.seq_raw','-e','tcp.payload'],text=True)
streams = defaultdict(lambda:defaultdict(list))
for row in rows.splitlines():
    stream,port,seq,payload = row.split('\t')
    streams[stream]['server' if port=='31901' else 'client'].append((int(seq),bytes.fromhex(payload.replace(':',''))))

def reassemble(parts):
    start = min(seq for seq,_ in parts)
    data = bytearray()
    for seq,part in sorted(parts):
        offset = seq-start
        assert offset<=len(data), 'TCP capture gap'
        overlap = min(len(data)-offset,len(part))
        assert data[offset:offset+overlap]==part[:overlap], 'Conflicting TCP retransmit'
        data.extend(part[overlap:])
    return bytes(data)

def frames(data):
    result=[]; offset=0
    while offset<len(data):
        if offset+4>len(data):return result, {'offset':offset,'captured_bytes':len(data)-offset,'declared_size':None}
        size=struct.unpack_from('<I',data,offset)[0]
        if offset+4+size>len(data):return result, {'offset':offset,'captured_bytes':len(data)-offset-4,'declared_size':size,'header_hex':data[offset:offset+26].hex()}
        result.append(data[offset:offset+4+size]);offset+=4+size
    return result, None

results=[]
for stream,parts in streams.items():
    if set(parts)!={'client','server'}:continue
    client,server = reassemble(parts['client']),reassemble(parts['server'])
    if client[:16]!=struct.pack('<4I',200,200,210,220):continue
    hello=client[:28]
    client_frames,client_partial=frames(client[28:])
    server_frames,server_partial=frames(server)
    auth,greeting = client_frames[0],server_frames[0]
    assert auth[4:6]==b'\xab\x82' and greeting[4:6]==b'\xab\x81'
    prk=hmac.new(hashlib.sha1(hello[8:]+greeting+auth[:-8]).digest(),b'Local319DiagnosticKey123',hashlib.sha1).digest()
    challenge=hmac.new(prk,b'CLIENTCHAL\x01',hashlib.sha1).digest()[:16]
    assert auth[-8:]==challenge[:8]
    assert server_frames[1][4:]==b'\xab\x83'+challenge[8:]
    keys=b'';previous=b''
    for i in range(1,5):
        previous=hmac.new(prk,previous+b'BDDATA'+bytes([i]),hashlib.sha1).digest();keys+=previous
    reverse_keys=keys[20:40]+keys[:20]+keys[56:72]+keys[40:56]
    requests=[];replies=[];assets=[]
    for frame in client_frames[1:]:
        if len(frame)==4:continue
        kind,body=decode(frame[4:],keys)
        if kind==0x86:requests.append({'service':body[0],'task':body[2],'body_hex':body.hex()})
    for frame in server_frames[2:]:
        if len(frame)==4:continue
        kind,body=decode(frame[4:],reverse_keys)
        if kind!=1:continue
        txn,error,task=struct.unpack_from('<Q',body,1)[0],struct.unpack_from('<I',body,10)[0],body[15]
        replies.append({'transaction':txn,'error':error,'task':task,'body_bytes':len(body)})
        if task==230 and error==0 and len(body)>26:
            path=capture.with_name(f'{capture.stem}-assets-stream-{stream}.bin');path.write_bytes(body[26:])
            payload=body[26:]
            raw=payload
            compressed=payload[0]==0x16
            if compressed:
                assert payload[1]==payload[6]==payload[11]==8
                algorithm,raw_size,packed_size=[struct.unpack_from('<I',payload,o)[0] for o in (2,7,12)]
                assert algorithm==50 and packed_size==len(payload)-16
                raw=zlib.decompress(payload[16:])
                assert len(raw)==raw_size
            count=struct.unpack_from('<I',raw,31)[0]
            assert len(raw)==40+48*count
            ids=[struct.unpack_from('<I',raw,36+48*i)[0] for i in range(count)]
            owned=json.loads((REPO/'runtime/instances/codol-3.19.26.22-911c42a0027c/server/local-profiles319/owned_items.json').read_text())
            assets.append({'path':str(path),'sha256':hashlib.sha256(body[26:]).hexdigest(),
                           'body_bytes':len(body),'result_count':struct.unpack_from('<I',body,17)[0],
                           'total_results':struct.unpack_from('<I',body,22)[0],
                           'frame_bytes':len(frame),'compressed':compressed,'raw_bytes':len(raw),
                           'inventory_count':count,'matches_persisted_items':ids==owned,
                           'first_ids':ids[:3],'last_ids':ids[-3:]})
    results.append({'stream':stream,'client_frames':len(client_frames),'server_frames':len(server_frames),
                    'handshake_verified':True,'complete_encrypted_frame_hmacs_verified':True,
                    'client_partial_frame':client_partial,'server_partial_frame':server_partial,
                    'requests':requests,'replies':replies,'assets':assets})
report={'capture':str(capture),'capture_sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),
        'version':'3.19.26.22','exe_sha256':'36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537',
        'streams':results,'unverified':'Other services and full game state machine; UI usability'}
capture.with_suffix('.decoded.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'streams':[{'stream':r['stream'],'requests':len(r['requests']),'assets':r['assets'],'partial':r['server_partial_frame']} for r in results]}))
