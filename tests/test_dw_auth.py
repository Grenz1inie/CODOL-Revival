"""Validate the observed task-10 request against the client ticket wire layout."""
import base64
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dw_auth import SESSION_KEY, auth_reply

class AuthTests(unittest.TestCase):
    def test_captured_request_has_coherent_128_byte_tickets(self):
        request = json.loads((ROOT / 'tests/fixtures/auth-request.json').read_text())
        reply = auth_reply(request)
        ticket = base64.b64decode(reply['client_ticket'], validate=True)
        server = base64.b64decode(reply['server_ticket'], validate=True)
        self.assertEqual((reply['auth_task'], reply['code']), ('11', '700'))
        self.assertEqual(reply['iv_seed'], request['iv_seed'])
        self.assertEqual(len(ticket), 128)
        self.assertEqual(len(server), 128)
        self.assertEqual(struct.unpack_from('<I', ticket, 0)[0], 0xefbdadde)
        self.assertEqual(struct.unpack_from('<I', ticket, 5)[0], int(request['title_id']))
        self.assertEqual(struct.unpack_from('<Q', ticket, 25)[0], int(json.loads(request['extra_data'])['user_id']))
        self.assertEqual(ticket[97:121], SESSION_KEY)
        self.assertEqual(server[:24], SESSION_KEY)

if __name__ == '__main__':
    unittest.main()
