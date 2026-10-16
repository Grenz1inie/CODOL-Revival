"""Bounded diagnostic frames; immutable payloads and explicit per-peer state."""
import hashlib
import json
import struct
from pathlib import Path


def validate_initial_payload(data):
    if (not 9 <= len(data) <= 1024 or data[0] != 0 or data[5:7] != b'\0\x08'
            or data[7] & 1 or data[-1] != 5
            or not 0 < struct.unpack_from('<I', data, 1)[0] <= 0x7fffffff):
        raise ValueError('Expected a full snapshot with flag 8, no prior base, and EOF')
    return struct.unpack_from('<I', data, 1)[0]


def load_stream(path, initial):
    raw=Path(path).read_bytes()
    if len(raw)>3_000_000:raise ValueError('Oversized snapshot stream')
    obj=json.loads(raw)
    if obj.get('format')!='codol319-bounded-snapshot-v1' or obj.get('simulation') is not False:
        raise ValueError('Unknown diagnostic stream format')
    step=obj.get('interval_ms');frames=obj.get('frames')
    if type(step) is not int or not 50<=step<=1000 or not isinstance(frames,list) or not 2<=len(frames)<=3601 or (len(frames)-1)*step>180000:
        raise ValueError('Stream must be bounded to 180 seconds and at most 20 Hz')
    payloads=[];times=[]
    for frame in frames:
        data=bytes.fromhex(frame['payload_hex']);stamp=validate_initial_payload(data)
        if frame['server_time']!=stamp or (times and stamp!=times[-1]+step):
            raise ValueError('Nonmonotonic or inconsistent snapshot time')
        payloads.append(data);times.append(stamp)
    if payloads[0]!=initial:raise ValueError('Stream starts with a different initial snapshot')
    return tuple(payloads),step/1000,hashlib.sha256(raw).hexdigest()


# Client CG (0054D07B) skips the scene while the next snapshot has flag 2 or 8,
# so continuation frames must not be flag-8 full baselines. The reader
# (004721AA..0047222B) takes deltaNum = serverSequence - deltaByte and only
# accepts a no-delta frame with flag 8; a delta frame needs a valid ring entry.
# Delta bytes 1..MAX_DELTA are validated natively by validate_snapshot_stream319.py.
MAX_DELTA = 15


def delta_frame(payload, sequence, last_ack):
    """Return (payload with delta byte and flags 0, delta). Player-base bit stays 0."""
    validate_initial_payload(payload)
    delta = sequence - last_ack
    if not 1 <= delta <= MAX_DELTA:
        delta = 1  # previous frame; acknowledgements lag on the slow client
    return payload[:5] + bytes((delta, 0)) + payload[7:], delta


def client_header(packet):
    if len(packet)<13:return None
    seq,server_id,ack,command_ack=struct.unpack_from('<IBII',packet)
    # command_ack = last reliable server command the client executed (nonzero once the host sends
    # server commands, e.g. the class menu).
    if not 1<=seq<=0x1fffffff or ack>0x1fffffff or command_ack>0x7fffffff or server_id!=1:
        return None
    return seq,ack
