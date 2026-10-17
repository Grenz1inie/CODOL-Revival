import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

destination = Path('A:/codol319-rebuild-20261017')
source = Path('E:/Games/3.19.26.22/CODOL_FINAL/CODOL_FINAL/使命召唤OL_final/使命召唤OL_final')
if len(sys.argv) == 1:
    repo = Path(__file__).resolve().parents[2]
    destination.mkdir()
    names = subprocess.check_output(['git','ls-files','-z'], cwd=repo).decode().split('\0')
    names += subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z','--',
                                     'games/codol/versions/v3_19_26_22'], cwd=repo).decode().split('\0')
    for name in set(names)-{''}:
        original = repo/name
        if original.is_file():
            target = destination/'repo'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original,target)
    shutil.copy2(__file__, destination/'verify.py')
    result = subprocess.run([sys.executable,'-B',str(destination/'verify.py'),'run'], cwd=destination/'repo',
        env={**os.environ,'PYTHONPATH':str(destination/'repo'),'CODOL319_CC':'A:/Coding/MinGW/bin/gcc.exe'})
    raise SystemExit(result.returncode)

sys.path.insert(0,str(destination/'repo'))
from games.codol.versions.v3_19_26_22.client import preparation, native_build, boot_assets, settings

blocked = []
allowed = [destination.resolve(),source.resolve(),Path(sys.base_prefix).resolve(),
           Path(os.environ['SystemRoot']).resolve(),Path(os.environ['TEMP']).resolve()]
def audit(event,args):
    if event not in ('open','os.listdir','os.scandir') or not args or not isinstance(args[0],(str,bytes,os.PathLike)):
        return
    p = Path(os.fsdecode(args[0])).resolve()
    if not any(p == a or p.is_relative_to(a) for a in allowed):
        blocked.append(str(p))
        raise PermissionError('Fresh verification forbids external input: '+str(p))
sys.addaudithook(audit)
runtime = destination/'runtime'
resumed = (runtime/'game-copy.ready').exists()
inputs = {name: preparation.digest(source/name) for name in boot_assets.SOURCE_HASHES}
before = {str(p.relative_to(source)):(p.stat().st_size,p.stat().st_mtime_ns) for p in source.rglob('*') if p.is_file()}
started = time.monotonic()
game = preparation.prepare(source,runtime)
duration = time.monotonic()-started
assert not (runtime/'server/profile319.json').exists()
assert not (runtime/'server/local-profiles319').exists()
assert preparation.digest(game/preparation.CLIENT)==preparation.CLIENT_SHA256
assert preparation.digest(game/boot_assets.ARCHIVE)=='ac5e1d194833cbedfe0e9d8b476b2e1d9f93414d01e0e49601a80abfe89ea981'
wallet = runtime/'server/local-profiles319/wallet.json'
wallet.parent.mkdir()
wallet.write_text('{"1":123,"2":7}')
profile = runtime/'server/profile319.json'
profile.write_text('{"name":"VerifyPlayer","experience":4321}')
save = game/'players/verification-save.bin'
save.write_bytes(b'keep this player data')
os.environ['CODOL319_CC']='missing-compiler-for-cache-test'
started = time.monotonic()
preparation.prepare(source,runtime)
repeat = time.monotonic()-started
assert wallet.read_text()=='{"1":123,"2":7}'
assert profile.read_text()=='{"name":"VerifyPlayer","experience":4321}'
assert save.read_bytes()==b'keep this player data'
after = {str(p.relative_to(source)):(p.stat().st_size,p.stat().st_mtime_ns) for p in source.rglob('*') if p.is_file()}
assert before==after
assert inputs=={name: preparation.digest(source/name) for name in inputs}
assert not blocked, blocked
manifest = json.loads((runtime/'generated/boot319/boot-build.json').read_text())
result = {'prepare_seconds':duration,'resumed_after_fixture_error':resumed,'repeat_without_compiler_seconds':repeat,'source_files_unchanged':len(before),
          'source_hashes':inputs,'generated':manifest['outputs'],'forbidden_reads':blocked,
          'native_outputs':list(native_build.OUTPUTS),'progress_preserved':True,'fresh_server_profile':True}
(destination/'result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2),flush=True)
