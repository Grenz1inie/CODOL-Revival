"""Build one experimental map-load message from this PID's asset capture."""
import json
import os
from pathlib import Path
import re
import subprocess

from config_message319 import gamestate_message
from inspect_config_capture319 import parse_capture
from reconstruct_ncs319 import reconstruct

ROOT=Path(os.environ['CODOL319_SERVER_ROOT']) / 'match-host'


def build_probe(capture_path, *, map_name, game_type, output_dir, numeric=None, extra_literals=None):
    capture_path=Path(capture_path)
    # A complete, freshly written capture ends with this summary line.
    if not capture_path.is_file():return None
    text=capture_path.read_text()
    if not re.search(r'database_nodes=\d+ assets=\d+\n\Z',text):return None
    capture=parse_capture(capture_path)
    prediction,wire=reconstruct(capture)
    output_dir=Path(output_dir)
    ordered=output_dir/'probe-ncs-input.bin';ordered.write_bytes(wire)
    result=subprocess.run([str(ROOT/'mainframe-verification/test_native_ncs319.exe'),
        str(ROOT/'mainframe-verification/config-reader-relocated.bin'),
        str(ROOT.parent/'iips-memory/codoMP_client_shipRetail.exe.9076736.bin'),str(ordered)],
        capture_output=True,text=True,timeout=10,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise ValueError('Native NCS replay failed: '+result.stderr)
    lines=result.stdout.splitlines()
    fields=dict(part.split('=') for part in lines[0].split())
    if fields['checksum'].upper()!=prediction['predicted_checksum_hex'] or lines[1]!='types='+prediction['type_table_hex']:
        raise ValueError('Native and Python NCS predictions disagree')
    # 5C0310 reads mapname and g_gametype from config 0, not config 1.
    # 472990 applies config 1 dvars, 472900 reads server ID from config 3,
    # and 472BE0 reads the config 16 triple. Client-game init 454981..454A28
    # requires config 2 to equal "cod" exactly (error 186 compares expected
    # versus received). No guessed asset index is sent.
    for value in (map_name,game_type):
        if not re.fullmatch('[a-zA-Z0-9_]+',value):raise ValueError('Invalid map/game name')
    # Config 11861 (0x2E55) is the slow-motion state parsed by CG 0060F4A0 with
    # "%i %i %g %g" (start, duration, from, to) at init and on change; it feeds the
    # engine timescale (004FDCC0 -> 004FDE60). Missing, it parsed as timescale 0 and
    # 004FE293 capped the client at ~1 frame/s with 1 ms per frame (live runs
    # 040205Z/041742Z). Duration 0 applies scale 1 immediately.
    literals={0:f'\\mapname\\{map_name}\\g_gametype\\{game_type}\\sv_maxclients\\18',
              1:'\\sv_serverid\\1',2:'cod',3:'1',16:'0 0 0',0x2E55:'0 0 1 1'}
    # Weapon names: config 0x1748+i (CG init 00454A52 walks i=1..0x6A3 through
    # 0059B560; the name must look up to i in the runtime table, else error 181).
    for index,text in (extra_literals or {}).items():
        if index in literals or not 0x1748<index<0x1748+0x6A4 or not re.fullmatch('[a-z0-9_]+',text):
            raise ValueError('Invalid weapon config literal')
        literals[index]=text
    payload=gamestate_message(map_name=map_name,game_type=game_type,
        net_config_checksum=int(prediction['predicted_checksum_hex'],16),
        type_table=bytes.fromhex(prediction['type_table_hex']),literals=literals,numeric=numeric)
    if len(payload)>1024:raise ValueError('Probe requires fragmentation')
    manifest={k:v for k,v in prediction.items() if k not in ('type_table_hex','defaults')}
    manifest.update(map_name=map_name,game_type=game_type,literals=literals,numeric=numeric or {},payload_hex=payload.hex(),
                    payload_bytes=len(payload),experimental=True)
    (output_dir/'probe-gamestate.json').write_text(json.dumps(manifest,indent=2))
    (output_dir/'probe-gamestate.bin').write_bytes(payload)
    return payload,manifest
