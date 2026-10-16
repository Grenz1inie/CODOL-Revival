# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reference waypoint format and A*, checked against the current map geometry."""
import csv
import heapq
import io
import math


class Navigation:
    def __init__(self, nodes, collision):
        self.nodes,self.collision=nodes,collision
        self.edges={}

    @classmethod
    def from_csv(cls, text, collision):
        rows=list(csv.reader(io.StringIO(text)))
        count=int(rows.pop(0)[0])
        if not 1 <= count <= 4096 or len(rows)!=count:
            raise ValueError('invalid waypoint count')
        nodes=[]
        for row in rows:
            if len(row)<3:
                raise ValueError('truncated waypoint')
            position=list(map(float,row[0].split()))
            links=list(map(int,row[1].split()))
            if (len(position)!=3 or not all(map(math.isfinite,position))
                    or any(n<0 or n>=count for n in links) or len(links)>48):
                raise ValueError('invalid waypoint position or link')
            # The old graph supplies XY/connectivity, not the current floor.
            # Only settle within one step; reject occupied/unsupported nodes.
            standing=row[2] in ('stand','grenade','claymore','javelin')
            if standing and collision is not None:
                x,y,z=position
                ground=collision.trace_box([x,y,z+18],[x,y,z-18])
                standing=(ground['hit'] and not ground['start_solid']
                          and ground['normal'][2] >= .7 and not ground.get('unresolved_static_models'))
                if standing:
                    position=[x,y,ground['position'][2]+.125]
            nodes.append(dict(position=position,links=links,standing=standing))
        return cls(nodes,collision)

    def _clear(self, a, b):
        def clear(start,end):
            trace=self.collision.trace_box(start,end)
            return trace['fraction'] >= 1 and not trace['start_solid'] and not trace.get('unresolved_static_models')
        if clear(a,b):
            return True
        # World._move can step 18 units. A flat sweep alone rejects curbs and
        # slight terrain rises in the reference graph. Check both end lifts
        # as edges are cached bidirectionally; walls/ceilings still obstruct.
        up_a=[a[0],a[1],a[2]+18]
        up_b=[b[0],b[1],b[2]+18]
        return clear(a,up_a) and clear(b,up_b) and clear(up_a,up_b)

    def _nearest(self, position):
        # Match the reference bot's 256-unit local graph attachment. Sweeping
        # every distant node when no local node is reachable stalls input ticks.
        order=sorted((i for i,node in enumerate(self.nodes)
                      if math.dist(position,node['position']) < 256),
                     key=lambda i:math.dist(position,self.nodes[i]['position']))
        return next((i for i in order if self.nodes[i]['standing']
                     and self._clear(position,self.nodes[i]['position'])),None)

    def route(self, start, goal):
        # Long distances belong to the waypoint graph, not repeated sweeps
        # across all geometry between two players on opposite sides of a map.
        if math.dist(start,goal) < 256 and self._clear(start,goal):
            return [list(goal)]
        first=self._nearest(start)
        if first is None:
            return []
        last=self._nearest(goal)
        if last is None:
            return []
        costs,parents,queue={first:0},{first:None},[(0,first)]
        while queue:
            _,index=heapq.heappop(queue)
            if index==last:
                path=[list(goal)]
                while index is not None:
                    path.append(self.nodes[index]['position'])
                    index=parents[index]
                path.reverse()
                # Replanning must not revisit the nearest node behind the bot
                # when the next node is already reachable from its position.
                while len(path)>1 and math.dist(start,path[1]) < 256 and self._clear(start,path[1]):
                    path.pop(0)
                return path
            node=self.nodes[index]
            for other in node['links']:
                target=self.nodes[other]
                if not target['standing']:
                    continue
                edge=tuple(sorted((index,other)))
                if edge not in self.edges:
                    self.edges[edge]=self._clear(node['position'],target['position'])
                if not self.edges[edge]:
                    continue
                cost=costs[index]+math.dist(node['position'],target['position'])
                if cost >= costs.get(other,float('inf')):
                    continue
                costs[other],parents[other]=cost,index
                heapq.heappush(queue,(cost+math.dist(target['position'],goal),other))
        return []
