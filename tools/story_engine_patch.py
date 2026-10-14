"""Separate experimental copies for configstring and FF423 compatibility probes.

The archive427 function/artifact names are historical; the verified version is
0x1a7 (423). All executable version checks use that value.
"""
import hashlib
import os
from pathlib import Path
import struct
import subprocess

import pefile


def _append_archive_adapter(image):
    """Append the missing reader to the experimental PE, preserving ASLR."""
    pe = pefile.PE(data=image)
    rva = pe.OPTIONAL_HEADER.SizeOfImage
    root = Path(__file__).resolve().parents[1]
    build = root / 'research/experiments/story-native/archive427-build'
    build.mkdir(exist_ok=True)
    compiler = Path('A:/Coding/MinGW/bin')
    env = dict(os.environ, PATH=str(compiler) + os.pathsep + os.environ['SystemRoot'] + '/System32')
    objects = []
    linked = build / 'adapter.exe'
    for name in ('story_archive427', 'story_collision423', 'story_catalog423', 'story_runtime423'):
        obj = build / (name + '.o')
        source = root / ('tools/native/' + name + '.c')
        subprocess.run([str(compiler / 'gcc.exe'), '-c', '-Os', '-fno-builtin', '-fno-jump-tables',
                        '-fno-asynchronous-unwind-tables', '-fno-ident', str(source), '-o', str(obj)],
                       env=env, check=True, capture_output=True)
        objects.append(str(obj))
    symbols = {'archive_reserve': 0x54f9ba, 'archive_bytes': 0x54fc45,
               'archive_string': 0x54ff6b, 'archive_push': 0x550a52, 'archive_pop': 0x550aae,
               'archive_asset': 0x551b07, 'archive_sound': 0x54fff2,
               'archive_record_asset': 0x54f7e1,
               'archive_water': 0x55124c,
               'native_malloc': 0x765678, 'native_free': 0x765608,
               'native_find_definition': 0x53dec8, 'native_printf': 0x757200,
               'native_read_map_body': 0x57165a, 'native_runtime_dynamic': 0x52f6d0,
               'native_load_addon': 0x53fcac, 'native_free_entities': 0x57161f,
               'native_read_entities': 0x571c8f,
               'archive_dispatch_table': 0x5591eb, 'archive_unknown_asset': 0x5596cb,
               'archive_selected_asset': 0x5591fe, 'archive_inline_asset': 0x55920b}
    command = [str(compiler / 'ld.exe'), '--image-base=0x400000',
               '-Ttext=' + hex(0x400000 + rva), '-e', '_replay_addon427', *objects, '-o', str(linked)]
    command += ['--defsym=_' + name + '=' + hex(address) for name, address in symbols.items()]
    subprocess.run(command, env=env, check=True, capture_output=True)
    names = subprocess.check_output([str(compiler / 'nm.exe'), '--defined-only', str(linked)],
                                    env=env, text=True)
    entries = {parts[2]: int(parts[0], 16) for line in names.splitlines()
               if len(parts := line.split()) == 3}
    adapter = pefile.PE(str(linked))
    code = next(s for s in adapter.sections if s.Name.rstrip(b'\0') == b'.text')
    if adapter.OPTIONAL_HEADER.DATA_DIRECTORY[5].Size:
        raise ValueError('Adapter must contain only position-independent calls')
    payload = code.get_data()[:code.Misc_VirtualSize]
    section_offset = pe.sections[-1].get_file_offset() + 40
    if any(image[section_offset:section_offset + 40]):
        raise ValueError('No spare PE section header')
    align = pe.OPTIONAL_HEADER.FileAlignment
    raw_offset = (len(image) + align - 1) & -align
    raw_size = (len(payload) + align - 1) & -align
    result = bytearray(image)
    result.extend(b'\0' * (raw_offset + raw_size - len(result)))
    result[raw_offset:raw_offset + len(payload)] = payload
    struct.pack_into('<8sIIIIIIHHI', result, section_offset, b'.rea427\0', len(payload), rva,
                     raw_size, raw_offset, 0, 0, 0, 0, 0x60000020)
    struct.pack_into('<H', result, pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),
                     pe.FILE_HEADER.NumberOfSections + 1)
    section_align = pe.OPTIONAL_HEADER.SectionAlignment
    struct.pack_into('<I', result, pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),
                     (rva + len(payload) + section_align - 1) & -section_align)
    struct.pack_into('<I', result, pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfCode'),
                     pe.OPTIONAL_HEADER.SizeOfCode + raw_size)
    for address, before, name in (
        (0x551c90, '5589e5575653', '_replay_material423'),
        (0x55501b, '5589e583ec04', '_replay_addon427'),
        (0x551e71, '5589e58d6424d0', '_replay_weapon423'),
        (0x55592d, '5589e5575653', '_replay_attachment423'),
        (0x5526e1, '5589e5575653', '_replay_tracer423'),
        (0x555038, '5589e58d6424c8', '_replay_collision423'),
        (0x56db01, '5589e58da424e0fdffff', '_read_collision_layout423'),
        (0x56ea50, '5589e583ec14', '_read_collision_entities423'),
        (0x5591e2, '83f82c0f87e0040000', '_route_asset45'),
        (0x5591fe, '83bdfcfcfffffd0f86a5feffff', '_route_shared_asset'),
        (0x545163, 'e8608dffff', '_find_dynamic_definition423'),
        (0x571cad, '5589e583ec04', '_read_addon_entities423'),
        (0x53448f, 'e83cb2ffff', '_probe_story_dynamic423'),
    ):
        hook = pe.get_offset_from_rva(address - 0x400000)
        expected = bytes.fromhex(before)
        if image[hook:hook + len(expected)] != expected:
            raise ValueError(f'{name} entry instruction mismatch')
        result[hook:hook + len(expected)] = (
            (b'\xe8' if expected[0] == 0xe8 else b'\xe9') +
            struct.pack('<i', entries[name] - address - 5) + b'\x90' * (len(expected) - 5))
    return bytes(result)


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
        (0x14ceaa, '3d6d010000', '3da7010000'),  # OpenFastFile: cmp eax,423
        (0x14b29f, '81fa6d010000', '81faa7010000'),  # DecryptFastFileMaterial: cmp edx,423
        (0x14b2ec, 'ba80e88a00', 'baa09f8500'),  # ReadClientRegion uses fseek offset, not VA
        # Client 0x495d60 and reference 0x5557bd share the 20-byte NCS layout.
        (0x154bca, '81bbcc0200006d010000', '81bbcc020000a7010000'),
        (0x15b8f0, '81780c6d010000', '81780ca7010000'),  # ReadNetConst asset version
        (0x15b8fc, '81b8cc0200006d010000', '81b8cc020000a7010000'),
        (0x174407, '81780c6d010000', '81780ca7010000'),  # WorldBaseName header size
        (0x1744c3, '817b0c6d010000', '817b0ca7010000'),  # WorldPlanes source starts after 0x648
        (0x16a025, '6bdf44', '6bdf48'),  # Collision submodel stride 68 -> 72
        (0x16a086, '8d431c', '8d4320'),  # Its leaf follows the new cinfo pointer
        (0x16a2a9, '0fb682cd000000', '0fb682e9000000'),  # clipMap checksum +0xe8
        (0x16a2b3, '0fb68ace000000', '0fb68aea000000'),
        (0x16a2bf, '0fb68acc000000', '0fb68ae8000000'),
        (0x16a2c8, '0fb692cf000000', '0fb692eb000000'),
        (0x16e7d8, '8d8478a8000000', '8d8478c4000000'),  # dynamic counts moved +0xa8 -> +0xc4
        # AddonMapEnts is 52 bytes, with an additional collision tail.
        (0x13f288, '83c62483ea24', '83c63483ea34'),  # inline name and its bound
        (0x13f2d8, '83fa23', '83fa33'),  # minimum header in mounted lookup
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
        # Material replay now uses the explicit FF423 reader, including image
        # holder aliases. Its extent and native consumers below remain separate.
        # Runtime dependency lookup and native material must use that same header.
        # Among admitted dependency types, only material reaches this default size.
        (0x13d1de, 'be60000000', 'be68000000'),
        (0x13d25d, '81780c6d010000', '81780ca7010000'),
        (0x13d26a, 'c1e203', 'c1e204'),  # name +0x10
        (0x1595e8, '817b0c6d010000', '817b0ca7010000'),
        (0x1595f5, '8d04c504000000', 'c1e00483c00490'),  # flags +0x14
        (0x15961f, '8b4210', '8b4218'),  # packed surface metadata +0x18
        # Shared zones contain menu lists. Client 0x48ff80/0x48f890 use
        # the existing 404-byte menu and 392-byte item branches, not legacy 400/380.
        (0x155908, '81bfcc0200006d010000', '81bfcc020000a7010000'),
        (0x15597d, '81bfcc0200006d010000', '81bfcc020000a7010000'),
        (0x1561ba, '81bfcc0200006d010000', '81bfcc020000a7010000'),
        (0x156229, '81b8cc0200006d010000', '81b8cc020000a7010000'),
        (0x15627d, '81b8cc0200006d010000', '81b8cc020000a7010000'),
        # Client 0x48a660 only consumes inline (-1) collision triangles.
        (0x1655a3, '81790c6d010000', '81790ca7010000'),
        (0x15241d, '81bbcc0200006d010000', '81bbcc020000a7010000'),
        # Client 0x48b6e0 consumes 64 bytes per visual-state sample, not 48.
        (0x151d2c, 'b930000000', 'b940000000'),
        (0x14b9ec, 'c7042430000000', 'c7042440000000'),  # ReadEffectSource
        # Keep complete samples in the headless native effect too; never truncate
        # a 64-byte source array with the legacy count*48 memcpy in pack().
        (0x14c34e, '8d0c40c1e104', '89c1c1e10690'),
        # Client 0x490fb0: 19 impact rows, 35 effect references per row.
        (0x1557db, 'ba10000000', 'ba13000000'),
        (0x1557ed, '8db8c0080000', '8db8640a0000'),
        # Client 0x48d9a0 uses the former 36-byte entity body without stage fields.
        (0x154404, 'c7042400000000', 'c7042401000000'),
        # Client 0x4993c0/0x498fd0: 0x648 world header and expanded draw arrays.
        (0x14f11c, '81bbcc0200006d010000', '81bbcc020000a7010000'),
        (0x152861, '81bfcc0200006d010000', '81bfcc020000a7010000'),
        (0x152b49, '81bfcc0200006d010000', '81bfcc020000a7010000'),
        (0x152d9d, '81b8cc0200006d010000', '81b8cc020000a7010000'),
        (0x152e33, '81b8cc0200006d010000', '81b8cc020000a7010000'),
        (0x153071, '81becc0200006d010000', '81becc020000a7010000'),
        (0x1534c5, '81bbcc0200006d010000', '81bbcc020000a7010000'),
        # Client 0x49a320 drops these categories. Reuse the existing EMPTY-only
        # branch; nonempty payloads still fail, and no AI data is fabricated.
        (0x3ed914, 'f0935500', '68945500'),  # 14: aipaths
        (0x3ed920, 'cb965500', '68945500'),  # 17: glass
        (0x3ed924, '04945500', '68945500'),  # 18: vehicle tracks
    )
    result = bytearray(image)
    for offset, before, after in edits:
        expected, replacement = bytes.fromhex(before), bytes.fromhex(after)
        if len(expected) != len(replacement):
            raise ValueError('In-place patch would shift PE sections')
        if image[offset:offset + len(expected)] != expected:
            raise ValueError('Reference engine instruction mismatch')
        result[offset:offset + len(expected)] = replacement
    return _append_archive_adapter(bytes(result))
