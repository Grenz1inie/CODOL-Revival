"""One owned loopback native server, prepared from the verified 423 build."""
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


CLIENT_SHA256 = 'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b'


class NativeServer:
    def __init__(self, root, port=28970, *, mode='story'):
        if mode not in ('story', 'pvp'):
            raise ValueError('unsupported native mode')
        self.root = Path(root).resolve()
        self.port = port
        self.mode = mode
        self.map_name = 'mp_killhouse_sh' if mode == 'pvp' else 'mp_cargoship'
        self.session_map = self.map_name if mode == 'pvp' else 'coop_training_mp_cargoship'
        self.home = None
        self.process = None
        self._published = False
        self.reason = 'not started'

    @property
    def ready(self):
        return bool(self._published and self.process is not None and self.process.poll() is None)

    def start(self, *, security_id: bytes, profile_path: Path,
              admission_path: Path, key_path: Path):
        """Wait up to 40 seconds for publication; empty path strings are probe-only."""
        if self.process is not None and self.process.poll() is None:
            raise RuntimeError('native server already started')
        if not isinstance(security_id, bytes) or len(security_id) != 8:
            raise ValueError('security ID must contain 8 bytes')
        if type(self.port) is not int or not 1 <= self.port <= 65535:
            raise ValueError('port must be between 1 and 65535')
        self._published = False
        stage = self.root / 'research/experiments/story-native'
        client = self.root.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
        reference = self.root.parent / 'CODOL-2.6.9.7-Launcher/CODOL-2.6.9.7-Launcher/runtime/game/server2697'
        self.manifest = json.loads((stage / 'native-build3333.json').read_text())
        exe = Path(self.manifest['executable'])
        assert hashlib.sha256(exe.read_bytes()).hexdigest() == self.manifest['executable_sha256']
        assert hashlib.sha256((self.root / 'games/codol/versions/v3_3_3_3/reverse/tools/native/server3333.patch').read_bytes()).hexdigest() == self.manifest['patch_sha256']
        assert hashlib.sha256(client.read_bytes()).hexdigest() == CLIENT_SHA256
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as guard:
            guard.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            guard.bind(('127.0.0.1', self.port))
        self.home = home = Path(tempfile.mkdtemp(prefix='source-startup-', dir=stage))
        shutil.copy2(exe, home / 'server3333.exe')
        shutil.copytree(reference / 'script-overlay2697', home / 'scripts')
        shutil.copytree(reference / 'scripts/coop', home / 'scripts/coop', dirs_exist_ok=True)
        # Change only the isolated loadout; retain the supplied callbacks/spawn flow.
        loadout = home / 'scripts/coop/maps/mp/gametypes/_coopmode.gsc'
        text = loadout.read_text()
        start = text.index('resolveLoadout()\n{')
        end = text.index('\ngiveStartingLoadout()', start)
        text = text[:start] + '''resolveLoadout()
{
    precacheItem( "defaultweapon_mp" );
    level.coop_primary = "defaultweapon_mp";
    level.coop_secondary = undefined;
    level.coop_melee = undefined;
    println( "CoDOL minimal loadout: defaultweapon_mp" );
}
''' + text[end:]
        loadout.write_text(text)
        shutil.copy2(self.root / 'games/codol/versions/v3_3_3_3/reverse/tools/native/minimal_cargoship.gsc', home / 'scripts/coop/maps/mp/mp_cargoship.gsc')
        if self.mode == 'pvp':
            waypoints = home / 'main/waypoints'
            waypoints.mkdir(parents=True)
            shutil.copy2(reference / 'runtime-assets/main/waypoints/mp_killhouse_sh_wp.csv', waypoints)
        v = json.loads((self.root / 'research/evidence/live-netconst-registration423.json').read_text(encoding='utf-8-sig'))
        assert v['exe_sha256'] == hashlib.sha256(client.read_bytes()).hexdigest()
        names, codinfo = v['names'], v['codinfo_names']
        crc = lambda rows: zlib.crc32(''.join(rows).encode('ascii'))
        assert crc(names) == v['checksum_seed']
        reg = home / 'registration423.txt'
        reg.write_text(f'codol2697-registration 2 {crc(names):08x} {len(names)} {len(codinfo)} {crc(codinfo):08x}\n' + '\n'.join(names + codinfo) + '\n')
        # Resolve supplied paths before changing the child's working directory.
        values = dict(dedicated='1', fs_basepath=str(stage / 'startup-assets'), fs_homepath=str(home),
            codol_clientExe=str(client), codol_target2697='1', codol_target2697Registration=str(reg),
            codol_zonePath=str(stage / 'startup-assets/chinese'), loc_language='11', net_ip='127.0.0.1', net_port=str(self.port),
            sv_webadmin='0', logfile='2', developer='1', sv_maxclients='1', onlinegame='1', xblive_privatematch='1',
            fs_game='coop', codol_zoneType='coop', codol_sessionMap='coop_training_mp_cargoship', g_gametype='coop',
            scr_codol_bots='0', scr_codol_botfill='0', codol_admissionRequired='1',
            codol_securityId=security_id.hex(),
            codol_securityKeyPath=str(Path(key_path).resolve()) if key_path else '',
            codol_admissionPath=str(Path(admission_path).resolve()) if admission_path else '',
            codol_profilePath=str(Path(profile_path).resolve()) if profile_path else '',
            codol_scriptPath=str(reference / 'scripts'), codol_scriptOverlay=str(reference / 'scripts'),
            codol_scriptNativeOverlay=str(home / 'scripts'))
        if self.mode == 'pvp':
            values.update(sv_maxclients='2', fs_game='', codol_zoneType='mp',
                          codol_sessionMap='', g_gametype='dm',
                          scr_codol_bots='1', sv_botDifficulty='regular')
        self.command = [str(home / 'server3333.exe')]
        for key, value in values.items():
            self.command += ['+set', key, value]
        self.command += ['+map', self.map_name, '+codol_checktargetpublication']
        env = {k: v for k, v in os.environ.items() if not k.startswith('CODOL_')}
        env['CODOL_ARCHIVE_TRACE'] = '1'
        try:
            with (home / 'console.log').open('wb') as output:
                self.process = subprocess.Popen(self.command, cwd=home, env=env,
                    stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW)
            self.reason = 'timeout'
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    self.reason = f'exit {self.process.returncode}'
                    break
                text = '\n'.join(p.read_text(errors='backslashreplace') for p in home.rglob('qconsole.log'))
                if (home / 'sys_error.txt').exists():
                    self.reason = 'sys_error'
                    break
                if 'With the reason: Server crashed:' in text:
                    self.reason = 'server crashed'
                    break
                if 'CoDOL native startup archives mounted' in text and 'map mount failed' in text:
                    self.reason = 'map initialization failed'
                    break
                # Recoverable Pathnode diagnostics also contain "ERROR:".
                if 'Calculate referenced files checksums...' in text and 'actual_client_crc=1' in text:
                    self._published = True
                    if self.ready:
                        self.reason = 'map publication ready'
                        return self
                time.sleep(max(0, min(.3, deadline - time.monotonic())))
            raise RuntimeError(self.reason)
        except BaseException:
            self.close()
            raise

    def close(self):
        """Stop only this instance's child; retain its home and exit evidence."""
        self._published = False
        if self.process is None or self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=10)
