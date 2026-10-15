# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline FF423 Killhouse export. Never executes a client or an engine.

The matching 3.3.3.3 client is an explicit, read-only decryption input. Exported
packages contain no executable dependency. Collision section traversal follows
tools/native/story_collision423.c; NCS replay follows CODOL_BeginZoneReplay and
replay_netconststrings in the retained reference source (AGPL-3.0-or-later).
"""
import math
import re
import struct
import argparse
import hashlib
import json
from pathlib import Path
import zlib
import sys
from itertools import product

from index_story_zone import read_assets, read_ncs, read_rawfile, read_baselines
from story_netconst423 import build_registry

INLINE = 0xffffffff
ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / 'research/experiments/independent-match'
MAP = 'mp_killhouse_sh'
ZONE_NAMES = ('code_pre_gfx_mp', 'localized_code_pre_gfx_mp', 'code_post_gfx_default_mp',
              'code_post_gfx_mp', 'localized_code_post_gfx_mp', 'common_mp',
              'localized_common_mp', 'common_gametype_mp', 'localized_common_gametype_mp',
              MAP, MAP + '_const')
sys.path.insert(0, str(ROOT / 'src'))


def read_collision(data):
    """Bounded FF423 type-15 traversal; retain references, never native pointers.

    Section bytes remain serialized, NOT a ready-to-use physics world. Inline
    children and the trailing dynamic/stage data remain in the original blob.
    """
    if not 256 <= len(data) <= 512 * 1024 * 1024:
        raise ValueError('invalid FF423 collision size')
    h = struct.unpack_from('<64I', data)
    position = 256
    sections = {}

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def take(count, stride):
        nonlocal position
        require(count <= (len(data) - position) // stride, 'truncated collision array')
        offset = position
        position += count * stride
        return offset

    def word(offset):
        require(0 <= offset <= len(data) - 4, 'collision reference outside asset')
        return struct.unpack_from('<I', data, offset)[0]

    def string(pointer):
        nonlocal position
        if pointer == INLINE:
            position = data.index(b'\0', position) + 1

    def section(name, count, stride, pointer, inline=False):
        require(pointer or not count, f'missing {name} pointer')
        if inline:
            require(not count or pointer == INLINE, f'unsupported shared {name}')
        offset = take(count, stride) if pointer == INLINE else None
        sections[name] = dict(offset=offset, count=count, stride=stride, reference=pointer,
                              status='inline' if offset is not None else 'shared' if count else 'empty')
        return offset

    def planes(offset, count):
        for i in range(count):
            if word(offset + i * 8) == INLINE:
                take(1, 20)

    string(h[0])
    section('planes', h[2], 20, h[3])
    offset = section('materials', h[4], 12, h[5], True)
    for i in range(h[4]):
        string(word(offset + i * 12))
    offset = section('brush_sides', h[6], 8, h[7], True)
    planes(offset, h[6])
    section('brush_edges', h[8], 1, h[9], True)
    offset = section('leaf_brush_nodes', h[10], 20, h[11], True)
    inline_indices = shared_nodes = 0
    for i in range(h[10]):
        count = struct.unpack_from('<H', data, offset + i * 20 + 2)[0]
        if 0 < count < 0x8000:
            if word(offset + i * 20 + 8) == INLINE:
                take(count, 2)
                inline_indices += count
            else:
                shared_nodes += 1
    section('leaf_brushes', h[12], 2, h[13])
    if h[12] and h[13] != INLINE:
        require(not shared_nodes and h[12] <= inline_indices, 'unsupported mixed leaf brush references')
        sections['leaf_brushes']['note'] = 'aliases inline leaf lists; do not duplicate'
    count = h[14] & 0xffff
    offset = section('brushes', count, 36, h[15], True)
    for i in range(count):
        if word(offset + i * 36 + 4) == INLINE:
            planes(take(1, 8), 1)
        if word(offset + i * 36 + 8) == INLINE:
            take(1, 1)
    section('brush_bounds', count, 24, h[16], True)
    section('brush_contents', count, 4, h[17], True)
    require(h[18] >= INLINE - 1, 'unsupported collision info reference')
    offset = take(1, 64)
    for i in range(16):
        value = word(offset + i * 4)
        if i < 12 and not i % 2:
            require(value == h[i + 2], 'collision info count mismatch')
        elif i == 12:
            require(value & 0xffff == count, 'collision info brush count mismatch')
        else:
            require(value < INLINE - 1, 'unsupported nested collision info')
    offset = section('static_models', h[19], 76, h[20], True)
    for i in range(h[19]):
        require(word(offset + i * 76) < INLINE - 1, 'inline static model unsupported')
    offset = section('nodes', h[21], 8, h[22], True)
    planes(offset, h[21])
    section('leaves', h[23], 40, h[24], True)
    section('leaf_surfaces', 0, 4, 0)
    section('vertices', h[25], 12, h[26], True)
    section('triangles', h[27], 6, h[28], True)
    section('walkable', (h[27] * 3 + 31) // 32, 4, h[29], True)
    section('borders', h[30], 28, h[31], True)
    offset = section('partitions', h[32], 12, h[33], True)
    for i in range(h[32]):
        if word(offset + i * 12 + 8) == INLINE:
            take(1, 28)
    section('aabbs', h[34], 32, h[35], True)
    offset = section('submodels', h[36], 72, h[37], True)
    references = [word(offset + i * 72 + 28) for i in range(h[36])]
    require(all(0 < ref < INLINE - 1 for ref in references) and len(set(references)) <= 1,
            'unsupported submodel collision info')
    section('static_nodes', h[47] & 0xffff, 28, h[48], True)
    map_offset = position
    require(h[38] >= INLINE - 1, 'unsupported MapEnts reference')
    take(1, 36)
    require(word(map_offset) == h[0] and word(map_offset + 4) == INLINE, 'MapEnts header mismatch')
    string(h[0])
    text_size = word(map_offset + 8)
    text_offset = take(text_size, 1)
    text = data[text_offset:position]
    require(text.endswith(b'\0') and b'\0' not in text[:-1], 'invalid entity text termination')
    triggers = {}
    for i, (name, stride) in enumerate((('models', 8), ('hulls', 32), ('slabs', 20))):
        count, reference = struct.unpack_from('<II', data, map_offset + 12 + i * 8)
        require(not count or reference == INLINE, 'unsupported shared trigger array')
        triggers[name] = dict(offset=take(count, stride), count=count, stride=stride)
    return dict(format_version=423, checksum=h[58], sections=sections,
                map_entities_offset=map_offset, entity_text_offset=text_offset,
                entity_text_size=text_size, entity_text=text, triggers=triggers,
                stage_reference=h[39], stage_count=h[40] & 255,
                unparsed_tail_offset=position, unparsed_tail_bytes=len(data) - position,
                physics_ready=False, static_model_geometry_exported=False)


def read_geometry(data, world):
    """Port the pure server3333 CODOL_ReadWorldPlanes/Collision* readers.

    Preserve exact convex halfspaces and partition-relative triangles. Bounds
    supply the six authored axial brush planes, never replace oblique sides.
    World membership comes from BSP leaves, not the unplaced submodel pool.
    """
    layout = read_collision(data)
    sections = layout['sections']

    def require(ok, reason):
        if not ok:
            raise ValueError(reason)

    def unpack(fmt, blob, offset):
        require(0 <= offset <= len(blob) - struct.calcsize(fmt), 'truncated geometry')
        values = struct.unpack_from(fmt, blob, offset)
        require(all(not isinstance(v, float) or math.isfinite(v) for v in values), 'nonfinite geometry')
        return values

    def word(blob, offset):
        return unpack('<I', blob, offset)[0]

    def rows(name, fmt):
        s = sections[name]
        require(s['offset'] is not None or not s['count'], f'unresolved {name}')
        return [unpack(fmt, data, s['offset'] + i * s['stride']) for i in range(s['count'])]

    def bounds(values):
        require(all(v >= 0 for v in values[3:]), 'negative geometry halfsize')
        return ([values[i] - values[i + 3] for i in range(3)],
                [values[i] + values[i + 3] for i in range(3)])

    # CODOL_ReadWorldPlanes + CODOL_AdvanceImageStreamVersion, FF423.
    require(len(world) >= 1608, 'truncated GfxWorld header')
    require(word(world, 0) == word(data, 0) != 0, 'clipMap/GfxWorld name reference mismatch')
    p = 1608
    if word(world, 0) == INLINE:
        end = world.index(b'\0', p)
        require(world[p:end] == data[256:data.index(b'\0', 256)], 'clipMap/GfxWorld name mismatch')
        p = end + 1
    if word(world, 4) == INLINE:
        p = world.index(b'\0', p) + 1
    count, pointer = unpack('<2I', world, 20)
    require(pointer or not count, 'missing skies')
    skies = p
    p += count * 16
    require(p <= len(world), 'truncated skies')
    for i in range(count):
        n, surfaces, image, _ = unpack('<4I', world, skies + 16 * i)
        if surfaces:
            p += n * 4
        require(p <= len(world), 'truncated sky surfaces')
        if image >= INLINE - 1:
            h = p
            p += 52
            require(p <= len(world), 'truncated sky image')
            if word(world, h + 48) == INLINE:
                p = world.index(b'\0', p) + 1
            if word(world, h) == INLINE:
                size = word(world, p + 12)
                p += 16 + size
    require(word(world, 56) == INLINE, 'GfxWorld planes not inline')
    count = sections['planes']['count']
    require(count == word(world, 8), 'GfxWorld plane count mismatch')
    plane_offset = p
    planes = [unpack('<4f', world, p + i * 20) for i in range(count)]
    require(all(abs(sum(n*n for n in plane[:3]) - 1) <= .001 for plane in planes), 'invalid plane normal')
    base = sections['planes']['reference']
    require(0 < base < INLINE - 1, 'unsupported plane reference base')

    def plane_index(ref):
        require(ref >= base and (ref - base) % 20 == 0 and (ref - base) // 20 < count,
                'invalid shared plane reference')
        return (ref - base) // 20

    materials = []
    cursor = sections['materials']['offset'] + sections['materials']['count'] * 12
    for ref, flags, contents in rows('materials', '<3I'):
        name = None
        if ref == INLINE:
            end = data.index(b'\0', cursor)
            name = data[cursor:end].decode('ascii')
            cursor = end + 1
        else:
            require(0 < ref < INLINE - 1, 'invalid material name reference')
        materials.append(dict(name=name, name_reference=ref, surface_flags=flags, contents=contents))
    sides = []
    for ref, mat, adjacent, edges in rows('brush_sides', '<IHBB'):
        require(mat < len(materials), 'brush side material out of range')
        sides.append(dict(plane=plane_index(ref), material=mat, adjacent=adjacent, edges=edges))
    nodes = []
    for i, (ref, left, right) in enumerate(rows('nodes', '<Ihh')):
        require(all(i < c < sections['nodes']['count'] if c >= 0 else
                    -1-c < sections['leaves']['count'] for c in (left, right)), 'invalid BSP child')
        nodes.append(dict(plane=plane_index(ref), children=[left, right]))
    raw_bounds = rows('brush_bounds', '<6f')
    contents = rows('brush_contents', '<I')
    brushes, side, edge, sidebase, edgebase = [], 0, 0, None, None
    for i, raw in enumerate(rows('brushes', '<HHII6H12B')):
        n, glass, side_ref, edge_ref = raw[:4]
        mats, adjacent, edge_counts = raw[4:10], raw[10:16], raw[16:22]
        require(side+n <= len(sides) and all(m < len(materials) for m in mats), 'invalid brush sides/material')
        if n:
            if sidebase is None:
                sidebase = side_ref - side*8
            require(0 < side_ref < INLINE - 1 and side_ref == sidebase+side*8, 'invalid brush side reference')
        e = sum(edge_counts) + sum(s['edges'] for s in sides[side:side+n])
        if e:
            if edgebase is None:
                edgebase = edge_ref-edge
            require(0 < edge_ref < INLINE - 1 and edge_ref == edgebase+edge, 'invalid brush edge reference')
        require(edge+e <= sections['brush_edges']['count'], 'brush edge overflow')
        require(all(a+b <= e for a,b in zip(adjacent,edge_counts)) and
                all(s['adjacent']+s['edges'] <= e for s in sides[side:side+n]), 'invalid edge adjacency')
        lo, hi = bounds(raw_bounds[i])
        brushes.append(dict(mins=lo, maxs=hi, first_side=side, side_count=n, axial_materials=mats,
                            first_edge=edge, edge_count=e, contents=contents[i][0], glass_piece=glass))
        side += n
        edge += e
    require(side == len(sides) and edge == sections['brush_edges']['count'], 'unconsumed brush geometry')

    # Leaf brush lists are inline in this FF423 map; the global pointer aliases
    # those lists. Resolve tree membership before considering world traces.
    tree = []
    cursor = sections['leaf_brush_nodes']['offset'] + sections['leaf_brush_nodes']['count']*20
    for i, raw in enumerate(rows('leaf_brush_nodes', '<BBhI3I')):
        axis, _, n, flags, ref, _, children = raw
        if n > 0:
            require(ref == INLINE, 'unresolved pooled leaf brush list')
            ids = unpack('<' + str(n) + 'H', data, cursor)
            cursor += n*2
            require(all(b < len(brushes) for b in ids), 'leaf brush index out of range')
            tree.append(dict(brushes=ids, children=[]))
        elif i == 0 and not any(raw):
            tree.append(dict(brushes=[], children=[]))
        else:
            child = [i+(children & 65535), i+(children >> 16)]
            if n == -1:
                child.append(i+1)
            require(n in (-1, 0) and axis <= 2 and
                    all(i < c < sections['leaf_brush_nodes']['count'] for c in child), 'invalid leaf brush tree')
            tree.append(dict(brushes=[], children=child))
    require(cursor == sections['brushes']['offset'], 'leaf brush stream not consumed')

    vertices = rows('vertices', '<3f')
    raw_triangles = rows('triangles', '<3H')
    triangles = [None]*len(raw_triangles)
    partitions, border, borderbase = [], 0, None
    borders = rows('borders', '<7f')
    for n, nb, block, _, first, ref in rows('partitions', '<4BII'):
        require(first+n <= len(triangles) and border+nb <= len(borders), 'partition outside geometry')
        if nb:
            if borderbase is None:
                borderbase = ref-border*28
            require(0 < ref < INLINE - 1 and ref == borderbase+border*28, 'invalid border reference')
        for t in range(first, first+n):
            ids = [block*1024+v for v in raw_triangles[t]]
            require(all(v < len(vertices) for v in ids), 'partition vertex index out of range')
            require(triangles[t] is None or triangles[t] == ids, 'inconsistent triangle ownership')
            triangles[t] = ids
        partitions.append(dict(first_tri=first, tri_count=n, vert_block=block, first_border=border, border_count=nb))
        border += nb
    require(border == len(borders) and all(t is not None for t in triangles), 'unconsumed terrain geometry')
    aabbs = []
    for i, row in enumerate(rows('aabbs', '<3fHH3fI')):
        mat, n, index = row[3], row[4], row[8]
        require(mat < len(materials), 'terrain material out of range')
        require(i < index and index+n <= sections['aabbs']['count'] if n else index < len(partitions),
                'invalid terrain AABB child')
        lo, hi = bounds(row[:3]+row[5:8])
        aabbs.append(dict(mins=lo, maxs=hi, material=mat, children=list(range(index,index+n)),
                          partition=None if n else index))

    def leaf(offset):
        first, n, bc, tc = unpack('<HHII', data, offset)
        root = word(data, offset+36)
        require(first+n <= len(aabbs) and root < len(tree), 'invalid leaf geometry root')
        lo, hi = bounds(unpack('<6f', data, offset+12))
        return dict(aabbs=list(range(first,first+n)), brush_root=root, brush_contents=bc,
                    terrain_contents=tc, mins=lo, maxs=hi)

    leaves = [leaf(sections['leaves']['offset']+i*40) for i in range(sections['leaves']['count'])]
    submodels = [leaf(sections['submodels']['offset']+i*72+32) for i in range(sections['submodels']['count'])]

    def membership(owners):
        found, visited = set(), set()
        pending = [l['brush_root'] for l in owners]
        while pending:
            i = pending.pop()
            if i in visited:
                continue
            visited.add(i)
            found.update(tree[i]['brushes'])
            pending.extend(tree[i]['children'])
        terrain, visited = set(), set()
        pending = [i for l in owners for i in l['aabbs']]
        while pending:
            i = pending.pop()
            if i in visited:
                continue
            visited.add(i)
            a = aabbs[i]
            if a['partition'] is not None:
                terrain.add((a['partition'],a['material']))
            pending.extend(a['children'])
        return sorted(found), sorted(terrain)

    # Traverse only BSP-root-reachable leaves. Submodel leaves are separate.
    pending, reachable, seen = [0], set(), set()
    while pending:
        i = pending.pop()
        if i < 0:
            reachable.add(-1-i)
        elif i not in seen:
            seen.add(i)
            pending.extend(nodes[i]['children'])
    world_brushes, world_partitions = membership([leaves[i] for i in sorted(reachable)])
    for model in submodels:
        model['brushes'], model['partitions'] = membership([model])
    static_models = []
    for row in rows('static_models', '<I18f'):
        ref = row[0]
        require(0 < ref < INLINE - 1, 'invalid static model reference')
        lo, hi = bounds(row[13:19])
        static_models.append(dict(model_reference=ref, origin=row[1:4], inverse_scaled_axis=row[4:13],
                                  mins=lo, maxs=hi, geometry=None))
    return dict(schema_version=1, format_version=423, physics_ready=False,
        provenance=dict(source='server3333/src/codol/collision/codol_{world_planes,collision_brushes,collision_terrain,collision_leaves,collision_brush_tree,collision_static_models}.c',
                        collision_sha256=hashlib.sha256(data).hexdigest(), gfxworld_sha256=hashlib.sha256(world).hexdigest(),
                        plane_offset=plane_offset, plane_reference=base),
        planes=planes, sides=sides, brushes=brushes, materials=materials,
        brush_edges=[b[0] for b in rows('brush_edges','<B')],
        vertices=vertices, triangles=triangles, partitions=partitions, borders=borders,
        walkable_words=[v[0] for v in rows('walkable','<I')], aabbs=aabbs,
        world_brushes=world_brushes, world_partitions=world_partitions, submodels=submodels,
        static_models=static_models,
        closure=dict(brush_terrain_decoded=True, unresolved_static_models=len(static_models),
                     unplaced_submodels=max(0,len(submodels)-1), unparsed_tail_bytes=layout['unparsed_tail_bytes'],
                     blockers=['Static xmodel references lack collision geometry.',
                               'Submodel transforms and dynamic/glass state are not installed.',
                               'Analytical point/box traces are not capsule movement or client-verified physics.']))


def read_zone_ncs(zone):
    return _replay_ncs_prefix(zone)[0]


def read_ncs_prefix_block3(zone):
    """Only the proven contiguous NCS prefix, for names in later asset headers.

    Does not replay weapons/models or certify the mounted NCS registration set.
    References outside this byte span must be resolved by their asset loader.
    """
    return _replay_ncs_prefix(zone)[1]


def read_block3_string(block, reference):
    offset = (reference-1)&0xfffffff
    if (reference-1)>>28 != 3 or offset >= len(block):
        raise ValueError(f'string reference outside replayed block 3: {reference:#x}')
    return block[offset:block.index(b'\0',offset)].decode('ascii')


def _replay_ncs_prefix(zone):
    """Replay only a contiguous NCS prefix; report other nonempty tables."""
    assets = read_assets(zone)
    block = bytearray()
    capacity = (struct.unpack_from('<I', zone, 20)[0] + 4095) & ~4095

    def add(data, alignment=1):
        padding = (-len(block)) % alignment
        if len(block) + padding + len(data) > capacity:
            raise ValueError('NCS replay exceeds block-3 capacity')
        block.extend(bytes(padding))
        block.extend(data)

    strings, pointer, count, directory_pointer = struct.unpack_from('<4I', zone, 40)
    if (strings and not pointer) or (count and not directory_pointer):
        raise ValueError('missing zone directory pointer')
    position = 56
    refs = struct.unpack_from('<' + 'I' * strings, zone, position)
    add(zone[position:position + strings * 4], 4)
    position += strings * 4
    for ref in refs:
        if ref == INLINE:
            end = zone.index(b'\0', position) + 1
            add(zone[position:end])
            position = end
    directory = position
    add(zone[directory:directory + count * 16], 4)
    result = dict(tables=[], unresolved=[], empty_assets=[])
    prefix = True
    for index, (kind, data) in enumerate(assets):
        if kind != 44:
            prefix = False
            continue
        if len(data) < 20:
            raise ValueError('truncated NCS header')
        name, kind, source, count, strings_pointer = struct.unpack_from('<5I', data)
        if not prefix:
            if count == 0 and strings_pointer == 0:
                # build_registry ignores empty tables before looking up their kind.
                result['empty_assets'].append(dict(asset_index=index, type=kind,
                    source=source, name_reference=name, count=0))
            else:
                result['unresolved'].append(dict(asset_index=index, reason='non-prefix NCS needs full zone replay'))
            continue
        proven = len(block)
        try:
            reference = struct.unpack_from('<I', zone, directory + index * 16 + 8)[0]
            if reference not in (INLINE, INLINE - 1):
                raise ValueError('NCS asset alias needs full zone replay')
            if reference == INLINE - 1:
                add(bytes(4), 4)
            cursor = 20
            if name == INLINE:
                end = data.index(b'\0', cursor) + 1
                add(data[cursor:end])
                cursor = end
            if strings_pointer == INLINE:
                if count > (len(data) - cursor) // 4:
                    raise ValueError('truncated NCS pointer array')
                refs = struct.unpack_from('<' + 'I' * count, data, cursor)
                add(data[cursor:cursor + count * 4], 4)
                cursor += count * 4
                for ref in refs:
                    if ref == INLINE:
                        end = data.index(b'\0', cursor) + 1
                        add(data[cursor:end])
                        cursor = end
            if cursor != len(data):
                raise ValueError('unaccounted NCS bytes')
            result['tables'].append(read_ncs(data, block))
        except ValueError as error:
            del block[proven:]
            result['unresolved'].append(dict(asset_index=index, reason=str(error)))
            prefix = False  # Later offsets are no longer proven.
    return result,bytes(block)


def read_entities(data):
    """Read serialized entity fields, without executing map scripts."""
    if not data.endswith(b'\0') or b'\0' in data[:-1]:
        raise ValueError('entity text must have exactly one terminal NUL')
    text = data[:-1].decode('ascii')
    tokens = []
    position = 0
    pattern = re.compile(r'\s*(\{|\}|"(?:[^"\\]|\\.)*")')
    while position < len(text):
        match = pattern.match(text, position)
        if not match:
            if text[position:].strip():
                raise ValueError('invalid entity token')
            break
        tokens.append(match[1])
        position = match.end()
    entities = []
    cursor = 0
    while cursor < len(tokens):
        if tokens[cursor] != '{':
            raise ValueError('expected entity opening brace')
        cursor += 1
        fields = {}
        while cursor < len(tokens) and tokens[cursor] != '}':
            if cursor + 1 >= len(tokens) or any(not t.startswith('"') for t in tokens[cursor:cursor + 2]):
                raise ValueError('expected entity key/value')
            key, value = (t[1:-1] for t in tokens[cursor:cursor + 2])
            fields[key] = value
            cursor += 2
        if cursor == len(tokens):
            raise ValueError('unterminated entity')
        cursor += 1
        entities.append(fields)
    return entities


def read_spawns(data):
    """Read authored spawn locations, without inventing defaults or running GSC."""
    points = []
    for entity_index,fields in enumerate(read_entities(data)):
        classname = fields.get('classname', '')
        if classname == 'info_player_start' or (classname.startswith('mp_') and '_spawn' in classname):
            point = dict(entity_index=entity_index, classname=classname)
            for key in ('origin', 'angles'):
                values = [float(v) for v in fields.get(key, '').split()]
                if len(values) != 3 or not all(math.isfinite(v) for v in values):
                    raise ValueError(f'invalid spawn {key} at entity {entity_index}')
                point[key] = values
            points.append(point)
    return points


def classify_submodels(data, geometry):
    """Separate placed obstacles from game objects; don't guess script state."""
    placements = []
    for index,fields in enumerate(read_entities(data)):
        name = fields.get('model','')
        if not name.startswith('*'):
            continue
        model = int(name[1:])
        if not 0 < model < len(geometry['submodels']):
            raise ValueError(f'entity {index}: invalid inline model {name}')
        target = fields.get('targetname','')
        if fields.get('script_gameobjectname'):
            category,reason = 'gametype_object','script_gameobjectname='+fields['script_gameobjectname']
        elif target == 'to_delete_in_coop_4player' or 'gate' in target:
            category,reason = 'placed_world_obstacle','authored targetname='+target+'; script activation/motion not assumed'
        elif target.startswith('smoke_grenade_sight_clip'):
            category,reason = 'dynamic_utility','authored smoke grenade sight clip'
        elif fields.get('script_specialops') == '1' or fields.get('script_noteworthy','').startswith(('launcher_','grenade_target_dummy')):
            category,reason = 'scripted_training_object','explicit script_specialops/script_noteworthy training marker'
        else:
            category,reason = 'script_state_unresolved','script_brushmodel alone does not prove static world membership'
        placements.append(dict(entity_index=index,submodel=model,category=category,reason=reason,
                               fields=fields,installed=False))
    referenced = {p['submodel'] for p in placements}
    return dict(scope='Authored inline model placements, not running script state; excluded from static XModel closure.',
                counts={k:sum(p['category']==k for p in placements) for k in sorted({p['category'] for p in placements})},
                unreferenced=sorted(set(range(1,len(geometry['submodels'])))-referenced),placements=placements)


