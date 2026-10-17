r"""Diagnostic 3.19.26.22 local match host (M1 vertical slice).

PURPOSE
  Stand up a loopback UDP endpoint that speaks the 3.19 *connectionless*
  (out-of-band) protocol well enough to answer the client's getchallenge and
  connect, and to LOG every datagram the client sends -- including the first
  netchan (sequenced) packet and any gamestate request. This is the first
  milestone (M1) toward a playable match: proving the isolated 3.19 client
  will actually drive its UDP game path against a host we control.

  This is NOT a simulation server. Default mode accepts the handshake and
  records what the client does next. The explicit experimental flags can
  send three empty sequenced packets and one minimal game-state candidate
  derived from a fresh client asset capture, and optionally one explicit
  initial snapshot payload after gamestateupdate 6. An explicit bounded
  snapshot stream can advance those frames after the client acknowledges
  the initial snapshot. It does not simulate players or bots.

WHAT IS VERIFIED vs ASSUMED
  Verified from the recovered client (iips-memory text/rdata dump):
    - OOB framing: four 0xff bytes + NUL-terminated ASCII text
      (sender 0x675260; challenge parser 0x5c1678..0x5c174e;
       getchallenge formatter 0x5c071f "getchallenge 0 \"%s\"").
    - The client's connectionless command tokens it emits/consumes:
      getchallenge, connect, and it parses challengeResponse / connectReject /
      connectResponse (handler dispatch 0x5c1678, strings at
      0xdbfd04/0xdbfee8/0xdbff0c/0xdbfefc).
  Assumed (CoD4/CODOL-2697 convention; CONFIRM from this run's log, do not
  treat as proven):
    - connect line is:  connect <16-hex xuid> "<userinfo>"
      with challenge= and qport= inside the userinfo string.
    - connectResponse carries \mapname\..\gametype\..\sv_maxclients\..\protocol\..
  The 2697 reference uses protocol 1 / shortversion 1.1.1.13; 3.19's expected
  protocol value is unknown. The host logs the client's challenge/qport and, on
  a protocol/version refusal, the client will send an `error` OOB line that this
  host logs verbatim -- that line is how M1 discovers the correct values.

HOW THE CLIENT REACHES THIS HOST
  The isolated client dials a host over real UDP only once the lobby advertises
  a session whose address resolves to this endpoint, OR via the loopback-bridge
  DLL (client_loopback319.cpp) which routes the client's NA_LOOPBACK "localhost"
  traffic here. See VERTICAL-SLICE-M1.md. This script is the host either way.

SAFETY
  Loopback only. Binds 127.0.0.1. Never writes to the game install or the
  English archive. Pure stdlib.
"""
import os
import argparse, re, socket, struct, sys, time, json, zlib, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
ASSETS = Path(os.environ['CODOL319_SERVER_ROOT']) / 'match-host'
from server_message319 import server_packet, server_command, binary_command, register_weapon_command


# Weapon from the player's own loadout (uploaded player data) instead of --weapon. Class 0 =
# Custom Loadout 1 (the pause-menu class choice is not decoded yet).
USE_LOADOUT = True
MODEL_FALLBACK = True
COMPOSITE_LOADOUT = True  # build the loadout gun as the client does (weapon_composite319): base + parts
# Composite weapon numbers must be registered in order with no gap (client error 181 'expected
# 1136, got 1150'), so loadout guns take the numbers after the file's bin-weapon commands.     # loadout gun without a loaded gun model -> --weapon (visible AN-94)
LOADOUT_CLASS = 0


def reliable_command(sequence, text):
    """Text server command, or a binary one written as "bin-weapon INDEX BASE [CAMO VARIANT ATTACH...]"
    (register composite weapon INDEX built from base weapon BASE, see register_weapon_command)."""
    if text.startswith('bin-weapon '):
        n = [int(v) for v in text.split()[1:]]
        return binary_command(sequence, register_weapon_command(n[0], n[1], *(n[2:4]), attachments=tuple(n[4:])))
    return server_command(sequence, text)


def load_server_commands():
    """server-commands319.txt next to this script: one "SECONDS TEXT" per line, e.g. "6 q 1"
    (open menu configstring 0x12C8+1 = changeclass, handler 00610A30). Each command gets the
    next reliable sequence (1, 2, ...) and is sent once, in the first live frame at or after
    SECONDS (repeating the same sequence stopped the client acknowledging)."""
    path = ASSETS / 'server-commands319.txt'
    out = []
    try:
        for line in path.read_text(encoding='ascii').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            at, text = line.split(None, 1)
            out.append((float(at), text))
    except OSError:
        pass
    return sorted(out, key=lambda c: c[0])  # sequence numbers must follow send order
from snapshot_stream319 import delta_frame
from client_message319 import parse as parse_client_message

OOB = b"\xff\xff\xff\xff"
# getchallenge 0 "<token up to 45 printable chars, no '"'>"
GETCHALLENGE = re.compile(rb'getchallenge 0 "([ -!#-~]{1,45})"\Z')
# connect <16 hex> "<userinfo>"   (userinfo begins with a backslash)
CONNECT = re.compile(rb'connect ([0-9A-Fa-f]{16}) "(\\[ -~]*)"\Z')

# Recovered from this 3.19 client's sender at 0x007F6EC0 and fragment
# selector at 0x007F6DF0. statResponse's numeric argument is consumed at
# 0x005C19B2 and applied by 0x007F6B00. Zero means upload complete.
STATS_PREFIX = OOB + b"stats\x00"
STATS_BYTES = 0x8000
STATS_CHUNK_BYTES = 0x4D6
STATS_RESET_MASK = 0x07FFFFFF


