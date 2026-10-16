# SPDX-License-Identifier: AGPL-3.0-or-later
"""Analytical point/box queries on brushes, terrain and static XModel surfaces.

Readiness is scoped to the explicitly exported frozen world. Triangle
queries are two-sided. No AABB is substituted for missing model geometry.
"""
import math
from itertools import combinations, product


def _dot(a, b):
    return sum(x*y for x,y in zip(a,b))


def _sub(a, b):
    return tuple(x-y for x,y in zip(a,b))


def _segment_bounds(start, end, low, high, half=(0,0,0)):
    """Conservative segment/AABB candidate test, including box expansion."""
    near,far=0.0,1.0
    for i in range(3):
        lo,hi=low[i]-half[i]-1e-8,high[i]+half[i]+1e-8
        delta=end[i]-start[i]
        if delta == 0:
            if start[i] < lo or start[i] > hi:
                return False
            continue
        a,b=(lo-start[i])/delta,(hi-start[i])/delta
        near,far=max(near,min(a,b)),min(far,max(a,b))
        if near > far:
            return False
    return True


def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


_AXES = ((1,0,0),(0,1,0),(0,0,1))


def placement_axis(angles):
    """Reference q_math.c AnglesToAxis, columns of the local-to-world map."""
    pitch,yaw,roll = map(math.radians,angles)
    cp,sp,cy,sy,cr,sr = math.cos(pitch),math.sin(pitch),math.cos(yaw),math.sin(yaw),math.cos(roll),math.sin(roll)
    return ((cp*cy,cp*sy,-sp),(sr*sp*cy-sy*cr,sr*sp*sy+cr*cy,sr*cp),
            (cr*sp*cy+sr*sy,cr*sp*sy-sr*cy,cr*cp))


def transform_vector(vector, axis):
    return [sum(vector[j]*axis[j][i] for j in range(3)) for i in range(3)]


def _brush_planes(geometry, brush):
    planes = []
    for sign in (-1,1):
        for axis in range(3):
            normal = [0,0,0]
            normal[axis] = sign
            dist = -brush['mins'][axis] if sign == -1 else brush['maxs'][axis]
            material = brush['axial_materials'][(0 if sign == -1 else 3)+axis]
            planes.append((normal,dist,material))
    for side in geometry['sides'][brush['first_side']:brush['first_side']+brush['side_count']]:
        p = geometry['planes'][side['plane']]
        planes.append((p[:3],p[3],side['material']))
    return planes


def model_to_world(point, instance):
    # CM_TraceStaticModel uses columns of inverseScaledAxis to map world to
    # model. Invert that exact matrix; don't apply animated bone transforms.
    axis = instance['inverse_scaled_axis']
    a,b,c = axis[0::3],axis[1::3],axis[2::3]
    bc,ca,ab = _cross(b,c),_cross(c,a),_cross(a,b)
    det = _dot(a,bc)
    if abs(det) < 1e-20:
        raise ValueError('singular static model transform')
    return [instance['origin'][i]+(point[0]*bc[i]+point[1]*ca[i]+point[2]*ab[i])/det
            for i in range(3)]


def _triangle(a, b, c):
    e1,e2 = _sub(b,a),_sub(c,a)
    n = _cross(e1,e2)
    length = math.sqrt(_dot(n,n))
    if length == 0:
        return None
    return (a,e1,e2,[v/length for v in n],
            [min(a[i],b[i],c[i]) for i in range(3)],
            [max(a[i],b[i],c[i]) for i in range(3)])


def _hit_metadata(result, metadata):
    for key in ('submodel','entity_number','surface','triangle','model_reference','surface_flags'):
        result.pop(key,None)
    result.update(metadata)