def select_dm_submodels(report, baseline, geometry):
    """Join current423 type6 baseline +0x98 against MapEnts '*N' and pose.

    This is a declared frozen-mode selection, not proof of script execution or
    live visibility. Original model contents remain authoritative for masks.
    """
    from match_server.collision import placement_axis,transform_vector
    by_model = {}
    for row in read_baselines(baseline):
        state = row['state']
        model = struct.unpack_from('<I',state,0x98)[0]
        if struct.unpack_from('<I',state,4)[0] == 6 and model:
            by_model.setdefault(model,[]).append(row)
    instances = []
    report.update(blockers=[],baseline_sha256=hashlib.sha256(baseline).hexdigest(),
                  scope='DM frozen initial world: placed_world_obstacle AND unique current baseline pose; other classes excluded.',
                  baseline_contract=dict(stride=272,model_offset=0x98,origin_offset=0x18,angles_offset=0x3c,
                                         evidence='Every selected model ID and float32 pose cross-checked against current MapEnts.'))
    for placement in report['placements']:
        rows = by_model.get(placement['submodel'],[])
        placement['baseline_present'] = bool(rows)
        placement['installed'] = False
        if placement['category'] != 'placed_world_obstacle':
            placement['activation'] = 'excluded_from_dm_frozen_world'
            continue
        reason = None
        if len(rows) != 1:
            reason = 'missing or ambiguous type6 baseline'
        else:
            row,state = rows[0],rows[0]['state']
            origin = list(struct.unpack_from('<3f',state,0x18))
            angles = list(struct.unpack_from('<3f',state,0x3c))
            placement['baseline'] = dict(entity_number=row['entity_id'],record_index=row['index'],
                record_offset=8+row['index']*272,record_sha256=hashlib.sha256(state).hexdigest(),
                origin=origin,angles=angles,entity_flags=struct.unpack_from('<I',state,8)[0],
                position_type=struct.unpack_from('<I',state,12)[0],
                angular_type=struct.unpack_from('<I',state,48)[0])
            if not all(math.isfinite(v) for v in origin+angles):
                reason = 'nonfinite baseline pose'
            if placement['baseline']['position_type'] or placement['baseline']['angular_type']:
                reason = 'baseline trajectory is not stationary'
            if placement['baseline']['entity_flags']:
                reason = 'baseline entity flags require activation interpretation'
            for key,values in (('origin',origin),('angles',angles)):
                text = placement['fields'].get(key)
                if text is None and key == 'angles':
                    continue  # Baseline supplies the angle; no invented default.
                authored = [float(v) for v in (text or '').split()]
                if len(authored) != 3 or not all(math.isfinite(v) for v in authored) or any(abs(a-b)>1e-3 for a,b in zip(authored,values)):
                    reason = 'baseline/MapEnts '+key+' mismatch'
            if reason is None:
                model = geometry['submodels'][placement['submodel']]
                placement.update(installed=True,activation='frozen_at_dm_baseline_pose',
                    collision_contents=dict(brush=model['brush_contents'],terrain=model['terrain_contents'],
                                            source='clipMap submodel leaf; per-brush/per-material masks retained'))
                local = [v for i in model['brushes']
                         for v in product(*zip(geometry['brushes'][i]['mins'],geometry['brushes'][i]['maxs']))]
                for partition,_ in model['partitions']:
                    part = geometry['partitions'][partition]
                    local.extend(geometry['vertices'][v] for t in geometry['triangles'][part['first_tri']:part['first_tri']+part['tri_count']]
                                 for v in t)
                axis = placement_axis(angles)
                world = [[a+b for a,b in zip(transform_vector(v,axis),origin)] for v in local]
                if not world:
                    raise ValueError(f"*{placement['submodel']}: selected obstacle has no geometry")
                instances.append(dict(submodel=placement['submodel'],entity_number=row['entity_id'],
                                      map_entity_index=placement['entity_index'],origin=origin,angles=angles,
                                      mins=[min(v[i] for v in world) for i in range(3)],
                                      maxs=[max(v[i] for v in world) for i in range(3)]))
        if reason:
            placement['activation'] = 'unresolved: '+reason
            report['blockers'].append(f"*{placement['submodel']}: {reason}")
    report['installed_count'] = len(instances)
    return instances