class StatsUpload:
    """One upload; preserve binary trailing NULs and validate before ack 0."""
    def __init__(self, compressed_length):
        self.compressed_length = compressed_length
        if compressed_length > STATS_BYTES:
            raise ValueError("3.19 sender falls back to raw stats above 32768 compressed bytes")
        self.length = compressed_length or STATS_BYTES
        self.count = (self.length + STATS_CHUNK_BYTES - 1) // STATS_CHUNK_BYTES
        if not 1 <= self.count <= 27:
            raise ValueError("stats upload exceeds the client's 27-bit mask")
        self.chunks = {}
        self.profile = None

    def accept(self, index, compressed_length, payload):
        if compressed_length != self.compressed_length:
            raise ValueError("stats length changed during upload")
        if not 0 <= index < self.count:
            raise ValueError("stats fragment index out of range")
        expected = min(STATS_CHUNK_BYTES, self.length - index * STATS_CHUNK_BYTES)
        if len(payload) != expected:
            raise ValueError(f"stats fragment {index}: expected {expected} bytes, got {len(payload)}")
        if index in self.chunks and self.chunks[index] != payload:
            raise ValueError("conflicting duplicate stats fragment")
        self.chunks[index] = payload
        missing = sum(1 << i for i in range(self.count) if i not in self.chunks)
        if missing == 0 and self.profile is None:
            wire = b"".join(self.chunks[i] for i in range(self.count))
            if self.compressed_length:
                decoder = zlib.decompressobj()
                profile = decoder.decompress(wire, STATS_BYTES + 1)
                if (len(profile) != STATS_BYTES or not decoder.eof or
                        decoder.unused_data or decoder.unconsumed_tail):
                    raise ValueError("stats zlib stream must contain exactly 32768 bytes with no trailing data")
            else:
                profile = wire
            self.profile = profile
        return missing


def info_value(userinfo: str, key: str):
    """Read a \\key\\value info string the CoD way (last wins)."""
    parts = userinfo.split("\\")[1:]
    out = None
    for i in range(0, len(parts) - 1, 2):
        if parts[i] == key:
            out = parts[i + 1]
    return out


def challenge_for(peer):
    # Deterministic, non-zero, 31-bit. The client only checks it round-trips.
    h = (hash(peer) ^ 0x51621517) & 0x7fffffff
    return h or 1


