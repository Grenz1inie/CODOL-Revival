"""Local CODOL protocol-210 lobby scaffold; importing this module starts nothing.

Wire provenance: AlterWare s1-mod f325d4bfaff5d0d9f3bf8b2bd19e8d4271175eef
(GPL-3.0), demonware/{keys.cpp,reply.cpp,reply.hpp,servers/lobby_server.cpp,
servers/stun_server.cpp,services/bdStorage.cpp,data_types.hpp,byte_buffer.cpp}.
https://git.alterware.dev/alterware/s1-mod
CODOL capture and FUN_00a61980 independently confirm the header/transcript/KDF.
See research/reference-protocol/protocol-notes.md for pinned URLs, licenses,
evidence and remaining CODOL differences. Newly written Python from wire facts.
"""
import hashlib
import hmac
from ipaddress import IPv4Address
import os
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from dw_profiles import ProfileError
from dw_marketplace import PurchaseError


# Local bring-up only: must match the 24 bytes in the auth-issued client ticket.
SESSION_KEY = bytes.fromhex('1337' * 12)
SERVER_ACK = bytes.fromhex('16000000ab81d2000000' + '1337' * 8)
MAX_FRAME = 0x80000  # CODOL's captured receive limit; also cap local allocations.


class ProtocolError(ValueError):
    pass


