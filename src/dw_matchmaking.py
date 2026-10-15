"""3.3.3.3 server-candidate encoding; publication requires a live ready instance."""
import struct


def server_result(*, port, server_id, security_id, security_key):
    """Encode one loopback MatchMakingInfo (client 0x701db0 / 0xa55700).

    Unused search metadata retains the zero defaults from 0x701a30.
    This codec alone does not publish or reserve a server.
    """
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('invalid local server port')
    if type(server_id) is not int or not 1 <= server_id < 1 << 64:
        raise ValueError('invalid server identity')
    if not isinstance(security_id, bytes) or len(security_id) != 8:
        raise ValueError('security ID must contain 8 bytes')
    if not isinstance(security_key, bytes) or len(security_key) != 16:
        raise ValueError('security key must contain 16 bytes')

    def blob(value):
        return b'\x13\x08' + struct.pack('<I', len(value)) + value

    endpoint = b'\x7f\0\0\x01' + struct.pack('<H', port)
    common_address = endpoint + bytes(24) + endpoint + b'\x01'
    result = blob(common_address) + blob(security_id)
    result += b''.join(b'\x08' + struct.pack('<I', value) for value in (0, 1, 0))
    result += b'\x10\0\x0a' + struct.pack('<Q', server_id) + b'\x10CODOL Local\0'
    result += b'\x07\0\0\0\0' * 3 + b'\x08\0\0\0\0' + b'\x07\0\0\0\0' * 3
    result += blob(security_key) + b'\x07\0\0\0\0' * 11
    return result + b'\x0a' + bytes(8) + b'\x07\0\0\0\0' * 2