class DiagHost:
    def __init__(self, port, mapname, gametype, maxclients, protocol, logdir, sequenced_probe=0, gamestate_capture=None, snapshot_payload=None, snapshot_stream=None, delta_continuation=False, ack_client_commands=False, live_seconds=0, live_origin=(1370.0,-384.0,248.0,180.0), weapon=0, eflags_test=False, viewmodels=(0,0), weapflags=0, collision_map=None):
        if not isinstance(sequenced_probe, int) or not 0 <= sequenced_probe <= 3:
            raise ValueError('Sequenced probe must be 0..3 packets')
        self.snapshot_payload = None
        if snapshot_payload:
            if not gamestate_capture:
                raise ValueError('Initial snapshot probe requires an explicit game-state capture')
            data = Path(snapshot_payload).read_bytes()
            # Structural envelope check only. Native wire validation is done
            # offline; this option must point at the explicitly prepared probe.
            if (not 9 <= len(data) <= 1024 or data[0] != 0 or data[5:7] != b'\0\x08'
                    or data[7] & 1 or data[-1] != 5
                    or not 0 < struct.unpack_from('<I', data, 1)[0] <= 0x7fffffff):
                raise ValueError('Expected an initial full snapshot with flag 8, no prior base, and EOF')
            self.snapshot_payload = data
        self.stream_frames = None
        self.stream_interval = None
        self.stream_sha256 = None
        self.stream_peers = {}
        if delta_continuation and not (snapshot_stream or live_seconds):
            raise ValueError('Delta continuation requires a snapshot stream')
        self.delta_continuation = bool(delta_continuation)
        if ack_client_commands and not (snapshot_stream or live_seconds):
            raise ValueError('Client command acknowledgement requires a snapshot stream')
        self.ack_client_commands = bool(ack_client_commands)
        # Live mode: authoritative movement from decoded usercmds (live_sim319),
        # encoded per tick by snapshot_codec319. Bounded by live_seconds.
        if live_seconds and not (0 < live_seconds <= 900):
            raise ValueError('Live simulation must be bounded to 900 seconds')
        if live_seconds and not (self.snapshot_payload and delta_continuation and ack_client_commands):
            raise ValueError('Live simulation needs the initial snapshot, delta continuation and command acknowledgement')
        self.live_seconds = live_seconds
        self.live_origin = tuple(float(v) for v in live_origin)
        # Weapon definition number from the client's runtime table (weapons319.txt).
        # Player field 39 (+3F8; owner-draw 83 at 0045822B reads it). The client fills
        # weapon-name config 0x1748+N itself from native constant table 13, so the
        # host sends none. The weapon must already be in the initial snapshot: the
        # loader 0059AED0 runs before the first render only on activation (00515894).
        if not isinstance(weapon,int) or not 0 <= weapon < 0x6A4:
            raise ValueError('Weapon must be a definition number in 0..0x6A3')
        self.weapon = weapon
        if len(viewmodels)!=2 or not all(isinstance(v,int) and 0<=v<1024 for v in viewmodels):
            raise ValueError('Invalid viewmodel indices')
        if any(viewmodels) and not weapon:
            raise ValueError('Viewmodels require --weapon')
        self.viewmodels = tuple(viewmodels)
        if not isinstance(weapflags,int) or not 0<=weapflags<1<<24 or (weapflags and not any(viewmodels)):
            raise ValueError('Invalid --weapflags')
        self.weapflags = weapflags
        # Captured clipMap (bridge capture_clipmap319) for host collision; loaded once,
        # shared by every live simulation.
        self.collision = None
        self.server_commands = load_server_commands()
        if collision_map:
            if not live_seconds or not Path(collision_map).is_file():
                raise ValueError('--collision-map needs --live-sim-seconds and an existing file')
            from collision_move319 import Collision
            self.collision = Collision(collision_map)
        # Experiment: 40 s normal, 30 s eFlags 0x400, 30 s eFlags 0x800, then 0.
        self.eflags_test = bool(eflags_test)
        self.weapon_name = None
        if weapon:
            table=dict(line.split(' ',1) for line in (ASSETS/'weapons319.txt').read_text().splitlines()[1:])
            self.weapon_name = table.get(str(weapon))
            # Composite weapons (index above the runtime table) exist once a bin-weapon command
            # in server-commands319.txt registers them.
            composite = {int(t.split()[1]): ' '.join(t.split()[2:]) for _, t in load_server_commands()
                         if t.startswith('bin-weapon ')}
            if not self.weapon_name and weapon in composite:
                self.weapon_name = '** ' + composite[weapon]
            if not self.weapon_name:
                raise ValueError('Weapon number not in weapons319.txt')
        if live_seconds and self.stream_frames is None:
            self.stream_frames = (self.snapshot_payload,)
            self.stream_interval = 0.05
        if snapshot_stream:
            if self.snapshot_payload is None:
                raise ValueError('Snapshot stream requires an explicit initial snapshot')
            from snapshot_stream319 import load_stream
            self.stream_frames,self.stream_interval,self.stream_sha256 = load_stream(snapshot_stream,self.snapshot_payload)
        self.port = port
        self.mapname = mapname
        self.gametype = gametype
        self.maxclients = maxclients
        self.protocol = protocol
        self.logdir = Path(logdir)
        self.logdir.mkdir(parents=True, exist_ok=True)
        self.jsonl = (self.logdir / "diag-host319.jsonl").open("a", encoding="utf-8")
        self.issued = {}          # peer -> challenge
        self.connected = set()    # peers that got a connectResponse
        self.netchan_seen = {}    # peer -> count of sequenced packets
        self.stats_seen = {}      # peer string -> number of stats datagrams
        self.stats_uploads = {}   # peer tuple -> validated fragment assembler
        self.match_pay = False      # real runs only (main sets it): tests drive fake clocks
        self.next_composite = 1 + max([int(t.split()[1]) for _, t in self.server_commands
                                       if t.startswith('bin-weapon ')] or [1135])
        self.profiles = {}
        # composite weapon number -> base weapon (the HUD reads the reserve ammo of the base)
        self.composite_bases = {int(t.split()[1]): int(t.split()[2]) for _, t in self.server_commands
                                if t.startswith('bin-weapon ')}        # peer tuple -> uploaded player data (for the in-match class picker)
        self.loadouts = {}        # peer tuple -> Custom Loadout 1 weapons from the uploaded player data
        self.sequenced_probe = sequenced_probe
        self.probe_sent = {}
        self.connect_challenge = {}
        self.gamestate_capture = Path(gamestate_capture) if gamestate_capture else None
        self.gamestate_sent = set()
        self.gamestate_failed = set()
        self.gamestate_sequences = {}
        self.snapshot_attempted = set()
        self.snapshot_sent = set()

    def emit(self, event, **kw):
        row = dict(event=event, t=round(time.time(), 3), **kw)
        self.jsonl.write(json.dumps(row) + "\n")
        self.jsonl.flush()
        # Binary OOB payloads can contain replacement characters. Keep stdout
        # ASCII-safe even when redirected through Windows' legacy code page.
        print(event, json.dumps({k: v for k, v in kw.items() if k != "hex"}, ensure_ascii=True))

    def oob_text(self, packet):
        """Return the OOB text (bytes, no trailing NUL) or None if not OOB."""
        if len(packet) < 5 or packet[:4] != OOB:
            return None
        body = packet[4:]
        if body.endswith(b"\x00"):
            body = body[:-1]
        return body

    def send(self, sock, peer, text, quiet=False):
        sock.sendto(OOB + text.encode("ascii") + b"\x00", peer)
        if not quiet:
            self.emit("sent", peer=f"{peer[0]}:{peer[1]}", text=text)

    def handle(self, sock, packet, peer):
        key = f"{peer[0]}:{peer[1]}"
        # Keep full packets for offline replay, including binary stats and any
        # first netchan packet. Earlier captures stored only a short prefix.
        self.emit("datagram", peer=key, bytes=len(packet), hex=packet.hex())
        if packet.startswith(STATS_PREFIX):
            self.handle_stats(sock, packet, peer)
            return
        oob = self.oob_text(packet)
        if oob is None:
            # Sequenced (netchan) traffic -- the milestone signal.
            n = self.netchan_seen.get(key, 0) + 1
            self.netchan_seen[key] = n
            seq = struct.unpack_from("<I", packet)[0] if len(packet) >= 4 else None
            self.emit("netchan", peer=key, count=n, bytes=len(packet),
                      seq=seq, hex=packet[:32].hex())
            self.observe_stream_peer(packet,peer)
            upload = self.stats_uploads.get(peer)
            sent = self.probe_sent.get(peer, 0)
            if (self.sequenced_probe and peer in self.connected and upload is not None and
                    upload.profile is not None and sent < self.sequenced_probe and
                    seq is not None and 1 <= seq <= 0x1fffffff and
                    peer in self.connect_challenge):
                # Bounded envelope experiment only: no endless keepalive and no
                # claim that an empty message loads a map. Native state logging
                # must confirm that server_sequence advances to accept it.
                response = server_packet(b'\x05', sequence=sent + 1,
                                         challenge=self.connect_challenge[peer])
                sock.sendto(response, peer)
                self.probe_sent[peer] = sent + 1
                self.emit('sequenced_probe_sent', peer=key, sequence=sent + 1,
                          bytes=len(response), hex=response.hex())
            elif (self.gamestate_capture and peer in self.connected and upload is not None and
                  upload.profile is not None and peer in self.connect_challenge and
                  peer not in self.gamestate_sent and peer not in self.gamestate_failed and
                  seq is not None and 1 <= seq <= 0x1fffffff):
                from gamestate_probe319 import build_probe
                try:
                    probe=build_probe(self.gamestate_capture,map_name=self.mapname,
                                      game_type=self.gametype,output_dir=self.logdir)
                    if probe is not None:
                        payload,manifest=probe
                        response=server_packet(payload,sequence=sent+1,challenge=self.connect_challenge[peer])
                        sock.sendto(response,peer)
                        self.gamestate_sent.add(peer)
                        self.gamestate_sequences[peer] = sent + 1
                        self.emit('gamestate_probe_sent',peer=key,sequence=sent+1,bytes=len(response),
                                  checksum=manifest['predicted_checksum_hex'],hex=response.hex())
                except Exception as ex:
                    self.gamestate_failed.add(peer)
                    self.emit('gamestate_probe_failed',peer=key,error=repr(ex))
            return

        m = GETCHALLENGE.match(oob)
        if m:
            c = challenge_for(peer)
            self.issued[peer] = c
            self.emit("getchallenge", peer=key, client_token=m.group(1).decode("ascii", "replace"))
            self.send(sock, peer, f"challengeResponse {c}")
            return

        m = CONNECT.match(oob)
        if m:
            xuid = m.group(1).decode("ascii")
            userinfo = m.group(2).decode("ascii", "replace")
            ch = info_value(userinfo, "challenge")
            qport = info_value(userinfo, "qport")
            proto = info_value(userinfo, "protocol")
            self.emit("connect", peer=key, xuid=xuid, challenge=ch, qport=qport,
                      protocol=proto, userinfo=userinfo[:300])
            # Answer with a CoD-style connectResponse. If the client refuses it
            # will reply with an `error` OOB line that we log below.
            resp = (f"connectResponse \\mapname\\{self.mapname}"
                    f"\\gametype\\{self.gametype}"
                    f"\\sv_maxclients\\{self.maxclients}"
                    f"\\protocol\\{self.protocol}")
            self.connected.add(peer)
            self.stats_uploads.pop(peer, None)
            self.probe_sent.pop(peer, None)
            self.gamestate_sent.discard(peer)
            self.gamestate_failed.discard(peer)
            self.gamestate_sequences.pop(peer, None)
            self.snapshot_attempted.discard(peer)
            self.snapshot_sent.discard(peer)
            self.stream_peers.pop(peer,None)
            self.connect_challenge.pop(peer, None)
            if ch is not None and ch.isdigit() and 0 <= int(ch) <= 0xffffffff:
                self.connect_challenge[peer] = int(ch)
            self.send(sock, peer, resp)
            return

        if oob == b'gamestateupdate 6' and self.snapshot_payload is not None:
            upload = self.stats_uploads.get(peer)
            if (peer not in self.connected or upload is None or upload.profile is None
                    or peer not in self.gamestate_sequences or peer not in self.connect_challenge):
                self.emit('initial_snapshot_ignored', peer=key, reason='incomplete_same_peer_session')
                return
            if peer in self.snapshot_attempted:
                self.emit('initial_snapshot_ignored', peer=key, reason='one_shot_already_attempted')
                return
            self.snapshot_attempted.add(peer)
            sequence = self.gamestate_sequences[peer] + 1
            response = server_packet(self.snapshot_payload, sequence=sequence,
                                     challenge=self.connect_challenge[peer])
            try:
                sock.sendto(response, peer)
            except OSError as ex:
                self.emit('initial_snapshot_failed', peer=key, sequence=sequence, error=repr(ex))
                return
            self.snapshot_sent.add(peer)
            if self.stream_frames:
                self.stream_peers[peer] = dict(next=1,last_sequence=sequence,initial_sequence=sequence,
                    client_sequence=0,last_ack=0,started=None,last_rx=None,created=time.monotonic(),due=None)
                if self.live_seconds:
                    from live_sim319 import LiveSim
                    self.stream_peers[peer].update(sim=LiveSim(self.live_origin[:3],self.live_origin[3],weapon=self.match_weapon(peer),viewmodels=self.viewmodels,weapflags=self.weapflags,collision=self.collision),
                        base_time=struct.unpack_from('<I',self.snapshot_payload,1)[0],last_time=0)
                    sim_=self.stream_peers[peer]['sim'];sim_.ammo_weapon=self.composite_bases.get(sim_.weapon,0)
            self.emit('initial_snapshot_sent', peer=key, sequence=sequence, bytes=len(response),
                      server_time=struct.unpack_from('<I', self.snapshot_payload, 1)[0],
                      payload_hex=self.snapshot_payload.hex(),
                      payload_sha256=hashlib.sha256(self.snapshot_payload).hexdigest(),
                      hex=response.hex(), simulation=False)
            return

        if oob.startswith(b"error"):
            self.emit("client_error", peer=key, text=oob.decode("ascii", "replace"))
            self.stop_stream(peer,'client_error')
            return

        if oob.startswith(b'disconnect'):
            self.stop_stream(peer,'client_disconnect')

        if oob.startswith(b"rcon") or oob.startswith(b"getstatus") or oob.startswith(b"getinfo"):
            self.emit("oob_other", peer=key, text=oob[:64].decode("ascii", "replace"))
            return

        self.emit("oob_unhandled", peer=key, text=oob[:120].decode("ascii", "replace"),
                  hex=packet[:48].hex())

    def match_weapon(self, peer):
        """Weapon in hand: the player's own Custom Loadout 1 primary when USE_LOADOUT and it maps
        to a runtime weapon, otherwise the --weapon default."""
        lo = self.loadouts.get(peer) if USE_LOADOUT else None
        w = lo and lo.get('primary')
        if w and self.weapon and lo.get('composite'):
            self.emit('match_weapon', peer=f'{peer[0]}:{peer[1]}', weapon=lo['composite'],
                      source='loadout_composite', loadout_weapon=w)
            return lo['composite']
        if w and self.weapon:
            if MODEL_FALLBACK and not self.weapon_has_model(w):
                comp = self.composite_for(w)
                if comp:
                    # A composite registered from this base (server-commands319.txt bin-weapon): the
                    # client builds its model from mp/coWeapModels/<base>.csv (00431810 -> 00430F40,
                    # e.g. m4_mp -> wea_m4_m4_blk / wea_m4_m4_blk_vmgun from common_marketplace_lite).
                    self.emit('match_weapon', peer=f'{peer[0]}:{peer[1]}', weapon=comp,
                              source='composite', loadout_weapon=w)
                    return comp
                # Modular guns (e.g. m4_mp) only have the tag_origin placeholder as gun model in
                # this client (OVERNIGHT-319.md), so the player would hold nothing: use --weapon.
                self.emit('match_weapon', peer=f'{peer[0]}:{peer[1]}', weapon=self.weapon,
                          source='model_fallback', loadout_weapon=w)
                return self.weapon
            self.emit('match_weapon', peer=f'{peer[0]}:{peer[1]}', weapon=w, source='loadout')
            return w
        return self.weapon

    def composite_for(self, base):
        """Lowest composite weapon index registered with this base weapon (bin-weapon INDEX BASE
        CAMO VARIANT ...), preferring camo 0 / variant 0; None if there is none."""
        best = None
        for _, t in load_server_commands():
            f = t.split()
            if f[0] == 'bin-weapon' and len(f) >= 3 and int(f[2]) == base:
                rank = (int(f[3]) if len(f) > 3 else 0, int(f[4]) if len(f) > 4 else 0, int(f[1]))
                if best is None or rank < best[0]:
                    best = (rank, int(f[1]))
        return best[1] if best else None

    def weapon_has_model(self, weapon):
        """False when the client's weapon-definition dump (config319-<pid>-weapdefs.txt, written by
        the bridge next to the game-state capture) shows only the tag_origin placeholder as the
        weapon's gun model; True when unknown."""
        if not self.gamestate_capture:
            return True
        name = self.gamestate_capture.name.replace('-first-netchan.txt', '-weapdefs.txt')
        path = self.gamestate_capture.parent / name
        if not path.exists():
            # Written by the bridge ~1 s after the weapon is chosen; the table is the same for every
            # run of this client build, so the newest earlier dump answers as well.
            dumps = sorted(self.gamestate_capture.parent.glob('config319-*-weapdefs.txt'),
                           key=lambda f: f.stat().st_mtime)
            if not dumps:
                return True
            path = dumps[-1]
        try:
            for line in path.read_text(errors='replace').splitlines():
                f = line.split()
                if len(f) > 3 and f[0] == str(weapon):
                    return '(tag_origin)' not in f[3] and '+10=00000000' not in f[3]
        except OSError:
            pass
        return True

    def stop_stream(self,peer,reason):
        state=self.stream_peers.pop(peer,None)
        if state is not None and state.get('sim') is not None:state['sim'].close()
        if state is not None:
            self.emit('snapshot_stream_stopped',peer=f'{peer[0]}:{peer[1]}',reason=reason,
                      frames_sent=state['next'],last_sequence=state['last_sequence'],last_ack=state['last_ack'])
            # Match pay: GP/CP/XP per minute actually played (local_profile319 economy, wallet.json);
            # live matches only (replayed capture streams have no simulation).
            if state.get('sim') is not None and self.match_pay:
              try:
                import sys as _sys, pathlib as _pl
                _sys.path.insert(0,str(_pl.Path(__file__).resolve().parent.parent))
                import local_profile319
                played=(state.get('last_rx') or time.monotonic())-(state.get('started') or state['created'])
                self.emit('match_pay',seconds=round(played,1),paid=local_profile319.earn(played),wallet=local_profile319.wallet())
              except Exception as ex:
                self.emit('match_pay_failed',error=repr(ex))

    def observe_stream_peer(self,packet,peer):
        state=self.stream_peers.get(peer)
        if state is None:return
        from snapshot_stream319 import client_header
        header=client_header(packet)
        if header is None:return
        seq,ack=header
        if seq<=state['client_sequence'] or not state['initial_sequence']<=ack<=state['last_sequence'] or ack<state['last_ack']:
            return
        now=time.monotonic()
        state.update(client_sequence=seq,last_ack=ack,last_rx=now)
        if self.ack_client_commands:
            # Acknowledge only commands actually received, contiguously, in order.
            # Not executed: logged for later semantics work.
            # The client keys its packets with the server command it last received (header
            # field command_ack = its serverCommandSequence): text as sent, binary ones as '!'.
            client_cmd_seq=struct.unpack_from('<I',packet,9)[0] if len(packet)>=13 else 0
            last_text=state.get('server_cmd_text',{}).get(client_cmd_seq,b'')
            parsed=parse_client_message(packet,challenge=self.connect_challenge.get(peer,0),baseline=state.get('last_cmd'),last_server_command=last_text)
            if parsed is not None and not parsed['error']:
                for number,text in parsed['commands']:
                    if number==state.get('command_ack',0)+1 and number<=0x7fffffff:
                        state['command_ack']=number
                        state['command_text']=text.encode('latin-1')
                        self.emit('client_command',peer=f'{peer[0]}:{peer[1]}',number=number,text=text[:200])
                        self.on_class_choice(peer,state,text)
                if parsed['move']:
                    state['moves']=state.get('moves',0)+1
                    sim=state.get('sim')
                    if 'cmd_error' not in parsed['move'] and parsed['move']['cmds']:
                        state['last_cmd']=parsed['move']['cmds'][-1]
                    if sim is not None and 'cmd_error' not in parsed['move']:
                        for cmd in parsed['move']['cmds']:sim.apply(cmd)
                        if parsed['move'].get('predicted') and getattr(sim,'collision',None):
                            d=sim.reconcile(parsed['move']['predicted'])
                            if d is not None:state['pred_err_max']=max(state.get('pred_err_max',0.0),d)
                    elif sim is not None:
                        state['cmd_errors']=state.get('cmd_errors',0)+1
        if state['started'] is None:
            state.update(started=now,due=now+self.stream_interval)
            self.emit('snapshot_stream_started',peer=f'{peer[0]}:{peer[1]}',ack=ack,
                      frames=len(self.stream_frames),interval_ms=round(self.stream_interval*1000),
                      simulation=False,reliable_ack=0)

    def tick_streams(self,sock,now=None):
        now=time.monotonic() if now is None else now
        for peer,state in list(self.stream_peers.items()):
            if state['started'] is None:
                if now-state['created']>5:self.stop_stream(peer,'initial_ack_timeout')
                continue
            if now-state['last_rx']>3:
                self.stop_stream(peer,'client_silent');continue
            if now-state['started']>(self.live_seconds+5 if self.live_seconds else 185):
                self.stop_stream(peer,'wall_time_limit');continue
            if now<state['due']:continue
            if state['last_sequence']-state['last_ack']>100:
                self.stop_stream(peer,'ack_stalled');continue
            sim=state.get('sim')
            if sim is not None:
                if now-state['started']>self.live_seconds:
                    self.stop_stream(peer,'live_completed');continue
                server_time=max(state['last_time']+1,state['base_time']+50+int((now-state['started'])*1000))
                if self.eflags_test:
                    elapsed=now-state['started']
                    sim.eflags=0x400 if 40<=elapsed<70 else 0x800 if 70<=elapsed<100 else 0
                try:payload=sim.payload(server_time)
                except (OSError,ValueError) as ex:
                    self.emit('live_encode_failed',peer=f'{peer[0]}:{peer[1]}',error=repr(ex))
                    self.stop_stream(peer,'encode_failed');continue
                state['last_time']=server_time;index=state['next']
            else:
                index=state['next'];payload=self.stream_frames[index]
            sequence=state['last_sequence']+1
            delta=0
            if self.delta_continuation:
                payload,delta=delta_frame(payload,sequence,state['last_ack'])
            snapshot_payload=payload
            if sim is not None and self.server_commands:
                elapsed=now-state['started']
                sent_cmds=state.setdefault('sent_commands',set())
                due=[n for n,(at,text) in enumerate(self.server_commands) if at<=elapsed and n not in sent_cmds]
                prefix=b''.join(reliable_command(n+1,self.server_commands[n][1]) for n in due)
                sent_cmds.update(due)
                texts=state.setdefault('server_cmd_text',{})
                for n in due:
                    t=self.server_commands[n][1]
                    texts[n+1]=b'!' if t.startswith('bin-weapon ') else t.encode('latin-1')
                if prefix:
                    payload=prefix+payload
                    if not state.get('commands_logged'):
                        state['commands_logged']=True
                        self.emit('server_commands_sent',peer=f'{peer[0]}:{peer[1]}',commands=[t for _,t in self.server_commands])
            reliable_ack=state.get('command_ack',0) if self.ack_client_commands else 0
            # The client's decoder (00470A60) mixes in the text of its own command
            # selected by this acknowledgement number, so pass that exact text.
            response=server_packet(payload,sequence=sequence,reliable_ack=reliable_ack,
                                   challenge=self.connect_challenge[peer],
                                   reliable_command=state.get('command_text',b'') if reliable_ack else b'')
            try:sock.sendto(response,peer)
            except OSError as ex:
                self.emit('snapshot_stream_send_failed',peer=f'{peer[0]}:{peer[1]}',error=repr(ex))
                self.stop_stream(peer,'send_failed');continue
            state.update(next=index+1,last_sequence=sequence,due=now+self.stream_interval)
            self.emit('snapshot_stream_frame',peer=f'{peer[0]}:{peer[1]}',index=index,
                      sequence=sequence,server_time=struct.unpack_from('<I',snapshot_payload,1)[0],
                      last_ack=state['last_ack'],delta=delta,flags=snapshot_payload[6],reliable_ack=reliable_ack,
                      hex=response.hex(),simulation=sim is not None,
                      **(dict(origin=[round(v,2) for v in sim.origin],yaw=round(sim.yaw,1),pitch=round(sim.pitch,1),
                              command_time=sim.command_time,commands=sim.commands,cmd_errors=state.get('cmd_errors',0),eflags=sim.eflags,
                              ground=sim.ground,reconciled=getattr(sim,'reconciled',0),corrected=getattr(sim,'corrected',0),ring_hits=getattr(sim,'ring_hits',0),ring_misses=getattr(sim,'ring_misses',0),
                              pred_err_max=round(state.pop('pred_err_max',0.0),2),
                              cmd={k:state['last_cmd'].get(k) for k in ('buttons','w14','w16','w18','b20','w22')} if state.get('last_cmd') else None,
                              mantles=getattr(sim,'mantles',0),mantle_log=getattr(sim,'mantle_log',[])[-3:],jumps=getattr(sim,'jumps',0))
                         if sim is not None else {}))
            if sim is None and state['next']==len(self.stream_frames):self.stop_stream(peer,'completed')

    def handle_stats(self, sock, packet, peer):
        key = f"{peer[0]}:{peer[1]}"
        n = self.stats_seen.get(key, 0) + 1
        self.stats_seen[key] = n
        try:
            if len(packet) < 13:
                raise ValueError("truncated stats header")
            index, compressed_length = struct.unpack_from("<BH", packet, 10)
            upload = self.stats_uploads.get(peer)
            if upload is None:
                upload = StatsUpload(compressed_length)
            missing = upload.accept(index, compressed_length, packet[13:])
            self.stats_uploads[peer] = upload
        except (ValueError, zlib.error) as ex:
            self.stats_uploads.pop(peer, None)
            self.emit("stats_rejected", peer=key, count=n, reason=str(ex))
            # This mask resets all 27 client fragment timestamps. In particular
            # never report completion for a truncated or corrupt profile.
            self.send(sock, peer, f"statResponse {STATS_RESET_MASK}")
            return
        self.emit("stats", peer=key, count=n, bytes=len(packet), chunk=index,
                  compressed_length=compressed_length, chunks=upload.count,
                  received_chunks=len(upload.chunks), missing_mask=missing,
                  complete=(upload.profile is not None))
        self.send(sock, peer, f"statResponse {missing}")
        if upload.profile is not None and peer not in self.loadouts:
            self.profiles[peer] = upload.profile
            self.loadouts[peer] = self.loadout_from_profile(key, upload.profile)

    def register_loadout_composite(self, key, weapon, item, attachments):
        """Register '** weapon 0 0 parts...' (the client's own composite for this loadout gun) with a
        bin-weapon server command; returns its weapon number, or None if the parts are unknown."""
        try:
            import weapon_composite319 as wc
            built = wc.compose(item, [a for a in attachments if a])
        except Exception as ex:
            self.emit('loadout_composite_failed', peer=key, error=repr(ex))
            return None
        if not built:
            self.emit('loadout_composite_failed', peer=key, error='unknown weapon item or part', item=item)
            return None
        numbers, names = built
        index = self.next_composite
        self.next_composite += 1
        text = 'bin-weapon %d %d 0 0 %s' % (index, weapon, ' '.join(str(n) for n in numbers))
        # After every scheduled command: reliable sequences and composite numbers stay in order.
        last = max((at for at, _ in self.server_commands), default=0.0)
        self.server_commands.append((last, text))
        self.composite_bases[index] = weapon
        self.emit('loadout_composite', peer=key, weapon=index, base=weapon, parts=names, command=text)
        return index

    def on_class_choice(self, peer, state, text):
        """In-match class picker: 'mr <id> <menu> customN' (Custom Loadout N). Takes that loadout
        from the uploaded player data and gives its primary (or the model fallback) at once."""
        m = re.match(r'mr \d+ \d+ custom(\d+)$', text.strip())
        if not m or peer not in self.profiles:
            return
        slot = int(m.group(1)) - 1
        key = f'{peer[0]}:{peer[1]}'
        lo = self.loadout_from_profile(key, self.profiles[peer], slot)
        if lo is None:
            return
        self.loadouts[peer] = lo
        weapon = self.match_weapon(peer)
        sim = state.get('sim')
        if sim is not None and weapon and weapon != sim.weapon:
            sim.set_weapon(weapon)
            sim.ammo_weapon = self.composite_bases.get(weapon, 0)
        self.emit('class_chosen', peer=key, slot=slot, weapon=weapon)

    def loadout_from_profile(self, key, profile, slot=None):
        """Custom Loadout 1 (weaponClasses[0], playerdata_classes319) from the uploaded player
        data: primary item id -> runtime weapon number. None keeps the --weapon default."""
        try:
            import playerdata_classes319 as pdc
            classes = pdc.classes(profile[4:])
            slot = LOADOUT_CLASS if slot is None else slot
            c = classes[slot]
            primary, pname = pdc.weapon_index(c['primary'])
            secondary, sname = pdc.weapon_index(c['secondary'])
            self.emit('loadout_from_stats', peer=key, slot=slot, primary_item=c['primary'], primary=primary,
                      primary_name=pname, secondary_item=c['secondary'], secondary=secondary, secondary_name=sname,
                      attachments=c['primary_attach'])
            lo = dict(primary=primary, secondary=secondary, cls=c)
            if COMPOSITE_LOADOUT and primary:
                lo['composite'] = self.register_loadout_composite(key, primary, c['primary'], c['primary_attach'])
            return lo
        except Exception as ex:
            self.emit('loadout_from_stats_failed', peer=key, error=repr(ex))
            return None

    def serve(self, seconds, stop_file=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", self.port))
        sock.settimeout(1.0)
        self.emit("listening", addr=f"127.0.0.1:{self.port}",
                  mapname=self.mapname, gametype=self.gametype,
                  protocol=self.protocol, sequenced_probe=self.sequenced_probe,
                  gamestate_capture=str(self.gamestate_capture) if self.gamestate_capture else None,
                  snapshot_payload_bytes=len(self.snapshot_payload) if self.snapshot_payload else 0,
                  snapshot_payload_sha256=hashlib.sha256(self.snapshot_payload).hexdigest()
                    if self.snapshot_payload else None,
                  snapshot_stream_frames=len(self.stream_frames) if self.stream_frames else 0,
                  snapshot_stream_sha256=self.stream_sha256)
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline and not (stop_file and stop_file.exists()):
            self.tick_streams(sock)
            sock.settimeout(min(0.05,self.stream_interval) if self.stream_peers else 1.0)
            try:
                packet, peer = sock.recvfrom(65535)
            except socket.timeout:
                continue
            except ConnectionResetError:
                # Windows reports the closed client's ICMP port-unreachable on the next recvfrom
                # (WSAECONNRESET). Keep serving: the silent-client check then ends the stream and
                # pays the match.
                continue
            try:
                self.handle(sock, packet, peer)
            except Exception as ex:  # never die on one bad datagram
                self.emit("handler_error", error=repr(ex))
        for peer in list(self.stream_peers):self.stop_stream(peer,'host_deadline')
        self.emit("stopped", netchan_peers=len(self.netchan_seen),
                  connected=len(self.connected), stats_peers=len(self.stats_seen),
                  stats_counts=self.stats_seen, netchan_counts=self.netchan_seen,
                  stats_completed=sum(u.profile is not None for u in self.stats_uploads.values()),
                  initial_snapshots_sent=len(self.snapshot_sent))
        sock.close()
        self.jsonl.close()


def selftest():
    """Run the protocol regression suite, with no client or game writes."""
    import unittest
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent),
                                               pattern="test_diag_host319.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


