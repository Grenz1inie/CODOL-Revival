"""Disassemble saved shop ABC method bytes; never edit the game resource.

Local input avmplus-opcodes.tbl is Adobe's core/opcodes.tbl (MPL 2.0):
https://raw.githubusercontent.com/adobe/avmplus/master/core/opcodes.tbl
SHA256: 8a6ae1d8841761eedeccd0c801709cfd7135f6cc020b4abd37396ec56dde3254
The upstream table and decoded game ABC JSON remain untracked local inputs.
"""
from pathlib import Path
import json
import re
import sys

OUT = Path(__file__).resolve().parent
OPS = {int(hexval, 16): (name, int(count)) for count, name, hexval in re.findall(
    r'^ABC_(?:UNUSED_)?OP(?:_F)?\(\s*(-?\d+),[^\n]*?,\s*(\w+)\)\s*//\s*(0x[0-9A-Fa-f]+)',
    (OUT / 'avmplus-opcodes.tbl').read_text(), re.M)}
NAMES = {4,5,0x45,0x46,0x4a,0x4c,0x4e,0x4f,0x59,0x5d,0x5e,0x5f,0x60,0x61,0x66,0x68,0x6a,0x80,0x86,0xb2}

def instructions(data):
    p = 0
    def u():
        nonlocal p
        v=0
        for shift in range(0,35,7):
            b=data[p];p+=1;v|=(b&127)<<shift
            if b<128:return v
        return v
    def byte():
        nonlocal p
        v=data[p];p+=1;return v
    def s24():
        nonlocal p
        v=int.from_bytes(data[p:p+3],'little',signed=True);p+=3;return v
    while p<len(data):
        start=p;op=byte();name,count=OPS[op]
        assert count>=0,(start,op)
        if 0x0c<=op<=0x1a:
            delta=s24();args=[p+delta]
        elif op==0x1b:
            default=s24();n=u();args=[start+default]+[start+s24() for _ in range(n+1)]
        elif op in (0x24,0x65):args=[byte()]
        elif op==0xef:args=[byte(),u(),byte(),u()]
        else:args=[u() for _ in range(count)]
        yield start,op,name,args

if __name__=='__main__':
    obj=json.loads((OUT/f'shop-abc-{sys.argv[1]}.json').read_text(encoding='utf-8'))
    wanted={int(x) for x in sys.argv[2:]}
    for m in obj['methods']:
        if wanted and m['method'] not in wanted:continue
        print(m['method'],m['label'])
        for p,op,name,args in instructions(bytes.fromhex(m['code'])):
            if op in (0xef,0xf0,0xf1):continue
            label=''
            if op in NAMES:label=obj['names'][args[0]]
            elif op==0x2c:label=repr(obj['strings'][args[0]])
            print(f'{p:04x} {name:18}',','.join(map(str,args)),label)
