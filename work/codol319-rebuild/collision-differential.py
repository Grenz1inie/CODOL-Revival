import json,os,random,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root))
from games.codol.versions.v3_19_26_22.client.native_build import build
native=build(Path(__file__).with_name('native'))/'collision319.exe'
old=root/'runtime/packages/codol-3.19.26.22/server/match-host/mainframe-verification/collision319.exe'
capture=root/'runtime/packages/codol-3.19.26.22/server/match-host/collision319/config319-27572-clipmap.bin'
rng=random.Random(319)
requests=[]
for i in range(140):
 x,y,z=1370+rng.uniform(-1400,1400),-384+rng.uniform(-1400,1400),rng.uniform(100,800)
 if i%3==0:end=(x,y,z-1000)
 else:end=(x+rng.uniform(-100,100),y+rng.uniform(-100,100),z+rng.uniform(-100,100))
 mode=['C','T','M'][i%3]
 ext=(15,0,70) if mode=='C' else (-15,-15,0,15,15,50) if mode=='T' else ()
 requests.append(mode+' '+' '.join('%.4f'%v for v in (x,y,z,*end,*ext)))
results=[]
for exe in (old,native):
 start=time.monotonic()
 r=subprocess.run([str(exe),str(capture)],input='\n'.join(requests)+'\n',capture_output=True,text=True,timeout=60)
 print(exe.name,exe.parent.name,r.returncode,round(time.monotonic()-start,3),r.stderr[:500],flush=True)
 results.append(r.stdout.splitlines())
assert results[0][0]==results[1][0], [r[:1] for r in results]
differences=[]
for request,expected,actual in zip(requests,results[0][1:],results[1][1:]):
 a,b=expected.split(),actual.split()
 if a[4:]!=b[4:] or any(abs(float(x)-float(y))>.001 for x,y in zip(a[:4],b[:4])):
  differences.append([request,expected,actual])
out={'requests':len(requests),'ready':results[0][0],'differences':differences}
Path(__file__).with_name('collision-differential.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
