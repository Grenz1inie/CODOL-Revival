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
            # Standing locomotion cannot use links requiring crouch or ladders.
            nodes.append(dict(position=position,links=links,standing=row[2] in ('stand','grenade','claymore','javelin')))
        return cls(nodes,collision)

    def _clear(self, a, b):
        trace=self.collision.trace_box(a,b)
        return trace['fraction'] >= 1 and not trace['start_solid'] and not trace.get('unresolved_static_models')

    def _nearest(self, position):
        order=sorted(range(len(self.nodes)),key=lambda i:math.dist(position,self.nodes[i]['position']))
        return next((i for i in order if self.nodes[i]['standing']
                     and self._clear(position,self.nodes[i]['position'])),None)

    def route(self, start, goal):
        if self._clear(start,goal):
            return [list(goal)]
        first,last=self._nearest(start),self._nearest(goal)
        if first is None or last is None:
            return []
        costs,parents,queue={first:0},{first:None},[(0,first)]
        while queue:
            _,index=heapq.heappop(queue)
            if index==last:
                path=[list(goal)]
                while index is not None:
                    path.append(self.nodes[index]['position'])
                    index=parents[index]
                return path[::-1]
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
