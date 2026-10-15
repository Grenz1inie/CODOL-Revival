"""Tiger192, ported from LibTomCrypt (Tom St Denis); see NOTICE.md."""
import struct
from .tiger_tables import TABLES

MASK = (1 << 64) - 1
T1, T2, T3, T4 = (TABLES[i:i+256] for i in range(0, 1024, 256))


def _round(a, b, c, x, multiplier):
    c ^= x
    a = (a - (T1[c & 255] ^ T2[(c >> 16) & 255] ^ T3[(c >> 32) & 255] ^ T4[(c >> 48) & 255])) & MASK
    b = (b + (T4[(c >> 8) & 255] ^ T3[(c >> 24) & 255] ^ T2[(c >> 40) & 255] ^ T1[c >> 56])) * multiplier & MASK
    return a, b, c


def _pass(a, b, c, x, multiplier):
    a, b, c = _round(a, b, c, x[0], multiplier)
    b, c, a = _round(b, c, a, x[1], multiplier)
    c, a, b = _round(c, a, b, x[2], multiplier)
    a, b, c = _round(a, b, c, x[3], multiplier)
    b, c, a = _round(b, c, a, x[4], multiplier)
    c, a, b = _round(c, a, b, x[5], multiplier)
    a, b, c = _round(a, b, c, x[6], multiplier)
    b, c, a = _round(b, c, a, x[7], multiplier)
    return a, b, c


def _schedule(x):
    x[0] = (x[0] - (x[7] ^ 0xa5a5a5a5a5a5a5a5)) & MASK
    x[1] ^= x[0]
    x[2] = (x[2] + x[1]) & MASK
    x[3] = (x[3] - (x[2] ^ ((~x[1] & MASK) << 19))) & MASK
    x[4] ^= x[3]
    x[5] = (x[5] + x[4]) & MASK
    x[6] = (x[6] - (x[5] ^ ((~x[4] & MASK) >> 23))) & MASK
    x[7] ^= x[6]
    x[0] = (x[0] + x[7]) & MASK
    x[1] = (x[1] - (x[0] ^ ((~x[7] & MASK) << 19))) & MASK
    x[2] ^= x[1]
    x[3] = (x[3] + x[2]) & MASK
    x[4] = (x[4] - (x[3] ^ ((~x[2] & MASK) >> 23))) & MASK
    x[5] ^= x[4]
    x[6] = (x[6] + x[5]) & MASK
    x[7] = (x[7] - (x[6] ^ 0x0123456789abcdef)) & MASK


def tiger(data):
    a, b, c = 0x0123456789abcdef, 0xfedcba9876543210, 0xf096a5b4c3b2e187
    padded = data + b'\x01' + bytes((55-len(data)) % 64) + struct.pack('<Q', len(data)*8)
    for offset in range(0, len(padded), 64):
        aa, bb, cc = a, b, c
        x = list(struct.unpack_from('<8Q', padded, offset))
        a, b, c = _pass(a, b, c, x, 5)
        _schedule(x)
        c, a, b = _pass(c, a, b, x, 7)
        _schedule(x)
        b, c, a = _pass(b, c, a, x, 9)
        a, b, c = a ^ aa, (b-bb) & MASK, (c+cc) & MASK
    return struct.pack('<3Q', a, b, c)
