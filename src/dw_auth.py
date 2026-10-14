"""Local QA account-auth response, based on this client's ticket parser.

Client SHA256 e3823fd6...: parser 0x00a598b0 accepts a decoded ticket whose
first DWORD is 0xefbdadde, without taking the encrypted-ticket branch.
This is the existing QA-client path, with no executable patch.
The 128-byte layout is corroborated by s1-mod auth3_server.cpp (see research).
"""
import base64
import json
import struct
import time

SESSION_KEY = bytes.fromhex('1337' * 12)

def auth_reply(request):
    if int(request['auth_task']) != 10:
        raise ValueError('Only observed local account auth_task=10 is implemented')
    extra = json.loads(request['extra_data'])
    user_id = int(extra['user_id'])
    title_id = int(request['title_id'])
    issued = int(time.time())
    ticket = struct.pack('<IBIIIQQ64s24s3s4s', 0xefbdadde, 0, title_id,
                         issued, issued + 86400, 0, user_id, b'LocalPlayer',
                         SESSION_KEY, bytes(3), bytes(4))
    server_ticket = SESSION_KEY + bytes(104)
    return {'auth_task': '11', 'code': '700', 'iv_seed': request['iv_seed'],
            'client_ticket': base64.b64encode(ticket).decode(),
            'server_ticket': base64.b64encode(server_ticket).decode()}
