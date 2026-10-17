import hashlib,json,struct,subprocess
from pathlib import Path
import pefile

root=Path(__file__).resolve().parents[2]
exe=root/'runtime/packages/codol-3.19.26.22/server/match-host/mainframe-verification/snapshot319_live.exe'
client=Path(r'E:\Games\3.19.26.22\CODOL_FINAL\CODOL_FINAL\使命召唤OL_final\使命召唤OL_final\codoMP_client_shipRetail.exe')
raw=client.read_bytes()
game=pefile.PE(str(client))
pe=pefile.PE(str(exe))
r=next(s for s in pe.sections if s.Name.startswith(b'.rdata')).get_data()
fields=lambda offset,count:[list(struct.unpack_from('<HhBx',r,offset+i*6)) for i in range(count)]
player,clients=fields(0x640,246),fields(0x2c0,87)
entities=[fields(0xce0+i*378,63) for i in range(24)]
locations={}
for name,table in [('player',player),('client',clients),*[(f'entity_{i}',v) for i,v in enumerate(entities)]]:
 pattern=b''.join(struct.pack('<Iii',*row) for row in table)
 offset=raw.find(pattern)
 if offset<0:raise ValueError(name)
 locations[name]=hex(game.OPTIONAL_HEADER.ImageBase+game.get_rva_from_offset(offset))
widths=list(r[0xc20:0xc20+185])
offset=raw.find(struct.pack('<185I',*widths))
if offset<0:raise ValueError('event widths')
locations['event_widths']=hex(game.OPTIONAL_HEADER.ImageBase+game.get_rva_from_offset(offset))
definition={'source':{'client_sha256':hashlib.sha256(raw).hexdigest(),'addresses':locations,
 'layout':'netfields: uint32 offset, int32 bits, uint32 hint; events: uint32 widths'},
 'player':player,'client':clients,'entity':entities,'event_widths':widths,
 'living':[list(struct.unpack_from('<III',r,0x200+i*12)) for i in range(10)],
 'allowed':list(struct.unpack_from('<54I',r,0x120))}
(root/'work/codol319-rebuild/snapshot-definition.json').write_text(json.dumps(definition,indent=2)+'\n')
base='1000 1000 1370 -384 248 0 0 0 0 180 0 2046'
cases=[{'name':'initial','request':base},
 {'name':'moving','request':'1200 1180 -1.5 30 300 20 -10 -5 25 359.9 0 2047'},
 {'name':'zero_weapon','request':base+' F39=0 F77=0'},
 {'name':'ammo','request':base+' F900=17 F901=42 F902=78 F56=54 F54=4096'},
 {'name':'events','request':base+' F1=1 F21=54:0 F2=1 F46=25:0'},
 {'name':'weapon_phase','request':base+' F9=3 F3=2200 F17=8 F101=1 F93=1 F35=1000 F36=1100 F172=5'},
 {'name':'aim','request':base+' F41=1065353216 F151=28 F152=2'},
 {'name':'entity_client','request':base+' E1=1400,-384,248,90,187,0,0,1 C1=1,109,110,111'},
 {'name':'multiple_bots','request':base+' E1=1400,-384,248,90,187 E2=1400,-300,248,180,187 C1=1,109 C2=2,109'},
 {'name':'no_entity_fields','request':base+' BM=0 E1=0,0,0,0,0,0,0,1'},
 {'name':'bad_ground','request':base[:-4]+'2048'},
 {'name':'nan','request':'1000 1000 nan 0 0 0 0 0 0 0'},
 {'name':'bad_clip','request':base+' F900=512'},
 {'name':'unknown_override','request':base+' F999=1'}]
cases += [{'name':f'field_{i}', 'request':base+f' F{i}='+str(v)} for i,v in [
 (20,17),(12,32768),(15,20),(102,1000),(114,2),(28,536870912),
 (38,1065353216),(34,1065353216),(92,1),(81,1),(89,1),(115,1),(108,1),
 (113,1),(99,1),(220,1),(193,1),(194,1),(106,1),(151,16383),(152,3),
 (1,255),(2,255),(3,65535),(56,2046),(39,2046),(77,16777215),
 (21,184),(22,54),(23,55),(24,100),(48,25),(49,54),(50,54),
 (900,511),(901,4095),(902,2046)]]
cases += [{'name':f'entity_type_{i}', 'request':base+f' E1=1400,-384,248,90,187,1,2,{i}'} for i in range(24)]
cases += [{'name':'entity_rounding','request':base+' E1=-1.5,0.5,2.5,-90,187'},
 {'name':'entity_overflow','request':base+' E1=32768,0,0,0'},
 {'name':'entity_order','request':base+' E2=0,0,0,0 E1=0,0,0,0'},
 {'name':'client_limit','request':base+' C31=7,1023,1023,1023,1023,1023'},
 {'name':'client_overflow','request':base+' C32=1,2'},
 {'name':'client_order','request':base+' C2=1,109 C1=1,109'},
 {'name':'signed_fields','request':base+' F15=4294967168 F3=4294934528'},
 {'name':'float_sign','request':base+' F114=2147483648'}]
cases += [{'name':'event_parameter','request':base+' F21=54:255'},
 {'name':'ground_none','request':base[:-4]+'2047'},
 {'name':'zero_time','request':'0'+base[4:]},
 {'name':'origin_limit','request':'1000 1000 32767 -32768 0 0 0 0 0 0'},
 {'name':'origin_overflow','request':'1000 1000 32768 0 0 0 0 0 0 0'},
 {'name':'zero_loadout','request':'1000 1000 0 0 0 0 0 0 0 0'}]
for case in cases:
 result=subprocess.run([str(exe),'187','4','5','128'],input=case['request']+'\n',capture_output=True,text=True,check=True,timeout=10)
 lines=result.stdout.splitlines()
 assert len(lines)==1,result.stdout
 case['expected']=lines[0]
fixture={'source':'snapshot319_live.exe SHA256 '+hashlib.sha256(exe.read_bytes()).hexdigest(),
 'arguments':[187,4,5,128],'cases':cases}
fixture['initial_payload_hex']=(exe.parent.parent/'activation-analysis319/initial-snapshot-living-loadout78-arms4-hands5-wf80-v2047-floor.bin').read_bytes().hex()
(root/'games/codol/versions/v3_19_26_22/tests/fixtures/snapshot319-reference.json').write_text(json.dumps(fixture,indent=2)+'\n')
print(json.dumps({'definitions_verified':len(locations),'cases':[(c['name'],c['expected'][:30]) for c in cases]}))