def export_zones(zones, output, *, gametype='dm', source_records=None, registration=None):
    """Export explicitly supplied decoded FF423 zones into a new local directory.

    source_records carries offline FF provenance; it is not a runtime mount list.
    Registration evidence proves only its own historical name-list checksum.
    """
    output = Path(output).resolve()
    if not output.is_relative_to(OUTPUT_ROOT.resolve()) or output == OUTPUT_ROOT.resolve():
        raise ValueError('output must be a new directory under research/experiments/independent-match')
    if output.exists():
        raise ValueError('output directory already exists; select a new export directory')
    map_assets = read_assets(zones[MAP])
    collision_assets = [data for kind, data in map_assets if kind == 15]
    worlds = [data for kind, data in map_assets if kind == 21]
    if len(collision_assets) != 1 or len(worlds) != 1:
        raise ValueError('expected exactly one Killhouse clipMap and GfxWorld')
    collision_bytes = collision_assets[0]
    collision = read_collision(collision_bytes)
    entity_text = collision.pop('entity_text')
    spawns = read_spawns(entity_text)
    filename = f'mp/constbaselines/bl_pc_{MAP}_{gametype}.bin'
    baseline_candidates = []
    for kind, data in read_assets(zones[MAP + '_const']):
        if kind == 36:
            name, payload = read_rawfile(data)
            if name == filename:
                baseline_candidates.append(payload)
    if len(baseline_candidates) != 1:
        raise ValueError('selected gametype baseline missing or ambiguous')
    baseline = baseline_candidates[0]
    baseline_rows = read_baselines(baseline)
    ncs = dict(tables=[], unresolved=[], empty_assets=[], registry=None, checksum_seed=None,
               client_checksum=None, mounted_set_verified=False, client_checksum_verified=False,
               status='unverified', registration_evidence=None,
               selected_zones=list(zones), missing_candidate_zones=[n for n in ZONE_NAMES if n not in zones])
    inputs = []
    for name, zone in zones.items():
        row = dict((source_records or {}).get(name, {}))
        row.update(name=name, zone_bytes=len(zone), zone_sha256=hashlib.sha256(zone).hexdigest())
        inputs.append(row)
        result = read_zone_ncs(zone)
        for key in ('tables', 'unresolved', 'empty_assets'):
            ncs[key].extend(dict(item, zone=name) for item in result[key])
    if registration is not None:
        from decode_story_fastfile import CLIENT_SHA256
        names = registration['names']
        if not names or not all(isinstance(n, str) and n and n.isascii() and '\0' not in n for n in names):
            raise ValueError('invalid network registration names')
        seed = zlib.crc32(''.join(names).encode('ascii'))
        if registration['checksum_seed'] != seed or registration['exe_sha256'] != CLIENT_SHA256:
            raise ValueError('registration evidence seed/client mismatch')
        ncs['checksum_seed'] = seed
        ncs['registration_evidence'] = dict(names=names, checksum_seed=seed,
            exe_sha256=CLIENT_SHA256, status='historical_seed_names_consistent_not_live_verified')
        if not ncs['unresolved']:
            try:
                ncs['registry'] = build_registry(ncs['tables'], checksum_seed=seed)
                ncs['status'] = 'offline_candidate_only'
            except ValueError as error:
                ncs['unresolved'].append(dict(reason=str(error), stage='registration'))
    unresolved = [
        'Actual client mounted NCS set/order and final checksum have not been observed for this export.',
        'Collision sections contain serialized references; shared planes and model geometry are unresolved.',
        'Static model instances are preserved, but their collision geometry is not exported.',
        'Trailing stage/dynamic data is preserved in collision.bin but not interpreted.',
        'Spawn locations are authored data; clearance, grounding and occupancy have not been checked.',
        'Map quantization center/position_base is unresolved; see position.json before entity position encoding.',
    ]
    if ncs['unresolved']:
        unresolved.append('Some selected NCS assets could not be resolved; no registry was published.')
    if registration is None:
        unresolved.append('No checksum seed evidence supplied; no candidate registry was built.')
    if ncs['missing_candidate_zones']:
        unresolved.append('The selected inputs omit zones from the proposed offline candidate set.')
    manifest = dict(schema_version=1, format_version=423, map=MAP, gametype=gametype,
        map_checksum=collision['checksum'], inputs=inputs, runtime_dependencies=[], files={},
        baseline=dict(name=filename, count=len(baseline_rows), stride=272),
        spawn_count=len(spawns), ncs_status=ncs['status'], physics_ready=False,
        integrity_scope='Source and exported byte hashes; not gameplay or client compatibility validation.',
        unresolved=unresolved)
    output.mkdir(parents=True)

    def save(name, data):
        (output / name).write_bytes(data)
        manifest['files'][name] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

    def save_json(name, value):
        save(name, (json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode())

    save('collision.bin', collision_bytes)
    save('gfxworld.bin', worlds[0])
    save('entities.txt', entity_text)
    save('baseline.bin', baseline)
    for name, section in collision['sections'].items():
        if section['offset'] is not None:
            section['file'] = f'collision.{name}.bin'
            start = section['offset']
            save(section['file'], collision_bytes[start:start + section['count'] * section['stride']])
    save_json('collision.json', collision)
    save_json('spawns.json', spawns)
    save_json('ncs.json', ncs)
    enrich_geometry(manifest, collision, collision_bytes, worlds[0], spawns, save_json,
                    model_zones={n:z for n,z in zones.items() if n == 'common_mp'},baseline=baseline)
    # Written last: an interrupted export has no usable package manifest.
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


def select_position(geometry, spawns):
    """Choose a server center; do not claim an original authored map secret.

    CS16 and its reader contract are verified by test_match_snapshot's current
    client test. Include all decoded geometry bounds, unresolved static instance
    bounds, and spawn points; future moving entities must stay in this envelope.
    """
    points = list(geometry['vertices']) + [s['origin'] for s in spawns]
    for b in geometry['brushes'] + geometry['static_models'] + geometry.get('submodel_instances',[]):
        points.extend((b['mins'],b['maxs']))
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    qlo = [math.floor(v+.5) for v in lo]
    qhi = [math.floor(v+.5) for v in hi]
    # Integer midpoint is exactly representable as float32 at these map scales.
    base = [(a+b+1)//2 for a,b in zip(qlo,qhi)]
    fits = all(-2147483648 <= b <= 2147483647 and
               struct.unpack('<f',struct.pack('<f',b))[0] == b and
               a >= b-32768 and c <= b+32767 for a,b,c in zip(qlo,base,qhi))
    return dict(center=base if fits else None, position_base=base if fits else None,
        server_selected=fits, authored_center=False, client423_verified=True,
        status='server_selected' if fits else 'unresolved_range_exceeds_codec',
        configstring_index=16, configstring_value=' '.join(map(str,base)) if fits else None,
        selection='Integer midpoint of exported-map-bounds, including unresolved static instance bounds and spawns.',
        bounds=dict(mins=lo,maxs=hi), quantized_bounds=dict(mins=qlo,maxs=qhi),
        all_exported_bounds_encodable=fits,
        verification_scope='Client CS16 parsing and entity position codec contract; not authored center or world closure.',
        evidence=dict(file='research/evidence/client-gamestate-instructions423.json',
                      configstring_call='0x46e0e1 -> 0x4f9850 with ECX=16',
                      sscanf_call='0x46e0ec', destinations=['0x78b0a78','0x78b0a7c','0x78b0a80'],
                      test='tests/test_match_snapshot.py::test_map_center_is_server_supplied_configstring_16',
                      note='Current-client emulation replaces CRT sscanf only; entity reader verifies quantization.'),
        unresolved=[] if fits else ['Exported bounds cannot share this 16-bit position window.'])


def enrich_geometry(manifest, collision, data, world, spawns, save_json, *, model_zones=None, baseline):
    from match_server.collision import CollisionWorld
    from match_xmodel423 import install_static_models
    inputs = {i['name']:i['zone_sha256'] for i in manifest['inputs']}
    for name,zone in (model_zones or {}).items():
        if hashlib.sha256(zone).hexdigest() != inputs.get(name):
            raise ValueError(f'model zone {name} does not match this current423 package input')
    geometry = read_geometry(data,world)
    static_closure = install_static_models(geometry,world,model_zones)
    submodels = classify_submodels(read_collision(data)['entity_text'],geometry)
    geometry['submodel_instances'] = select_dm_submodels(submodels,baseline,geometry) if manifest['gametype']=='dm' else []
    missing = sum(m['geometry'] is None for m in geometry['static_models'])
    scope = 'dm_frozen_initial_static'
    blockers = ([f'{missing} instances still need external XModel definitions; see static-model-closure.json.'] if missing else [])
    blockers += submodels.get('blockers',['Only DM frozen-world selection is implemented.'])
    position = select_position(geometry,spawns)
    if not position['all_exported_bounds_encodable']:
        blockers.append('Placed world bounds exceed the position encoding window.')
    ready = not blockers
    exclusions = [
        '38 gameplay/training/utility inline models are excluded by the declared DM frozen-mode selection.',
        'Script-driven movement, runtime spawn_player_clip creation and dynamic/glass destruction are not simulated.',
        'The 49744-byte dynamic tail and capsule/client physics parity are outside this static geometry contract.']
    geometry['closure'].update(unresolved_static_models=missing,static_xmodels_complete=not missing,
                              submodel_placements_file='submodel-placements.json',
                              submodel_categories=submodels['counts'],installed_submodels=len(geometry['submodel_instances']),
                              unplaced_submodels=submodels['counts'].get('placed_world_obstacle',0)-len(geometry['submodel_instances'])
                                  if manifest['gametype']=='dm' else 116,
                              excluded_submodels=116-submodels['counts'].get('placed_world_obstacle',0) if manifest['gametype']=='dm' else 0,
                              frozen_world_ready=ready,readiness_scope=scope,blockers=blockers,excluded=exclusions)
    geometry.update(physics_ready=ready,readiness_scope=scope)
    consumer = CollisionWorld(geometry)
    ground = dict(scope=scope,max_drop=512,contents_mask=1,physics_ready=ready,
                  limitations='No capsule clearance, step handling, occupancy, full player mask or client physics parity.',
                  points=[dict(entity_index=p['entity_index'],classname=p['classname'],origin=p['origin'],
                               trace=consumer.ground_point(p['origin'])) for p in spawns])
    ground['hit_count'] = sum(p['trace']['hit'] for p in ground['points'])
    ground['start_solid_count'] = sum(p['trace']['start_solid'] for p in ground['points'])
    collision.update(shared_planes_resolved=True,brush_terrain_decoded=True,geometry_file='geometry.json',
                     physics_ready=ready,readiness_scope=scope,static_model_geometry_exported=not missing,
                     installed_submodels=len(geometry['submodel_instances']))
    collision['sections']['planes']['resolved_geometry'] = 'geometry.json:planes'
    manifest.update(position_status=position['status'],physics_ready=ready,readiness_scope=scope,
                    excluded_from_readiness=exclusions,
                    geometry=dict(planes=len(geometry['planes']),brushes=len(geometry['brushes']),
                                  triangles=len(geometry['triangles']),world_brushes=len(geometry['world_brushes']),
                                  world_partitions=len(geometry['world_partitions']),
                                  static_xmodels=len(geometry['xmodels']),static_triangle_records=static_closure['triangle_records'],
                                  installed_submodels=len(geometry['submodel_instances']),
                                  closure=geometry['closure']))
    replacements = {
        'Spawn point rays are provisional partial-world contacts; capsule clearance and occupancy remain unchecked.':
            'Spawn point contacts are exported; World remains responsible for player-box clearance and occupancy.',
        'Static model instances are preserved, but their collision geometry is not exported.':
            'Static XModel closure is complete; script-controlled inline model state remains excluded.' if not missing else
            'Some external static XModel definitions remain missing; see static-model-closure.json.',
        'Collision sections contain serialized references; shared planes and model geometry are unresolved.':
            'Shared planes and brush/terrain geometry are resolved; full-world closure remains incomplete.',
        'Spawn locations are authored data; clearance, grounding and occupancy have not been checked.':
            'Spawn point rays are provisional partial-world contacts; capsule clearance and occupancy remain unchecked.',
        'Map quantization center/position_base is unresolved; see position.json before entity position encoding.':
            'CS16 center is server-selected from exported bounds; entities outside the checked window must be rejected.'
            if position['server_selected'] else 'No common position encoding window fits the exported bounds.'}
    manifest['unresolved'] = [replacements.get(x,x) for x in manifest['unresolved']]
    # Rewrite previous package's collision caveats around the explicit frozen
    # contract. NCS uncertainty remains independent of geometry readiness.
    superseded = {
        'Static XModel closure is complete; script-controlled inline model state remains excluded.',
        'Some external static XModel definitions remain missing; see static-model-closure.json.',
        'Shared planes and brush/terrain geometry are resolved; full-world closure remains incomplete.',
        'Trailing stage/dynamic data is preserved in collision.bin but not interpreted.'}
    manifest['unresolved'] = [x for x in manifest['unresolved'] if x not in superseded]
    manifest['unresolved'].extend(blockers)
    for name,value in [('geometry.json',geometry),('spawn-grounding.json',ground),
                       ('position.json',position),('collision.json',collision),('static-model-closure.json',static_closure),
                       ('submodel-placements.json',submodels)]:
        save_json(name,value)


def export_geometry_package(source, output, *, model_zones=None):
    """Enrich a hash-verified existing export: no zone decrypt or EXE access."""
    from match_server.mapdata import load_map
    source,output = Path(source).resolve(),Path(output).resolve()
    if not output.is_relative_to(OUTPUT_ROOT.resolve()) or output == OUTPUT_ROOT.resolve() or output.exists():
        raise ValueError('output must be a new directory under research/experiments/independent-match')
    loaded = load_map(source)
    manifest = loaded['manifest']
    manifest['parent_manifest_sha256'] = hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest()
    files = loaded['files']

    def save_json(name, value):
        data = (json.dumps(value,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n').encode()
        files[name] = data
        manifest['files'][name] = dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

    enrich_geometry(manifest,loaded['collision'],files['collision.bin'],files['gfxworld.bin'],loaded['spawns'],save_json,
                    model_zones=model_zones,baseline=files['baseline.bin'])
    output.mkdir(parents=True)
    for name,data in files.items():
        (output/name).parent.mkdir(parents=True,exist_ok=True)
        (output/name).write_bytes(data)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-package', type=Path, help='reuse a verified export; no decryption/client required')
    parser.add_argument('--model-zone', type=Path, action='append', default=[],
                        help='decoded current423 model source zone; must match a package input SHA256')
    parser.add_argument('--assets', type=Path, help='directory containing signed FF423 files')
    parser.add_argument('--client', type=Path, help='matching 3.3.3.3 client, read as bytes only')
    parser.add_argument('--registration', type=Path, help='historical network-dvar registration evidence JSON')
    parser.add_argument('--gametype', default='dm')
    parser.add_argument('--output', type=Path, required=True, help='new directory under independent-match')
    args = parser.parse_args()
    if args.from_package:
        manifest = json.loads((args.from_package/'manifest.json').read_text(encoding='utf-8'))
        names = {i['zone_sha256']:i['name'] for i in manifest['inputs']}
        model_zones = {}
        for path in args.model_zone:
            zone = path.read_bytes()
            name = names.get(hashlib.sha256(zone).hexdigest())
            if name is None:
                parser.error(f'{path}: source hash is not an input of this package')
            model_zones[name] = zone
        report = export_geometry_package(args.from_package,args.output,model_zones=model_zones)
        print(json.dumps(dict(output=str(args.output.resolve()),geometry=report['geometry'],
                              position_status=report['position_status'],physics_ready=report['physics_ready'],
                              readiness_scope=report['readiness_scope']),indent=2))
        return
    if not args.assets or not args.client:
        parser.error('supply --from-package or both --assets and --client')
    from decode_story_fastfile import decode, CLIENT_SHA256
    client = args.client.read_bytes()
    if hashlib.sha256(client).hexdigest() != CLIENT_SHA256:
        raise ValueError('client hash mismatch')
    zones, sources = {}, {}
    for name in ZONE_NAMES:
        wire = (args.assets / (name + '.ff')).read_bytes()
        zones[name] = decode(client, wire, name)
        sources[name] = dict(ff_bytes=len(wire), ff_sha256=hashlib.sha256(wire).hexdigest(),
                             client_sha256=CLIENT_SHA256, signed_ff_verified=True)
    registration = None
    if args.registration:
        raw = args.registration.read_bytes()
        registration = json.loads(raw)
        sources[MAP]['registration_evidence_sha256'] = hashlib.sha256(raw).hexdigest()
    report = export_zones(zones, args.output, gametype=args.gametype,
                          source_records=sources, registration=registration)
    print(json.dumps(dict(output=str(args.output.resolve()), files=len(report['files']),
        baseline_count=report['baseline']['count'], spawn_count=report['spawn_count'],
        ncs_status=report['ncs_status'], physics_ready=False), indent=2))


if __name__ == '__main__':
    main()
