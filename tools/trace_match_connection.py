"""Run the local service with a bounded, private transport trace for one repro.

Contains ephemeral session keys: runtime/captures only; never commit this output.
The real handshake and authentication routines execute without substitution.
"""
import json
from pathlib import Path
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from match_server.transport import Association


def main():
    target = ROOT / ('runtime/captures/match-connection-trace-'+time.strftime('%Y%m%d-%H%M%S')+'.json')
    events = []

    def trace(method, original):
        def call(self, packet):
            if len(events) >= 32:
                return original(self, packet)
            event = dict(time=time.time(), method=method, packet=packet.hex())
            if method == 'handshake' and self.private is not None:
                event['private'] = format(self.private.private_numbers().private_value, '056x')
            try:
                value = original(self, packet)
                event['result'] = value.hex()
                return value
            except ValueError as error:
                event['error'] = str(error)
                raise
            finally:
                event['security_id'] = self.sid.hex()
                event['security_key'] = self.security.hex()
                event['key'] = self.key.hex() if self.key is not None else None
                events.append(event)
                target.write_text(json.dumps(events, indent=2), encoding='utf-8')
        return call

    for method in ('handshake', 'decrypt'):
        setattr(Association, method, trace(method, getattr(Association, method)))
    runpy.run_path(str(ROOT / 'src/local_server.py'), run_name='__main__')


if __name__ == '__main__':
    main()
