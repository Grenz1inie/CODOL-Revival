"""Synthetic loopback test tickets; never supplies an online account credential.
Tiger implementation follows LibTomCrypt's Unlicense reference:
https://github.com/libtom/libtomcrypt/blob/develop/src/hashes/tiger.c
"""
from pathlib import Path
import os
import struct,time,base64,json,sys
from cryptography.hazmat.primitives.ciphers import Cipher,modes
from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
root=Path(os.environ['CODOL319_SERVER_ROOT'])
raw=(root/'iips-memory/codoMP_client_shipRetail.exe.9076736.bin').read_bytes()
offset=raw.index(struct.pack('<Q',0x02AAB17CF7E90C5E))
tables=struct.unpack_from('<1024Q',raw,offset)
MASK=(1<<64)-1
def tiger(message):
    padded=message+b'\x01'+bytes((55-len(message))%64)+struct.pack('<Q',len(message)*8)
    state=[0x0123456789ABCDEF,0xFEDCBA9876543210,0xF096A5B4C3B2E187]
    def schedule(x):
        x[0]=(x[0]-(x[7]^0xA5A5A5A5A5A5A5A5))&MASK;x[1]^=x[0];x[2]=(x[2]+x[1])&MASK
        x[3]=(x[3]-(x[2]^((~x[1]&MASK)<<19)))&MASK;x[4]^=x[3];x[5]=(x[5]+x[4])&MASK
        x[6]=(x[6]-(x[5]^((~x[4]&MASK)>>23)))&MASK;x[7]^=x[6];x[0]=(x[0]+x[7])&MASK
        x[1]=(x[1]-(x[0]^((~x[7]&MASK)<<19)))&MASK;x[2]^=x[1];x[3]=(x[3]+x[2])&MASK
        x[4]=(x[4]-(x[3]^((~x[2]&MASK)>>23)))&MASK;x[5]^=x[4];x[6]=(x[6]+x[5])&MASK
        x[7]=(x[7]-(x[6]^0x0123456789ABCDEF))&MASK
    for pos in range(0,len(padded),64):
        x=list(struct.unpack_from('<8Q',padded,pos));s=state.copy()
        for indices,mul in [([0,1,2],5),([2,0,1],7),([1,2,0],9)]:
            if mul!=5:schedule(x)
            for j,word in enumerate(x):
                a,b,c=[indices[(j+k)%3] for k in range(3)]
                s[c]^=word;v=s[c]
                s[a]=(s[a]-(tables[v&255]^tables[256+((v>>16)&255)]^tables[512+((v>>32)&255)]^tables[768+((v>>48)&255)]))&MASK
                s[b]=((s[b]+(tables[768+((v>>8)&255)]^tables[512+((v>>24)&255)]^tables[256+((v>>40)&255)]^tables[(v>>56)&255]))*mul)&MASK
        state=[s[0]^state[0],(s[1]-state[1])&MASK,(s[2]+state[2])&MASK]
    return struct.pack('<3Q',*state)
def response(request):
    sys.path.insert(0,str(root));from local_profile319 import player_name
    # The client base64-decodes the Demonware user name before storing it in dw_username
    # (007F2E1B -> 007F3440; only the literal "HostUser" is taken as is), so the ticket and
    # extra_data carry base64(UTF-8 name). A plain (non-base64) name decodes to garbage.
    name=base64.b64encode(player_name().encode('utf-8'))
    seed=int(request['iv_seed']);now=int(time.time());session=b'Local319DiagnosticKey123'
    assert len(session)==24
    ticket=struct.pack('<IBIIIQQ',0xEFBDADDE,0,1,now,now+3600,0,1000001)+(name+b'\0').ljust(64,b'\0')+session
    ticket=ticket.ljust(128,b'\0');assert len(ticket)==128
    enc=Cipher(TripleDES(tiger(bytes(16))),modes.CBC(tiger(struct.pack('<I',seed))[:8])).encryptor()
    encrypted=enc.update(ticket)+enc.finalize()
    b64=lambda b:base64.b64encode(b).decode('ascii')
    return {'auth_task':33,'code':700,'iv_seed':seed,'client_ticket':b64(encrypted),'server_ticket':b64(bytes(128)),
            'extra_data':json.dumps({'username':name.decode('ascii'),'encrypted_codoid':b64(bytes(16)),'encrypted_register_codoid_data':b64(bytes(16))})}
if __name__=='__main__':
    assert tiger(b'').hex()=='3293ac630c13f0245f92bbb1766e16167a4e58492dde73f3'
    assert tiger(b'abc').hex()=='2aab1484e8c158f2bfb8c5ff41b57a525129131c957b5f93'
    print('Tiger reference vectors passed; synthetic response bytes',len(json.dumps(response({'iv_seed':1}))))