class _SpatialIndex:
    """Median-split BVH. Bounds only select candidates for exact geometry."""
    def __init__(self, entries):
        # Entries: (mins, maxs, caller-owned stable key).
        def build(rows):
            lo = tuple(min(r[0][i] for r in rows) for i in range(3))
            hi = tuple(max(r[1][i] for r in rows) for i in range(3))
            if len(rows) <= 8:
                return lo,hi,rows,None,None
            spread = [max(r[0][i]+r[1][i] for r in rows)-min(r[0][i]+r[1][i] for r in rows)
                      for i in range(3)]
            axis = max(range(3),key=spread.__getitem__)
            rows.sort(key=lambda r:r[0][axis]+r[1][axis])
            mid = len(rows)//2
            return lo,hi,None,build(rows[:mid]),build(rows[mid:])
        self.root = build(list(entries)) if entries else None

    def query(self, lo, hi):
        result,stack = [],[self.root] if self.root else []
        def overlaps(a, b):
            return not (hi[0]<a[0] or lo[0]>b[0] or hi[1]<a[1] or lo[1]>b[1] or hi[2]<a[2] or lo[2]>b[2])
        while stack:
            low,high,rows,left,right = stack.pop()
            if not overlaps(low,high):
                continue
            if rows is None:
                stack.extend((left,right))
            else:
                result.extend(key for a,b,key in rows if overlaps(a,b))
        return result


def _projections(vertices, axes):
    result,seen = [],set()
    for axis in axes:
        length = math.sqrt(_dot(axis,axis))
        if length < 1e-10:
            continue
        normal = tuple(v/length for v in axis)
        key = tuple(round(v,10) for v in normal)
        if key in seen or tuple(-v for v in key) in seen:
            continue
        seen.add(key)
        values = [_dot(normal,v) for v in vertices]
        result.append((normal,min(values),max(values)))
    return result


def _brush_projections(planes):
    # A bounded convex brush is the intersection of ALL its halfspaces.
    # Reconstruct actual vertices; projecting only its AABB loses sloped faces.
    vertices = []
    for (a,da,_),(b,db,_),(c,dc,_) in combinations(planes,3):
        bc = _cross(b,c)
        det = _dot(a,bc)
        if abs(det) < 1e-10:
            continue
        ca,ab = _cross(c,a),_cross(a,b)
        v = tuple((da*bc[i]+db*ca[i]+dc*ab[i])/det for i in range(3))
        if all(_dot(n,v) <= d+1e-5 for n,d,_ in planes):
            vertices.append(v)
    if len(vertices) < 4:
        raise ValueError('brush halfspaces do not form a bounded convex solid')
    normals = [p[0] for p in planes]
    # Every real edge is an intersection of two face planes. Superset edge
    # directions add redundant valid separating axes, never fake geometry.
    axes = list(_AXES)+normals
    axes.extend(_cross(_cross(a,b),box_axis) for a,b in combinations(normals,2) for box_axis in _AXES)
    return _projections(vertices,axes)


def _sweep(start, end, half, projections):
    enter,leave,normal,inside = -math.inf,1.0,None,True
    for axis,lo,hi in projections:
        radius = sum(abs(n)*h for n,h in zip(axis,half))
        lo,hi = lo-radius,hi+radius
        a,b = _dot(axis,start),_dot(axis,end)
        inside &= lo+1e-8 < a < hi-1e-8
        speed = b-a
        if abs(speed) < 1e-12:
            # Tangential surface contact must not block horizontal sliding.
            if a <= lo+1e-8 or a >= hi-1e-8:
                return None
            continue
        t0,t1 = (lo-a)/speed,(hi-a)/speed
        n = [-v for v in axis] if speed > 0 else list(axis)
        if t0 > t1:
            t0,t1 = t1,t0
        if t0 >= enter:
            enter,normal = t0,n
        leave = min(leave,t1)
        if enter > leave or leave < 0:
            return None
    if inside:
        return 0.0,None,True
    # A prior contact can round just behind the surface. Retain its normal
    # and clamp that tiny negative time, instead of tunnelling into the slope.
    if normal is not None and -1e-8 <= enter <= 1 and leave >= enter:
        return max(0.0,enter),normal,False
    return None


