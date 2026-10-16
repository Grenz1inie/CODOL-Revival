# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded FF423 GfxWorld replay, starting at its verified shared plane span.

Ported from server3333/src/codol/assets/codol_load_blocks.c (replay_world*,
replay_model, replay_surfaces, replay_material) and codol_xmodel_collision.c.
Block 0 headers consume file bytes; block 2 runtime arrays consume none.
Only block 3 relocation is needed for collision/name/base-matrix data.
"""
import struct
import hashlib
import math
from bisect import bisect_right

INLINE = 0xffffffff


def u32(b, offset=0):
    return struct.unpack_from('<I',b,offset)[0]


def u16(b, offset=0):
    return struct.unpack_from('<H',b,offset)[0]


class Replay:
    def __init__(self, data, offset, reference):
        self.data,self.pos,self.block = data,offset,reference-0x30000001
        self.starts,self.spans,self.aliases = [],[],{}

    def take(self, size, align=4, block=3):
        if size < 0 or self.pos+size > len(self.data):
            raise ValueError(f'truncated replay at {self.pos}, bytes={size}')
        offset = self.pos
        self.pos += size
        if block == 3:
            self.block = (self.block+align-1)&-align
            if size:
                self.starts.append(self.block)
                self.spans.append((self.block,self.block+size,offset))
            self.block += size
        return self.data[offset:self.pos]

    def reserve_alias(self):
        self.block = (self.block+3)&-4
        ref = self.block+0x30000001
        self.block += 4
        return ref

    def resolve(self, ref, size):
        if not ref or (ref-1)>>28 != 3:
            raise ValueError(f'unsupported collision reference {ref:#x}')
        offset = (ref-1)&0xfffffff
        i = bisect_right(self.starts,offset)-1
        if i < 0 or offset+size > self.spans[i][1]:
            raise ValueError(f'collision reference not in replayed GfxWorld: {ref:#x} bytes={size}')
        start,_,source = self.spans[i]
        return self.data[source+offset-start:source+offset-start+size]

    def string(self, ref=INLINE):
        if ref == INLINE:
            return self.take(self.data.index(b'\0',self.pos)-self.pos+1,1)[:-1].decode('ascii')
        offset = (ref-1)&0xfffffff
        i = bisect_right(self.starts,offset)-1
        if i < 0:
            raise ValueError(f'name reference not replayed: {ref:#x}')
        data = self.resolve(ref,self.spans[i][1]-offset)
        return data[:data.index(b'\0')].decode('ascii')

    def asset(self, ref, kind):
        if ref < INLINE-1:
            return None
        alias = self.reserve_alias() if ref == INLINE-1 else None
        result = getattr(self,kind)()
        if alias is not None and kind == 'model':
            self.aliases[alias] = result
        return result

    def image(self):
        h = self.take(52,block=0)
        if u32(h,48) == INLINE:
            self.string()
        if u32(h) == INLINE:
            d = self.take(16)
            self.take(u32(d,12),1)

    def shader(self, declaration=False):
        h = self.take(100 if declaration else 16,block=0)
        if u32(h) == INLINE:
            self.string()
        if not declaration and u32(h,8):
            self.take(u16(h,12)*4)

    def declaration(self):
        self.shader(True)

    def technique(self):
        h = self.take(208,block=0)
        if u32(h) == INLINE:
            self.string()
        for i in range(48):
            if u32(h,16+4*i) != INLINE:
                continue
            t = self.take(8)
            passes = self.take(u16(t,6)*20,1)
            for j in range(0,len(passes),20):
                r = passes[j:j+20]
                for k,kind in enumerate(('declaration','shader','shader')):
                    self.asset(u32(r,k*4),kind)
                if u32(r,16):
                    args = self.take(sum(r[12:15])*8)
                    for k in range(0,len(args),8):
                        if u16(args,k) in (1,7) and u32(args,k+4) == INLINE:
                            self.take(16)
            if u32(t) == INLINE:
                self.string()

    def water(self):
        h = self.take(68)
        n = u32(h,12)*u32(h,16)
        for offset in (4,8):
            if u32(h,offset):
                self.take(n*(8 if offset == 4 else 4))
        self.asset(u32(h,64),'image')

    def material(self):
        h = self.take(104,block=0)
        if u32(h,16) == INLINE:
            self.string()
        self.asset(u32(h,88),'technique')
        if u32(h,92) == INLINE:
            rows = self.take(h[80]*12)
            for i in range(0,len(rows),12):
                ref = u32(rows,i+8)
                if rows[i+7] == 11:
                    if ref == INLINE:
                        self.water()
                else:
                    self.asset(ref,'image')
        if u32(h,96) == INLINE:
            self.take(h[81]*32,16)
        if u32(h,100) == INLINE:
            self.take(h[82]*8)

    def surfaces(self):
        h = self.take(48,block=0)
        if u32(h) == INLINE:
            self.string()
        if not u32(h,4):
            return
        rows = self.take(u16(h,8)*84)
        for i in range(0,len(rows),84):
            r = rows[i:i+84]
            if u32(r,28) == INLINE:
                self.take(sum(u16(r,20+2*j)*(2*j+1) for j in range(4))*2,2)
            if u32(r,32) == INLINE:
                self.take(u16(r,4)*32,16,block=6)
            if u32(r,44) == INLINE:
                rigid = self.take(u32(r,40)*12)
                for j in range(0,len(rigid),12):
                    if u32(rigid,j+8) == INLINE:
                        tree = self.take(40)
                        if u32(tree,28):
                            self.take(u32(tree,24)*16,16)
                        if u32(tree,36):
                            self.take(u32(tree,32)*2,2)
            if u32(r,16) == INLINE:
                self.take(u16(r,6)*6,16,block=7)

    def preset(self):
        h = self.take(68,block=0)
        for offset in (0,28):
            if u32(h,offset) == INLINE:
                self.string()

    def physics(self):
        h = self.take(72,block=0)
        if u32(h) == INLINE:
            self.string()
        if u32(h,8):
            geoms = self.take(u32(h,4)*68)
            for i in range(0,len(geoms),68):
                if not u32(geoms,i):
                    continue
                b = self.take(68)
                n = u16(b,24)
                if u32(b,28):
                    sides = self.take(n*8)
                    for j in range(n):
                        if u32(sides,j*8) == INLINE:
                            self.take(20)
                if u32(b,32):
                    self.take(u32(b,60),1)
                if u32(b,64) == INLINE:
                    self.take(n*20)

    def model(self):
        start = self.pos
        h = self.take(360,block=0)
        bones,roots = h[4:6]
        if roots > bones:
            raise ValueError('invalid XModel bone counts')
        name_ref = u32(h)
        try:
            name = self.string(name_ref)
        except ValueError:
            if name_ref == INLINE:
                raise
            name = None  # Names can precede GfxWorld; never infer from ordering.
        arrays = []
        for i,(stride,align) in enumerate(zip((2,1,8,12,1,32),(2,1,2,4,1,4))):
            size = (bones-roots if 1 <= i <= 3 else bones)*stride
            ref = u32(h,44+4*i)
            arrays.append(self.take(size,align) if ref == INLINE else (ref,size))
        if u32(h,68):
            materials = self.take(h[6]*4)
            for i in range(h[6]):
                self.asset(u32(materials,i*4),'material')
        for i in range(4):
            lod = 72+i*56
            self.asset(u32(h,lod+8),'surfaces')
            if u32(h,lod+12) == INLINE:
                self.string()
        surfaces = []
        if u32(h,300):
            rows = self.take(u32(h,304)*44)
            for i in range(0,len(rows),44):
                row = rows[i:i+44]
                ref,n = u32(row),u32(row,4)
                mid = struct.unpack_from('<3f',row,8)
                half = struct.unpack_from('<3f',row,20)
                if u32(row,32) >= bones or not all(math.isfinite(v) for v in (*mid,*half)) or min(half) < 0:
                    raise ValueError('invalid XModel surface bounds/bone')
                records = self.take(n*48) if ref == INLINE else (ref,n*48)
                surfaces.append(dict(bone=u32(row,32),contents=u32(row,36),surface_flags=u32(row,40),
                                     mins=[a-b for a,b in zip(mid,half)],
                                     maxs=[a+b for a,b in zip(mid,half)],
                                     records=records,record_reference=ref,record_count=n))
        if u32(h,312):
            self.take(bones*28)
        self.asset(u32(h,352),'preset')
        self.asset(u32(h,356),'physics')
        return dict(name=name,name_reference=name_ref,bones=bones,roots=roots,base_matrices=arrays[5],surfaces=surfaces,
                    source_offset=start,source_bytes=self.pos-start)

    def world_to_models(self):
        raw = self.data[:1608]
        h = raw[:80]+raw[80:96]+raw[108:164]+raw[164:264]+raw[264:424]+raw[1392:1608]
        self.take(u32(h,8)*20)
        if u32(h,60):
            self.take(u32(h,12)*2,2)
        count = u32(h,52)
        counts = self.take(count*4) if u32(h,68) else b''
        if u32(h,72):
            trees = self.take(count*4,128)
            for i in range(count):
                if u32(trees,i*4):
                    nodes = self.take(u32(counts,i*4)*44)
                    for j in range(0,len(nodes),44):
                        if u32(nodes,j+36) == INLINE:
                            self.take(u16(nodes,j+34)*2,2)
        if u32(h,76):
            cells = self.take(count*48)
            for i in range(0,len(cells),48):
                c = cells[i:i+48]
                if u32(c,28):
                    portals = self.take(u32(c,24)*60)
                    for j in range(0,len(portals),60):
                        if u32(portals,j+28):
                            self.take(portals[j+34]*12)
                for k in (32,40):
                    if u32(c,k+4):
                        self.take(c[k],1)
        d = raw[80:164]
        count = u32(d)
        if u32(d,4):
            images = self.take(count*4)
            for i in range(count):
                self.asset(u32(images,4*i),'image')
        if u32(d,8):
            probes = self.take(count*20)
            for i in range(0,len(probes),20):
                if u32(probes,i+12):
                    volumes = self.take(u32(probes,i+16)*104)
                    for j in range(0,len(volumes),104):
                        if u32(volumes,j+96):
                            self.take(u32(volumes,j+100)*2,2)
        count = u32(d,16)
        if u32(d,20):
            self.take(count*12)
        if u32(d,24):
            self.take(count,1)
        d = d[:16]+d[28:]
        count = u32(d,16)
        if u32(d,20):
            images = self.take(count*8)
            for i in range(count*2):
                self.asset(u32(images,i*4),'image')
        for i in (32,36):
            self.asset(u32(d,i),'image')
        for ptr,n,stride,align in ((44,40,44,4),(56,52,1,1),(68,64,2,2)):
            if u32(d,ptr):
                self.take(u32(d,n)*stride,align)
        g = h[152:208]
        if u32(g,28):
            axis = u32(g,20)
            if axis > 2:
                raise ValueError('invalid light grid axis')
            self.take((u16(g,14+2*axis)-u16(g,8+2*axis)+1)*2,2)
        for ptr,n,stride in ((36,32,1),(44,40,4),(52,48,168)):
            if u32(g,ptr):
                self.take(u32(g,n)*stride,1 if stride == 1 else 4)
        if u32(h,212):
            self.take(u32(h,208)*60)
        if u32(h,248):
            rows = self.take(u32(h,244)*8)
            for i in range(0,len(rows),8):
                self.asset(u32(rows,i),'material')
        for i in (256,260,264,268):
            self.asset(u32(h,i),'material')
        self.asset(u32(h,412),'image')
        lights = u32(h,32)
        if u32(h,448):
            rows = self.take(lights*12)
            for i in range(0,len(rows),12):
                for j in (0,1):
                    if u32(rows,i+4+j*4):
                        self.take(u16(rows,i+2*j)*2,2)
        if u32(h,452):
            rows = self.take(lights*8)
            for i in range(0,len(rows),8):
                if u32(rows,i+4):
                    hulls = self.take(u32(rows,i)*80)
                    for j in range(0,len(hulls),80):
                        if u32(hulls,j+76):
                            self.take(u32(hulls,j+72)*20)
        p = h[456:564]
        models,surfaces = u32(p),u32(h,16)
        if u32(p,76):
            self.take((u32(p,4)+u32(p,8))*2,2)
        if u32(p,80):
            self.take(models*36)
        if u32(p,84):
            rows = self.take(surfaces*24)
            for i in range(0,len(rows),24):
                self.asset(u32(rows,i+16),'material')
        if u32(p,88):
            self.take(surfaces*24)
        if u32(p,92) != INLINE:
            raise ValueError('missing inline static draw array')
        slots = ((self.block+3)&-4)+0x30000001
        rows = self.take(models*76)
        for i in range(models):
            result = self.asset(u32(rows,i*76+52),'model')
            if result is not None:
                self.aliases[slots+i*76+52] = result


def read_static_models(world, plane_offset, plane_reference):
    replay = Replay(world,plane_offset,plane_reference)
    replay.world_to_models()
    for model in {id(m):m for m in replay.aliases.values()}.values():
        finish_model(model,replay)
    return replay.aliases


def finish_model(model, replay):
    base = model['base_matrices']
    if isinstance(base,tuple):
        base = replay.resolve(*base) if base[1] else b''
    model['base_matrices'] = list(struct.iter_unpack('<8f',base))
    for surface in model['surfaces']:
        records = surface['records']
        if isinstance(records,tuple):
            records = replay.resolve(*records) if records[1] else b''
        surface['records_sha256'] = hashlib.sha256(records).hexdigest()
        surface['records'] = list(struct.iter_unpack('<12f',records))
        surface['triangles'] = [triangle_vertices(r) for r in surface['records']]
    start,size = model['source_offset'],model['source_bytes']
    model['source_sha256'] = hashlib.sha256(replay.data[start:start+size]).hexdigest()


def triangle_vertices(record):
    """Invert XModelTraceLine's plane and two barycentric covectors.

    _xmodel.asm: plane dot(p)=d, s=dot(svec,p)-sw, t=dot(tvec,p)-tw;
    accept s>=0, t>=0, s+t<=1. Static triangles are already model-space,
    even when boneIdx!=0; only XModelTraceLineAnimated applies bone motion.
    """
    from reference_match.collision import _cross, _dot
    n,s,t = record[:3],record[4:7],record[8:11]
    st,tn,ns = _cross(s,t),_cross(t,n),_cross(n,s)
    det = _dot(n,st)
    if not all(math.isfinite(v) for v in record) or abs(det) < 1e-20:
        raise ValueError('singular or nonfinite XModel collision triangle')
    return [[(record[3]*st[i]+(record[7]+u)*tn[i]+(record[11]+v)*ns[i])/det
             for i in range(3)] for u,v in ((0,0),(1,0),(0,1))]


def install_static_models(geometry, world, model_zones=None):
    """Resolve only this clipMap's aliases and external names; no rendering.

    model_zones contains decoded current423 zones, verified against the source
    package's input hashes by the exporter. Only selected inline model payloads
    are replayed; unsupported shared references fail rather than invent data.
    """
    from index_story_zone import read_assets
    from reference_match.collision import model_to_world
    from itertools import product
    aliases = read_static_models(world,geometry['provenance']['plane_offset'],
                                 geometry['provenance']['plane_reference'])
    references = sorted({m['model_reference'] for m in geometry['static_models']})
    wanted = {m['name'][1:] for ref,m in aliases.items()
              if ref in references and m['name'] and m['name'].startswith(',')}
    external = {}
    for zone_name,zone in (model_zones or {}).items():
        zone_hash = hashlib.sha256(zone).hexdigest()
        for index,(kind,payload) in enumerate(read_assets(zone)):
            if kind != 4 or len(payload) < 360 or u32(payload) != INLINE:
                continue
            name = payload[360:payload.index(b'\0',360)].decode('ascii')
            if name not in wanted:
                continue
            replay = Replay(payload,0,0x30000001)
            model = replay.model()
            if replay.pos != len(payload):
                raise ValueError(f'XModel {name}: unaccounted source bytes')
            finish_model(model,replay)
            model['provenance'] = dict(zone=zone_name,zone_sha256=zone_hash,asset_index=index,
                                       format_version=423,source='type4_payload')
            if name in external and external[name]['source_sha256'] != model['source_sha256']:
                raise ValueError(f'ambiguous external XModel definition: {name}')
            external[name] = model
    xmodels,unresolved,rows = {},[],[]
    world_hash = hashlib.sha256(world).hexdigest()
    for ref in references:
        model = aliases.get(ref)
        stub = model['name'] if model else None
        if stub and stub.startswith(','):
            model = external.get(stub[1:])
        if model is None:
            unresolved.append(dict(reference=ref,name=stub,missing='external type4 definition' if stub else 'GfxWorld model alias'))
            continue
        if 'provenance' not in model:
            model['provenance'] = dict(file='gfxworld.bin',sha256=world_hash,format_version=423,
                                       source='replay_world_dpvs/smodelDrawInst+52')
        xmodels[str(ref)] = model
        vertices = [v for s in model['surfaces'] for t in s['triangles'] for v in t]
        if vertices:
            model['mins'] = [min(v[i] for v in vertices) for i in range(3)]
            model['maxs'] = [max(v[i] for v in vertices) for i in range(3)]
        rows.append(dict(reference=ref,name=model['name'],external_name=stub if stub and stub.startswith(',') else None,
                         surface_count=len(model['surfaces']),triangle_records=sum(len(s['records']) for s in model['surfaces']),
                         source_sha256=model['source_sha256'],provenance=model['provenance']))
    for instance in geometry['static_models']:
        key = str(instance['model_reference'])
        instance['geometry'] = key if key in xmodels else None
        if key in xmodels and 'mins' in xmodels[key]:
            model = xmodels[key]
            # Bounds are only broad-phase. Every narrow-phase hit uses triangles.
            corners = [model_to_world(v,instance) for v in product(*zip(model['mins'],model['maxs']))]
            instance['source_bounds'] = dict(mins=instance['mins'],maxs=instance['maxs'])
            instance['mins'] = [min(instance['mins'][i],*(v[i] for v in corners)) for i in range(3)]
            instance['maxs'] = [max(instance['maxs'][i],*(v[i] for v in corners)) for i in range(3)]
    geometry['xmodels'] = xmodels
    return dict(status='resolved' if not unresolved else 'missing_external_models',
                scope='All clipMap static instances; model-space surfaces transformed by inverseScaledAxis and origin.',
                instance_count=len(geometry['static_models']),distinct_aliases=len(references),resolved=len(xmodels),
                unresolved=unresolved,aliases=rows,triangle_records=sum(r['triangle_records'] for r in rows),
                contract=dict(record_stride=48,surface_stride=44,
                              equations='n.p=d; s=svec.p-sw; t=tvec.p-tw; s>=0; t>=0; s+t<=1',
                              bone_transform='None for static XModelTraceLine',
                              start_solid_scope='Brush volume or box/surface overlap; mesh interiors are not certified solids.',
                              source='server3333/src/asmsource/_xmodel.asm:XModelTraceLine; _cm_staticmodel.asm:CM_TraceStaticModel',
                              query_semantics='Two-sided mathematical triangles and axis-aligned box SAT; no legacy contact epsilon.'))
