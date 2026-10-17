import hashlib,json,struct,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
from games.codol.versions.v3_19_26_22.tests.test_collision_build319 import clipmap_fixture
old=root/'runtime/packages/codol-3.19.26.22/server/match-host/mainframe-verification/collision319.exe'
capture=Path(__file__).with_name('collision-fixture.bin');capture.write_bytes(clipmap_fixture())
cases=[]
def add(name,mode,start,end,bounds=()):
 cases.append({'name':name,'request':mode+' '+' '.join(str(v) for v in (*start,*end,*bounds))})
add('floor_capsule','C',(0,0,30),(0,0,-30),(15,0,70))
add('floor_box','T',(0,0,30),(0,0,-30),(-15,-15,0,15,15,70))
add('wall_capsule','C',(0,0,10),(100,0,10),(15,0,70))
add('wall_box','T',(0,0,10),(100,0,10),(-15,-15,0,15,15,50))
add('free','C',(0,-300,30),(100,-300,30),(15,0,70))
add('inside','C',(45,0,10),(45,0,10),(15,0,70))
add('escape','C',(45,0,10),(90,0,150),(15,0,70))
add('slope_capsule','C',(-100,0,150),(-100,0,0),(15,0,70))
add('slope_box','T',(-100,0,150),(-100,0,0),(-15,-15,0,15,15,70))
add('corner','C',(15,-230,10),(35,-190,10),(15,0,70))
add('mantle','M',(90,0,0),(110,0,0))
add('mantle_filter','M',(0,0,10),(100,0,10))
add('nonsolid_filter','C',(0,30,10),(0,90,10),(15,0,70))
add('triangle_floor','C',(350,0,100),(350,0,-50),(15,0,70))
add('triangle_floor_box','T',(350,0,100),(350,0,-50),(-10,-10,0,10,10,30))
add('triangle_edge','C',(290,0,100),(290,0,-50),(15,0,70))
add('triangle_reverse_slope','C',(650,0,160),(650,0,-20),(15,0,70))
add('triangle_reverse_box','T',(650,0,160),(650,0,-20),(-10,-10,0,10,10,30))
for i in range(12):
 add('round_corner_'+str(i),'C',(15+i,-220,10),(15+i,-180,10),(15,0,70))
cases.append({'name':'bad_request','request':'C 1 2'})
r=subprocess.run([str(old),str(capture)],input='\n'.join(c['request'] for c in cases)+'\n',capture_output=True,text=True,timeout=10)
print(r.returncode,r.stderr)
lines=r.stdout.splitlines();print(lines)
assert len(lines)==len(cases)+1
for c,l in zip(cases,lines[1:]):c['expected']=l
fixture={'source':'collision319.exe SHA256 '+hashlib.sha256(old.read_bytes()).hexdigest(),
 'geometry_sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),'ready':lines[0],'cases':cases}
(root/'games/codol/versions/v3_19_26_22/tests/fixtures/collision319-reference.json').write_text(json.dumps(fixture,indent=2)+'\n')
