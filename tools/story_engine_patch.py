"""Separate experimental copies for configstring and FF427 compatibility probes."""
import hashlib


def patch_configstrings(image):
    if hashlib.sha256(image).hexdigest() != '1736926655100b53499ae75ea5bddd0741983c12c89cdb51d49aef8a0be03243':
        raise ValueError('Reference engine hash mismatch')
    if image[0x9fc4d:0x9fc55] != bytes.fromhex('c7 44 24 08 0b 00 00 00') or image[0x9f8b4:0x9f8bb] != bytes.fromhex('81 7d 1c ff 07 00 00'):
        raise ValueError('Reference engine instruction mismatch')
    result = bytearray(image)
    result[0x9f8b8] = 0x03  # Maximum alias count: 0x7ff -> 0x3ff.
    result[0x9fc51] = 0x0a  # Wire width: 11 -> 10 bits.
    return bytes(result)


def patch_archive427(image):
    """Isolated archive probe: retain material-hash and block verification.

    The matching 3333 client carries the same RSA material at a different file offset.
    This replaces the 365 branch, not a general multi-version runtime adapter.
    """
    if hashlib.sha256(image).hexdigest() != '1736926655100b53499ae75ea5bddd0741983c12c89cdb51d49aef8a0be03243':
        raise ValueError('Reference engine hash mismatch')
    edits = (
        (0x14ceaa, '3d6d010000', '3da7010000'),  # OpenFastFile: cmp eax,427
        (0x14b29f, '81fa6d010000', '81faa7010000'),  # DecryptFastFileMaterial: cmp edx,427
        (0x14b2ec, 'ba80e88a00', 'baa09f8500'),  # ReadClientRegion uses fseek offset, not VA
        # Client 0x495d60 and reference 0x5557bd share the 20-byte NCS layout.
        (0x154bca, '81bbcc0200006d010000', '81bbcc020000a7010000'),
        # Client 0x488a80: technique-set size 0xd0, 48 pointers at +0x10.
        (0x150a98, '81b8cc0200006d010000', '81b8cc020000a7010000'),
        # The model extent pass must consume the same layout as replay_material.
        (0x1476b0, '817d146d010000', '817d14a7010000'),
        (0x1476ce, 'c7042460000000', 'c7042468000000'),
        (0x1476f7, '8d04c6', '8d4610'),
        (0x14770a, '8d443050', '8d443058'),
        (0x14771b, '8d443054', '8d44305c'),
        (0x147730, '8d443058', '8d443060'),
        (0x147745, '8d44305c', '8d443064'),
        (0x1477c2, '0fb67c3048', '0fb67c3050'),
        (0x14789f, '0fb64c3049', '0fb64c3051'),
        (0x1478c9, '0fb64c304a', '0fb64c3052'),
        (0x1472dc, '3d6d010000', '3da7010000'),  # technique-set extent
        (0x146f90, '3d6d010000', '3da7010000'),  # image extent: 0x34, name +0x30
        (0x15055c, '81bbcc0200006d010000', '81bbcc020000a7010000'),
        # Client 0x488bd0: 0x68 bytes, name +0x10, arrays/counts shifted by eight.
        (0x1510c5, 'b960000000', 'b968000000'),
        (0x151108, '8d04c6', '8d4610'),
        (0x151115, '8d4650', '8d4658'),
        (0x151134, '8d4654', '8d465c'),
        (0x151141, '8d4658', '8d4660'),
        (0x151152, '8d465c', '8d4664'),
        (0x151183, '0fb65648', '0fb65650'),
        (0x1511a9, '807e4800', '807e5000'),
        (0x1511e0, '0fb64648', '0fb64650'),
        (0x151219, '0fb65649', '0fb65651'),
        (0x151241, '0fb6564a', '0fb65652'),
        # Client 0x48a660 only consumes inline (-1) collision triangles.
        (0x1655a3, '81790c6d010000', '81790ca7010000'),
        (0x15241d, '81bbcc0200006d010000', '81bbcc020000a7010000'),
        # Client 0x48b6e0 consumes 64 bytes per visual-state sample, not 48.
        (0x151d2c, 'b930000000', 'b940000000'),
        # Client 0x4993c0/0x498fd0: 0x648 world header and expanded draw arrays.
        (0x14f11c, '81bbcc0200006d010000', '81bbcc020000a7010000'),
        (0x152861, '81bfcc0200006d010000', '81bfcc020000a7010000'),
        (0x152b49, '81bfcc0200006d010000', '81bfcc020000a7010000'),
        (0x152d9d, '81b8cc0200006d010000', '81b8cc020000a7010000'),
        (0x152e33, '81b8cc0200006d010000', '81b8cc020000a7010000'),
        (0x153071, '81becc0200006d010000', '81becc020000a7010000'),
        (0x1534c5, '81bbcc0200006d010000', '81bbcc020000a7010000'),
    )
    result = bytearray(image)
    for offset, before, after in edits:
        expected, replacement = bytes.fromhex(before), bytes.fromhex(after)
        if image[offset:offset + len(expected)] != expected:
            raise ValueError('Reference engine instruction mismatch')
        result[offset:offset + len(expected)] = replacement
    return bytes(result)
