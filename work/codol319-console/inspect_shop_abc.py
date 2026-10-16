"""Read DoABC structures from the decoded local GFX, without executing ActionScript."""
from pathlib import Path
import struct
import json

OUT=Path(__file__).resolve().parent
class Reader:
    def __init__(self,b):self.b=b;self.p=0
    def u8(self):v=self.b[self.p];self.p+=1;return v
    def u(self):
        value=0
        for shift in range(0,35,7):
            b=self.u8();value|=(b&127)<<shift
            if b<128:return value
        return value
    def take(self,n):v=self.b[self.p:self.p+n];self.p+=n;return v
    def vector(self):return [self.u() for _ in range(self.u())]
    def traits(self):
        result=[]
        for _ in range(self.u()):
            name,kind=self.u(),self.u8();v=[self.u(),self.u()]
            if kind&15 in (0,6):
                d=self.u()
                if d:self.u8()
            if kind&64:self.vector()
            result.append((name,kind&15,v))
        return result

def abc(b):
    r=Reader(b);r.take(4)
    for _ in range(2):
        for _ in range(max(0,r.u()-1)):r.u()
    r.take(max(0,r.u()-1)*8)
    strings=['']+[r.take(r.u()).decode('utf-8') for _ in range(max(0,r.u()-1))]
    ns=[None]+[(r.u8(),r.u()) for _ in range(max(0,r.u()-1))]
    sets=[None]+[r.vector() for _ in range(max(0,r.u()-1))]
    names=['*']
    for _ in range(max(0,r.u()-1)):
        k=r.u8()
        if k in (7,13):
            space,name=r.u(),r.u();v=strings[ns[space][1]]+'::'+strings[name]
        elif k in (15,16):v=strings[r.u()]
        elif k in (17,18):v='RTQNameL'
        elif k in (9,14):v=strings[r.u()];r.u()
        elif k in (27,28):v='MultinameL';r.u()
        elif k==29:v=names[r.u()];r.vector()
        else:raise ValueError(('multiname',k,r.p))
        names.append(v)
    methods=[]
    for _ in range(r.u()):
        n=r.u();r.u()
        for _ in range(n):r.u()
        name=strings[r.u()];flags=r.u8()
        if flags&8:
            for _ in range(r.u()):r.u();r.u8()
        if flags&128:
            for _ in range(n):r.u()
        methods.append(name)
    for _ in range(r.u()):
        r.u();n=r.u()
        for _ in range(n*2):r.u()
    n=r.u();classes=[];labels={}
    def traits(label):
        for name,kind,v in r.traits():
            if kind in (1,2,3,5):labels[v[1]]=label+'.'+names[name]
    for _ in range(n):
        name=names[r.u()];r.u();flags=r.u8()
        if flags&8:r.u()
        r.vector();labels[r.u()]=name+'.<init>';traits(name);classes.append(name)
    for name in classes:
        labels[r.u()]=name+'.<static>';traits(name)
    for _ in range(r.u()):r.u();r.traits()
    bodies=[]
    for _ in range(r.u()):
        method=r.u();limits=[r.u() for _ in range(4)];code=r.take(r.u())
        for _ in range(r.u()):
            for _ in range(5):r.u()
        r.traits()
        bodies.append(dict(method=method,label=labels.get(method,methods[method]),limits=limits,code=code.hex()))
    assert r.p==len(b),(r.p,len(b))
    return dict(strings=strings,names=names,classes=classes,methods=bodies)

b=(OUT/'codo319.gfx').read_bytes()
p=8+((5+4*(b[8]>>3)+7)//8)+4
count=0;results=[]
while p<len(b):
    tag=struct.unpack_from('<H',b,p)[0];p+=2
    kind,length=tag>>6,tag&63
    if length==63:length=struct.unpack_from('<I',b,p)[0];p+=4
    data=b[p:p+length];p+=length
    if kind==82:
        end=data.index(b'\0',4)
        if any(s in data for s in (b'IsMarketplaceItemOwned',b'IsPermanentOwnedProduct',b'MarketplaceItemCard',b'MarketplaceItemObj',b'ProductObj')):
            obj=abc(data[end+1:]);obj['offset']=p-length
            (OUT/('shop-abc-%d.json'%count)).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
            results.append(dict(index=count,classes=obj['classes']))
        count+=1
print(json.dumps([r for r in results if any('::ProductObj' in c for c in r['classes'])],indent=2))
