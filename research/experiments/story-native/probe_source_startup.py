"""Bounded isolated native-map regression; never launches the game client."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import zlib

STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parents[2]
CLIENT=ROOT.parent/'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
REFERENCE=ROOT.parent/'CODOL-2.6.9.7-Launcher/CODOL-2.6.9.7-Launcher/runtime/game/server2697'
manifest=json.loads((STAGE/'native-build3333.json').read_text())
exe=Path(manifest['executable'])
assert hashlib.sha256(exe.read_bytes()).hexdigest()==manifest['executable_sha256']
assert hashlib.sha256((ROOT/'tools/native/server3333.patch').read_bytes()).hexdigest()==manifest['patch_sha256']
assert hashlib.sha256(CLIENT.read_bytes()).hexdigest()=='e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b'
with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as guard:
    guard.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
    guard.bind(('127.0.0.1',28970))
home=Path(tempfile.mkdtemp(prefix='source-startup-',dir=STAGE))
shutil.copy2(exe,home/'server3333.exe')
shutil.copytree(REFERENCE/'script-overlay2697',home/'scripts')
shutil.copytree(REFERENCE/'scripts/coop',home/'scripts/coop',dirs_exist_ok=True)
v=json.loads((ROOT/'research/evidence/live-netconst-registration423.json').read_text(encoding='utf-8-sig'))
assert v['exe_sha256']==hashlib.sha256(CLIENT.read_bytes()).hexdigest()
names=v['names'];codinfo=v['codinfo_names']
crc=lambda rows:zlib.crc32(''.join(rows).encode('ascii'))
assert crc(names)==v['checksum_seed']
reg=home/'registration423.txt'
reg.write_text(f'codol2697-registration 2 {crc(names):08x} {len(names)} {len(codinfo)} {crc(codinfo):08x}\n'+'\n'.join(names+codinfo)+'\n')
values=dict(dedicated='1',fs_basepath=str(STAGE/'startup-assets'),fs_homepath=str(home),
    codol_clientExe=str(CLIENT),codol_target2697='1',codol_target2697Registration=str(reg),
    codol_zonePath=str(STAGE/'startup-assets/chinese'),loc_language='11',net_ip='127.0.0.1',net_port='28970',
    sv_webadmin='0',logfile='2',developer='1',sv_maxclients='1',onlinegame='1',xblive_privatematch='1',
    fs_game='coop',codol_zoneType='coop',codol_sessionMap='coop_training_mp_cargoship',g_gametype='coop',
    scr_codol_bots='0',scr_codol_botfill='0',codol_admissionRequired='1',codol_profilePath='',
    codol_scriptPath=str(REFERENCE/'scripts'),codol_scriptOverlay=str(REFERENCE/'scripts'),
    codol_scriptNativeOverlay=str(home/'scripts'))
command=[str(home/'server3333.exe')]
for key,value in values.items():command+=['+set',key,value]
command+=['+map','mp_cargoship','+codol_checktargetpublication']
env={k:v for k,v in os.environ.items() if not k.startswith('CODOL_')}
env['CODOL_ARCHIVE_TRACE']='1'
with (home/'console.log').open('wb') as output:
    process=subprocess.Popen(command,cwd=home,env=env,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW)
    ready=False;reason='timeout';end=time.monotonic()+40
    try:
        while time.monotonic()<end:
            if process.poll() is not None:reason=f'exit {process.returncode}';break
            text='\n'.join(p.read_text(errors='backslashreplace') for p in home.rglob('qconsole.log'))
            if 'Calculate referenced files checksums...' in text and 'actual_client_crc=1' in text:
                ready=True;reason='map publication ready';break
            if (home/'sys_error.txt').exists():reason='sys_error';break
            if 'CoDOL native startup archives mounted' in text and ('map mount failed' in text or 'ERROR:' in text):
                reason='map initialization failed';break
            time.sleep(.3)
    finally:
        if process.poll() is None:process.terminate()
        process.wait(timeout=10)
result=dict(command=command,home=str(home),reason=reason,ready=ready,executable_sha256=manifest['executable_sha256'],
    patch_sha256=manifest['patch_sha256'],returncode=process.returncode,gameplay_verified=False)
(home/'probe.json').write_text(json.dumps(result,indent=2))
(ROOT/'research/evidence/server3333-startup-latest.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
for name in ['console.log','main/qconsole.log','sys_error.txt']:
    p=home/name
    if p.exists():print(name+'\n'+p.read_text(errors='backslashreplace')[-6500:])
assert ready,reason