def legacy_handshake_selftest(logdir):
    """Exercise the OOB handshake codec with a synthetic client, no sockets."""
    class FakeSock:
        def __init__(self): self.sent = []
        def sendto(self, data, peer): self.sent.append((data, peer))
    h = DiagHost(0, "mp_seatown", "tdm", 18, 1, logdir)
    s = FakeSock(); peer = ("127.0.0.1", 50000)
    # 1) getchallenge -> challengeResponse
    h.handle(s, OOB + b'getchallenge 0 "abc123"\x00', peer)
    assert s.sent and s.sent[-1][0].startswith(OOB + b"challengeResponse ")
    c = h.issued[peer]
    # 2) connect -> connectResponse, parses challenge/qport
    ui = rb'\challenge\%d\qport\12345\protocol\1\name\Dreamer' % c
    h.handle(s, OOB + b'connect 000000003b9aca01 "' + ui + b'"\x00', peer)
    assert any(b"connectResponse" in d for d, _ in s.sent)
    assert peer in h.connected
    # 3) netchan (sequenced) packet is recognised as the milestone signal
    h.handle(s, struct.pack("<I", 1) + b"\x00\x00 game", peer)
    assert h.netchan_seen["127.0.0.1:50000"] == 1
    # 4) complete single-chunk 32 KiB stats upload -> explicit zero mask
    payload = zlib.compress(b"x" * STATS_BYTES)
    stats_pkt = STATS_PREFIX + struct.pack("<BH", 0, len(payload)) + payload
    h.handle(s, stats_pkt, peer)
    assert any(b"statResponse" in d for d, _ in s.sent), "stats not acked"
    assert h.stats_seen["127.0.0.1:50000"] == 1
    # 5) error line is captured
    h.handle(s, OOB + b"error\nEXE_ERR_SERVER_IS_DIFFERENT_VER\n\x00", peer)
    h.jsonl.close()
    print("SELFTEST OK: challenge=%d, connect+stats+netchan+error paths exercised" % c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=28970,
                    help="loopback UDP port to host on (default 28970)")
    ap.add_argument("--map", default="mp_seatown")
    ap.add_argument("--gametype", default="tdm")
    ap.add_argument("--maxclients", type=int, default=18)
    ap.add_argument("--protocol", type=int, default=1,
                    help="connectResponse protocol value; confirm from client error log")
    ap.add_argument("--seconds", type=int, default=600)
    ap.add_argument("--logdir", default=".")
    ap.add_argument('--stop-file', type=Path, help='Stop and settle this match when the instance requests it')
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument('--sequenced-probe', type=int, choices=range(4), default=0,
                    help='Experimental: send up to 3 empty sequenced responses after complete stats')
    ap.add_argument('--gamestate-probe-capture',
                    help='Experimental: same-PID first-netchan capture for one native-validated game-state candidate')
    ap.add_argument('--snapshot-probe-payload',
                    help='Experimental: one explicit initial snapshot payload after the same peer loads the map')
    ap.add_argument('--snapshot-stream',
                    help='Experimental: bounded continuation frames after the initial snapshot is acknowledged')
    ap.add_argument('--delta-continuation', action='store_true',
                    help='Experimental: send continuation frames as flag-0 delta snapshots against the last acknowledged frame')
    ap.add_argument('--ack-client-commands', action='store_true',
                    help='Experimental: acknowledge received client reliable commands (not executed)')
    ap.add_argument('--live-sim-seconds', type=int, default=0,
                    help='Experimental: authoritative host movement from usercmds for this many seconds (max 900)')
    ap.add_argument('--live-origin', type=float, nargs=4, default=[1370.0,-384.0,248.0,180.0],
                    metavar=('X','Y','Z','YAW'))
    ap.add_argument('--weapon', type=int, default=0, help='Weapon definition number (weapons319.txt), e.g. 78 = ak47_mp')
    ap.add_argument('--viewmodels', type=int, nargs=2, default=(0,0), metavar=('ARMS','HANDS'), help='CS_MODELS indices for first-person arms/hands, e.g. 4 5')
    ap.add_argument('--collision-map', default=None, help='Captured clipMap (config319-<pid>-clipmap.bin) for host collision')
    ap.add_argument('--weapflags', type=lambda s:int(s,0), default=0, help='Player field 77 (+0x400); 0x80 skips the HUD weapon-name draw')
    ap.add_argument('--eflags-test', action='store_true', help='Experiment: timed eFlags 0x400/0x800 phases')
    a = ap.parse_args()
    if a.selftest:
        selftest(); return
    host = DiagHost(a.port, a.map, a.gametype, a.maxclients, a.protocol, a.logdir,
             a.sequenced_probe, a.gamestate_probe_capture, a.snapshot_probe_payload,a.snapshot_stream,
             a.delta_continuation, a.ack_client_commands, a.live_sim_seconds, a.live_origin, a.weapon, a.eflags_test, tuple(a.viewmodels), a.weapflags, a.collision_map)
    host.match_pay = True
    try:
        host.serve(a.seconds, a.stop_file)
    finally:
        for peer in list(host.stream_peers):
            host.stop_stream(peer, 'host_shutdown')
        if host.collision is not None:
            host.collision.close()
        host.jsonl.close()


if __name__ == "__main__":
    main()