class CollisionWorld:
    def __init__(self, geometry):
        self.geometry = geometry
        self.complete = bool(geometry['closure'].get('frozen_world_ready')) and not geometry['closure']['blockers']
        self._brush_axes = {}
        self._triangle_axes = {}
        self._static_cache = {}
        self._triangle_placements = {}
        self.brushes = []
        for index in geometry['world_brushes']:
            b = geometry['brushes'][index]
            self.brushes.append((index,b,_brush_planes(geometry,b)))
        self.triangles = []
        for partition, material in geometry['world_partitions']:
            part = geometry['partitions'][partition]
            for index in range(part['first_tri'], part['first_tri']+part['tri_count']):
                a,b,c = [geometry['vertices'][i] for i in geometry['triangles'][index]]
                edge1,edge2 = _sub(b,a),_sub(c,a)
                normal = _cross(edge1,edge2)
                length = math.sqrt(_dot(normal,normal))
                if length == 0:  # Degenerate triangles have no surface.
                    continue
                lo = [min(a[i],b[i],c[i]) for i in range(3)]
                hi = [max(a[i],b[i],c[i]) for i in range(3)]
                self.triangles.append((index,material,a,edge1,edge2,
                                       [v/length for v in normal],lo,hi))
        for instance in geometry.get('submodel_instances',[]):
            model = geometry['submodels'][instance['submodel']]
            axis,origin = placement_axis(instance['angles']),instance['origin']
            metadata = dict(submodel=instance['submodel'],entity_number=instance['entity_number'])
            def point(v):
                return [a+b for a,b in zip(transform_vector(v,axis),origin)]
            for index in model['brushes']:
                source = geometry['brushes'][index]
                planes = []
                for n,d,m in _brush_planes(geometry,source):
                    n = transform_vector(n,axis)
                    planes.append((n,d+_dot(n,origin),m))
                corners = [point(v) for v in product(*zip(source['mins'],source['maxs']))]
                brush = dict(source,mins=[min(v[i] for v in corners) for i in range(3)],
                             maxs=[max(v[i] for v in corners) for i in range(3)],placement=metadata)
                self.brushes.append((index,brush,planes))
            for partition,material in model['partitions']:
                part = geometry['partitions'][partition]
                for index in range(part['first_tri'],part['first_tri']+part['tri_count']):
                    triangle = _triangle(*(point(geometry['vertices'][i]) for i in geometry['triangles'][index]))
                    if triangle is not None:
                        self._triangle_placements[len(self.triangles)] = metadata
                        self.triangles.append((index,material,*triangle))
        entries = [(b['mins'],b['maxs'],(0,slot)) for slot,(_,b,_) in enumerate(self.brushes)]
        entries.extend((t[-2],t[-1],(1,slot)) for slot,t in enumerate(self.triangles))
        entries.extend((m['mins'],m['maxs'],(2,i)) for i,m in enumerate(geometry.get('static_models',[])))
        self._spatial = _SpatialIndex(entries)

    def _candidates(self, lo, hi):
        candidates = ([],[],[])
        # Preserve the pre-index ordering for simultaneous-contact tie breaks.
        for kind,index in sorted(self._spatial.query(lo,hi)):
            candidates[kind].append(index)
        return candidates

    def _query_triangles(self, overlaps, contents_mask, terrain, instances, query_lo, query_hi):
        for slot in terrain:
            index,material,*triangle = self.triangles[slot]
            if self.geometry['materials'][material]['contents'] & contents_mask and overlaps(*triangle[-2:]):
                placement = self._triangle_placements.get(slot,{})
                yield dict(kind='submodel_triangle' if placement else 'triangle',index=index,material=material,
                           **placement),triangle,(0,slot)
        for index in instances:
            instance = self.geometry['static_models'][index]
            if instance['geometry'] is None or not overlaps(instance['mins'],instance['maxs']):
                continue
            if index not in self._static_cache:
                model = self.geometry['xmodels'][instance['geometry']]
                rows = []
                for si,surface in enumerate(model['surfaces']):
                    for ti,vertices in enumerate(surface['triangles']):
                        triangle = _triangle(*(model_to_world(v,instance) for v in vertices))
                        if triangle is not None:
                            rows.append((si,ti,surface['contents'],surface['surface_flags'],triangle))
                self._static_cache[index] = rows,_SpatialIndex([(r[-1][-2],r[-1][-1],i) for i,r in enumerate(rows)])
            rows,spatial = self._static_cache[index]
            for slot in sorted(spatial.query(query_lo,query_hi)):
                si,ti,contents,flags,triangle = rows[slot]
                if contents & contents_mask and overlaps(*triangle[-2:]):
                    yield dict(kind='static_model',index=index,material=None,surface=si,triangle=ti,
                               model_reference=instance['model_reference'],surface_flags=flags),triangle,(1,index,slot)

    def require_ready(self):
        """Require frozen-world closure, not dynamic modes or client parity."""
        if not self.complete:
            raise ValueError('collision world incomplete: ' + '; '.join(self.geometry['closure']['blockers']))

    def trace_point(self, start, end, *, contents_mask, any_hit=False):
        """Nearest exact segment intersection, with an explicit partial-world flag.

        No engine contact epsilon, sweep radius, step or client prediction is
        emulated. A no-hit answer means only no hit in the exported world subset.
        Visibility can use any_hit to stop at an obstacle; shots keep nearest-hit.
        """
        if len(start) != 3 or len(end) != 3 or not all(math.isfinite(v) for v in (*start,*end)):
            raise ValueError('point trace requires finite vectors')
        direction = _sub(end,start)
        query_lo = [min(a,b) for a,b in zip(start,end)]
        query_hi = [max(a,b) for a,b in zip(start,end)]
        brushes,terrain,instances = self._candidates(query_lo,query_hi)
        result = dict(hit=False,fraction=1.0,position=list(end),normal=None,kind=None,index=None,
                      material=None,start_solid=False,complete=self.complete,contents_mask=contents_mask)

        def overlaps(lo, hi):
            return _segment_bounds(start,end,lo,hi)

        result['unresolved_static_models'] = [i for i in instances if self.geometry['static_models'][i]['geometry'] is None
                                               and overlaps(self.geometry['static_models'][i]['mins'],self.geometry['static_models'][i]['maxs'])]

        def hit(t, normal, kind, index, material, inside=False, **metadata):
            if not result['hit'] or t < result['fraction']:
                result.update(hit=True,fraction=t,position=[start[i]+t*direction[i] for i in range(3)],
                              normal=normal,kind=kind,index=index,material=material)
                _hit_metadata(result,metadata)
            result['start_solid'] |= inside

        for slot in brushes:
            index,brush,planes = self.brushes[slot]
            if not brush['contents'] & contents_mask or not overlaps(brush['mins'],brush['maxs']):
                continue
            enter,leave,normal,material = 0.0,1.0,None,None
            inside,intersects = True,True
            for n,d,m in planes:
                a,b = _dot(n,start)-d,_dot(n,end)-d
                inside &= a < 0
                if a > 0 and b > 0:
                    intersects = False
                    break
                if a == 0 and b < 0 and enter == 0:
                    normal,material = list(n),m
                if a <= 0 and b <= 0:
                    continue
                t = a/(a-b)
                if a > b:
                    if t >= enter:
                        enter,normal,material = t,list(n),m
                else:
                    leave = min(leave,t)
                if enter > leave:
                    intersects = False
                    break
            if intersects and (inside or normal is not None):
                placement = brush.get('placement',{})
                hit(0.0 if inside else enter,normal,'submodel_brush' if placement else 'brush',index,material,inside,**placement)
                if any_hit:
                    return result
        for metadata,(a,e1,e2,normal,lo,hi),_ in self._query_triangles(overlaps,contents_mask,terrain,instances,query_lo,query_hi):
            p = _cross(direction,e2)
            det = _dot(e1,p)
            if abs(det) < 1e-10:
                continue
            delta = _sub(start,a)
            u = _dot(delta,p)/det
            q = _cross(delta,e1)
            v = _dot(direction,q)/det
            if u < -1e-9 or v < -1e-9 or u+v > 1+1e-9:
                continue
            t = _dot(e2,q)/det
            if 0 <= t <= 1:
                n = normal if _dot(normal,direction) <= 0 else [-c for c in normal]
                hit(t,n,**metadata)
                if any_hit:
                    return result
        return result

    def trace_box(self, start, end, mins=(-15,-15,0), maxs=(15,15,70), *, contents_mask=0x2001001):
        """Continuous SAT for a translating box; position is the caller's origin.

        Brushes use face normals, box axes and edge-cross-box axes. Triangles
        use their normal, box axes and three edge-cross-box axes. This is exact
        convex geometry, without the old engine's contact epsilon or capsule
        approximation. Missing static instances are reported, not replaced.
        """
        vectors = (start,end,mins,maxs)
        if any(len(v) != 3 or not all(math.isfinite(x) for x in v) for v in vectors):
            raise ValueError('box trace requires finite vectors')
        if any(a >= b for a,b in zip(mins,maxs)):
            raise ValueError('box extents must have positive volume')
        half = [(b-a)/2 for a,b in zip(mins,maxs)]
        offset = [(a+b)/2 for a,b in zip(mins,maxs)]
        a,b = [start[i]+offset[i] for i in range(3)],[end[i]+offset[i] for i in range(3)]
        lo = [min(start[i],end[i])+mins[i] for i in range(3)]
        hi = [max(start[i],end[i])+maxs[i] for i in range(3)]
        brushes,terrain,instances = self._candidates(lo,hi)
        result = dict(hit=False,fraction=1.0,position=list(end),normal=None,kind=None,index=None,
                      material=None,start_solid=False,complete=self.complete,contents_mask=contents_mask)

        def overlaps(low, high):
            return _segment_bounds(a,b,low,high,half)

        result['unresolved_static_models'] = [i for i in instances if self.geometry['static_models'][i]['geometry'] is None
                                               and overlaps(self.geometry['static_models'][i]['mins'],self.geometry['static_models'][i]['maxs'])]

        def consider(projections, kind, index, material, **metadata):
            hit = _sweep(a,b,half,projections)
            if hit is None:
                return
            t,normal,inside = hit
            if not result['hit'] or t < result['fraction']:
                result.update(hit=True,fraction=t,position=[start[i]+t*(end[i]-start[i]) for i in range(3)],
                              normal=normal,kind=kind,index=index,material=material)
                _hit_metadata(result,metadata)
            result['start_solid'] |= inside

        for slot in brushes:
            index,brush,planes = self.brushes[slot]
            if not brush['contents'] & contents_mask or not overlaps(brush['mins'],brush['maxs']):
                continue
            if slot not in self._brush_axes:
                self._brush_axes[slot] = _brush_projections(planes)
            # Cross-edge contact has no unique material face; don't guess one.
            placement = brush.get('placement',{})
            consider(self._brush_axes[slot],'submodel_brush' if placement else 'brush',index,None,**placement)
        for metadata,(v,e1,e2,normal,low,high),key in self._query_triangles(overlaps,contents_mask,terrain,instances,lo,hi):
            if key not in self._triangle_axes:
                vertices = [v,tuple(v[i]+e1[i] for i in range(3)),tuple(v[i]+e2[i] for i in range(3))]
                axes = list(_AXES)+[normal]
                axes.extend(_cross(edge,axis) for edge in (e1,e2,_sub(e2,e1)) for axis in _AXES)
                self._triangle_axes[key] = _projections(vertices,axes)
            consider(self._triangle_axes[key],**metadata)
        return result

    def ground_point(self, origin, *, max_drop=512, contents_mask=1):
        """Provisional supporting point; no footprint/occupancy certification."""
        if not math.isfinite(max_drop) or max_drop <= 0:
            raise ValueError('max_drop must be positive')
        trace = self.trace_point(origin,[origin[0],origin[1],origin[2]-max_drop],contents_mask=contents_mask)
        trace['safe_spawn'] = False
        trace['status'] = ('start_solid' if trace['start_solid'] else
                          ('frozen_world_hit' if self.complete else 'partial_world_hit') if trace['hit'] else
                          ('no_surface_in_frozen_world' if self.complete else 'no_surface_in_partial_world'))
        return trace