def _derive_keys(transcript, session_key):
    if len(session_key) != 24:
        raise ProtocolError('session key must contain 24 bytes')
    prk = hmac.digest(hashlib.sha1(transcript).digest(), session_key, 'sha1')

    def expand(label, size):
        output, previous = b'', b''
        for counter in range(1, (size + 19) // 20 + 1):
            previous = hmac.digest(prk, previous + label + bytes((counter,)), 'sha1')
            output += previous
        return output[:size]

    return expand(b'CLIENTCHAL', 16), expand(b'BDDATA', 72)


def _decode_task(packet, keys):
    # Full frame: length4, AB85, sequence4, IV16, AES blocks, HMAC8.
    ciphertext = packet[26:-8]
    if len(packet) < 50 or not ciphertext or len(ciphertext) % 16:
        raise ProtocolError('invalid AES session frame size')
    expected = hmac.digest(keys[:20], packet[:-8], 'sha1')[:8]
    if not hmac.compare_digest(packet[-8:], expected):
        raise ProtocolError('client session MAC mismatch')
    decryptor = Cipher(algorithms.AES(keys[40:56]), modes.CBC(packet[10:26])).decryptor()
    clear = decryptor.update(ciphertext) + decryptor.finalize()
    size = struct.unpack_from('<I', clear)[0]
    if size < 3 or size > len(clear) - 5 or len(clear) - 5 - size >= 16:
        raise ProtocolError('invalid inner payload length')
    if clear[4] != 0x86:
        raise ProtocolError(f'unsupported inner type 0x{clear[4]:02x}')
    payload = clear[5:5 + size]
    if payload[1] != 3:
        raise ProtocolError('task ID is not a typed byte (03)')
    return struct.unpack_from('<I', packet, 6)[0], payload


def _task_reply(keys, task_id, transaction, sequence, publisher_file=False, results=(), error_code=0,
                publisher_data=b''):
    payload = b'\x0a' + struct.pack('<Q', transaction) + b'\x08' + struct.pack('<I', error_code)
    payload += bytes((3, task_id))
    if publisher_file:
        results = (b'\x13\x08' + struct.pack('<I', len(publisher_data)) + publisher_data,)
    if results:
        payload += (b'\x08' + struct.pack('<I', len(results))) * 2 + b''.join(results)
    else:
        # S1 omits the second count when there are no result objects.
        payload += b'\x08\0\0\0\0'
    return _encrypted_reply(keys, payload, sequence, 1)


def _encrypted_reply(keys, payload, sequence, message_type):
    clear = struct.pack('<IB', len(payload), message_type) + payload
    clear += bytes(-len(clear) % 16)  # zero padding, not PKCS#7
    iv = os.urandom(16)
    encryptor = Cipher(algorithms.AES(keys[56:72]), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(clear) + encryptor.finalize()
    packet = struct.pack('<I', 30 + len(ciphertext)) + b'\xab\x85'
    packet += struct.pack('<I', sequence) + iv + ciphertext
    return packet + hmac.digest(keys[20:40], packet, 'sha1')[:8]


def handle_lobby(sock, peer, record, save_capture, *, session_key=SESSION_KEY, profiles=None, marketplace=None,
                 private_profiles=None, publisher_files=None):
    """Handle one accepted socket; caller owns localhost binding, timeout and close.

    Callbacks match local_server.py: record(kind, **fields),
    save_capture(kind, bytes) -> capture name. Captures contain complete frames,
    including the special raw 28-byte hello, or remaining bytes at truncated EOF.
    A session_key override must match auth. No ticket-key guessing is performed.
    Unsupported/malformed packets and bad proofs/MACs are logged and end handling.
    Service 10/tasks 7 and 21 return a named publisher file, or an empty fallback.
    With a profile store, service
    8/tasks 1 and 3 read/save public profiles; 2 and 6 read/save private profiles.
    Service 80/tasks 130 and 230 read currency. Other tasks remain zero-result stubs.
    """
    pending = bytearray()
    phase = 'hello'
    hello = b''
    keys = None
    sequence = transaction = 0
    receive_limit = MAX_FRAME
    profile_owner = None

    def capture(direction, packet):
        name = save_capture('lobby-' + direction, packet)
        record('lobby_data', peer=peer, direction=direction, phase=phase,
               length=len(packet), capture=name)

    def receive():
        # Initial C8 is a protocol sentinel, never a 200-byte body length.
        while len(pending) < 4:
            block = sock.recv(65536)
            if not block:
                if pending:
                    capture('request', bytes(pending))
                    raise ProtocolError('EOF in frame header')
                return None
            pending.extend(block)
        size = struct.unpack_from('<I', pending)[0]
        if phase == 'hello' and size == 200:
            total = 28
        else:
            if size > MAX_FRAME:
                raise ProtocolError(f'frame length {size} exceeds {MAX_FRAME}')
            total = size + 4
        while len(pending) < total:
            block = sock.recv(min(65536, total - len(pending)))
            if not block:
                capture('request', bytes(pending))
                raise ProtocolError(f'EOF in frame body ({len(pending)}/{total})')
            pending.extend(block)
        packet = bytes(pending[:total])
        del pending[:total]
        capture('request', packet)
        return packet

    def send(packet):
        if len(packet) - 4 > receive_limit:
            raise ProtocolError('reply exceeds client receive limit')
        sock.sendall(packet)
        capture('response', packet)

    try:
        while (packet := receive()) is not None:
            if packet == bytes(4):
                send(packet)
                continue
            if phase == 'hello':
                if len(packet) != 28 or packet[:8] != b'\xc8\0\0\0' * 2:
                    raise ProtocolError('expected raw 28-byte C8/C8 client hello')
                minimum, maximum, receive_limit = struct.unpack_from('<III', packet, 8)
                if not minimum <= 210 <= maximum:
                    raise ProtocolError(f'unsupported protocol range {minimum}..{maximum}')
                hello = packet
                send(SERVER_ACK)
                record('lobby_header', peer=peer, protocol=210, client_max_frame=receive_limit)
                phase = 'auth'
                continue
            if len(packet) < 6 or packet[4] != 0xab:
                raise ProtocolError('missing AB frame marker')
            if phase == 'auth':
                if packet[5] != 0x82 or len(packet) < 14:
                    raise ProtocolError('expected client auth frame AB82 with 8-byte proof')
                transcript = hello[8:] + SERVER_ACK + packet[:-8]
                challenge, keys = _derive_keys(transcript, session_key)
                if not hmac.compare_digest(packet[-8:], challenge[:8]):
                    raise ProtocolError('client auth proof mismatch')
                send(b'\x0a\0\0\0\xab\x83' + challenge[8:])
                record('lobby_authenticated', peer=peer,
                       transcript_sha1=hashlib.sha1(transcript).hexdigest())
                phase = 'session'
                continue
            if packet[5] != 0x85:
                raise ProtocolError(f'unsupported session type 0x{packet[5]:02x}')
            client_sequence, payload = _decode_task(packet, keys)
            service_id, task_id = payload[0], payload[2]
            parameters = payload[3:]
            publisher_file = service_id == 10 and task_id in (7, 21)
            filename = None
            results = ()
            error_code = 0
            push = None
            operation = 'bdStorage.getPublisherFile' if publisher_file else 'unimplemented'
            if (service_id, task_id) == (11, 13):
                if profile_owner is None or parameters != b'\0':
                    raise ProtocolError('create channel expects current owner and no fields')
                # Single local room on this connection. REA 0xa55a40 reads
                # u64, u32, u32, u64, bool, bool, u32 into bdChannelInfo.
                info = b'\x0a' + struct.pack('<Q', 1)
                info += (b'\x08' + struct.pack('<I', 1)) * 2
                info += b'\x0a' + struct.pack('<Q', profile_owner)
                info += b'\x01\0\x01\0\x08\0\0\0\0'
                results = (info,)
                operation = 'bdMessaging.createChannel'
            elif (service_id, task_id) == (11, 4):
                # REA 0xa4ced0: channel uint64, blob, message-type uint32.
                # 0xa3d5a0 consumes the push; limit is its 1024-byte buffer.
                if profile_owner is None:
                    raise ProtocolError('room broadcast preceded the self-profile read')
                if len(parameters) < 21 or parameters[0] != 10 or parameters[9:11] != b'\x13\x08':
                    raise ProtocolError('invalid room broadcast fields')
                size = struct.unpack_from('<I', parameters, 11)[0]
                if (size > 1024 or len(parameters) != size + 21
                        or parameters[15 + size] != 8 or parameters[-1] != 0):
                    raise ProtocolError('invalid room broadcast size or message type')
                # Local single-player delivery only. Empty sender display name is
                # accepted by readString; room routing uses the numeric sender ID.
                push = b'\x08' + struct.pack('<I', 8)
                push += b'\x0a' + struct.pack('<Q', profile_owner) + b'\x10\0' + parameters[:-1]
                operation = 'bdMessaging.sendToChannel'
            elif profiles is not None and service_id == 8 and task_id == 1:
                if not parameters or parameters[-1] != 0 or (len(parameters) - 1) % 9:
                    raise ProtocolError('getPublicInfos expects typed user IDs and terminator')
                user_ids = []
                for offset in range(0, len(parameters) - 1, 9):
                    if parameters[offset] != 0x0a:
                        raise ProtocolError('getPublicInfos expects a typed uint64')
                    user_ids.append(struct.unpack_from('<Q', parameters, offset + 1)[0])
                # This local single-player prototype observes the first self-profile
                # read before all saves. Do not reassign the owner on later queries.
                if profile_owner is None and len(user_ids) == 1:
                    profile_owner = user_ids[0]
                results = tuple(value for uid in user_ids if (value := profiles.load(uid)) is not None)
                operation = 'bdProfiles.getPublicInfos'
            elif profiles is not None and service_id == 8 and task_id == 3:
                if profile_owner is None:
                    raise ProtocolError('public profile save preceded the self-profile read')
                profiles.save(profile_owner, parameters)
                operation = 'bdProfiles.setPublicInfo'
            elif private_profiles is not None and service_id == 8 and task_id in (2, 6):
                if profile_owner is None:
                    raise ProtocolError('private profile access preceded the self-profile read')
                if task_id == 2:
                    if parameters != b'\0':
                        raise ProtocolError('getPrivateInfo expects only a terminator')
                    value = private_profiles.load(profile_owner)
                    results = () if value is None else (value,)
                    operation = 'bdProfiles.getPrivateInfo'
                else:
                    owner = b'\x0a' + struct.pack('<Q', profile_owner)
                    if not parameters.startswith(owner):
                        raise ProtocolError('private profile save must match the current owner')
                    private_profiles.save(profile_owner, parameters[9:])
                    operation = 'bdProfiles.setPrivateInfoByUserID'
            elif marketplace is not None and (service_id, task_id) in ((80, 154), (93, 131)):
                if profile_owner is None:
                    raise ProtocolError('purchase preceded the self-profile read')
                operation = 'bdMarketplace.purchaseSkus'
                # Observed CODOL single-SKU/quantity-one purchase, default recipient.
                prefix = bytes.fromhex('1000080100000008')
                suffix = bytes.fromhex('08010000000801000000010008010000000a00000000000000001000080000000008000000000300080100000000')
                if service_id == 93:
                    suffix = suffix[:-5] + bytes.fromhex('0000000000')
                try:
                    if len(parameters) != len(prefix) + 4 + len(suffix) or not parameters.startswith(prefix) or parameters[12:] != suffix:
                        raise PurchaseError('暂只支持已验证的单件商品购买请求')
                    sku = struct.unpack_from('<I', parameters, 8)[0]
                    profile = private_profiles.summary(profile_owner) if private_profiles else {}
                    result = marketplace.purchase(profile_owner, sku,
                                                  unlock_rank=profile.get('prestige', 0) * 100 + profile.get('level', 0))
                    record('marketplace_purchase', peer=peer, profile_owner=profile_owner, **result)
                except PurchaseError as error:
                    error_code = error.code
                    record('marketplace_purchase_rejected', peer=peer, profile_owner=profile_owner, error=str(error), code=error.code)
            elif marketplace is not None and service_id == 93 and task_id == 1:
                if profile_owner is None or parameters != bytes.fromhex('080100000000'):
                    raise ProtocolError('unsupported premium balance context or result limit')
                results = (marketplace.currency_result(profile_owner, currency_id=2),)
                operation = 'bdMarketplace.getPremiumBalance'
            elif marketplace is not None and service_id == 80 and task_id in (130, 203, 230):
                if profile_owner is None:
                    raise ProtocolError('marketplace read preceded the self-profile read')
                expected = {230: b'\x10\0\0', 130: b'\x08\x01\0\0\0\0', 203: bytes.fromhex('100006204e00')}[task_id]
                if parameters != expected:
                    raise ProtocolError('unsupported marketplace context or result limit')
                try:
                    if task_id == 203:
                        results = marketplace.inventory_results(profile_owner)
                    else:
                        result = (marketplace.player_assets_result(profile_owner) if task_id == 230
                                  else marketplace.currency_result(profile_owner))
                        results = (result,)
                except (OSError, ValueError, KeyError) as error:
                    raise ProtocolError(f'cannot read marketplace state: {error}') from error
                operation = {230: 'bdMarketplace.getPlayerAssets', 130: 'bdMarketplace.getBalance', 203: 'bdMarketplace.getInventory'}[task_id]
            if publisher_file:
                if task_id == 21:
                    # CODOL's observed variant prefixes a typed context string.
                    if not parameters or parameters[0] != 0x10 or b'\0' not in parameters[1:]:
                        raise ProtocolError('getPublisherFile expects a typed context')
                    parameters = parameters[parameters.index(b'\0', 1) + 1:]
                if not parameters or parameters[0] != 0x10 or b'\0' not in parameters[1:]:
                    raise ProtocolError('getPublisherFile expects a typed NUL-terminated filename')
                filename = parameters[1:].split(b'\0', 1)[0].decode('utf-8', errors='backslashreplace')
            record('lobby_task', peer=peer, service_id=service_id, task_id=task_id,
                   client_sequence=client_sequence, filename=filename,
                   operation=operation, profile_owner=profile_owner,
                   result_count=1 if publisher_file else len(results),
                   error_code=error_code,
                   parameters_hex=payload[3:131].hex(), parameter_length=len(payload) - 3)
            sequence += 1
            transaction += 1
            publisher_data = (publisher_files or {}).get(filename, b'') if publisher_file else b''
            send(_task_reply(keys, task_id, transaction, sequence, publisher_file, results, error_code,
                             publisher_data))
            if push is not None:
                sequence += 1
                send(_encrypted_reply(keys, push, sequence, 2))
                record('lobby_room_message', peer=peer, profile_owner=profile_owner,
                       channel_id=struct.unpack_from('<Q', parameters, 1)[0],
                       message_size=size, push_event=8)
    except (OSError, ProtocolError, ProfileError) as exc:
        record('lobby_error', peer=peer, phase=phase, error=str(exc))


def stun_reply(packet, peer, server=('127.0.0.1', 3074)):
    """Return the S1-style Demonware UDP reply, or None; performs no network I/O.

    This is not RFC5389 STUN. Endpoints are (IPv4 string, port), with network-order
    address bytes and little-endian ports. Caller supplies the advertised peer
    and server endpoints. CODOL's UDP behavior still needs a real capture.
    """
    if len(packet) < 3 or packet[0] not in (20, 30):
        return None

    def endpoint(value):
        return IPv4Address(value[0]).packed + struct.pack('<H', value[1])

    reply = bytes((packet[0] + 1, 2, 0)) + endpoint(peer)
    return reply + endpoint(server) if packet[0] == 20 else reply
