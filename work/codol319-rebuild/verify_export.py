import json
from pathlib import Path
import sys
import time
import traceback

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(repo))
from games.codol.versions.v3_19_26_22.client.resource_export import export_common, validate_common

target = Path(__file__).parent/'live-generated'
started = time.monotonic()
try:
    export_common(target, {'pid':47740,'created':1792194718.37381},
                  repo/'runtime/instances/codol-3.19.26.22-911c42a0027c/game/codoMP_client_shipRetail.exe')
    manifest = validate_common(target)
    result = {'ok':True,'seconds':time.monotonic()-started,'manifest':manifest,
              'items':len(json.loads((target/'item-registry319.json').read_text())['items'])}
except BaseException:
    result = {'ok':False,'seconds':time.monotonic()-started,'error':traceback.format_exc()}
(Path(__file__).parent/'live-export-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
