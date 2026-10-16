import unittest

from test_match_world import room
import test_match_world as fixture


CSV='''4
200 0 .125,1 3,stand,,,
200 160 .125,0 2,stand,,,
0 160 .125,1 3,stand,,,
0 0 .125,0 2,stand,,,
'''


class MatchNavigationTests(unittest.TestCase):
    def test_long_route_uses_graph_instead_of_map_wide_collision_sweeps(self):
        import math
        from reference_match.navigation import Navigation
        geometry=room(((350,-100,0),(360,100,200)))
        trace_box=geometry.trace_box
        distances=[]
        def measured_trace(start,end,*args,**kwargs):
            distances.append(math.dist(start,end))
            return trace_box(start,end,*args,**kwargs)
        geometry.trace_box=measured_trace
        positions=[[0,0,0],[0,160,0],[200,160,0],[400,160,0],
                   [600,160,0],[800,160,0],[800,0,0]]
        nodes=[dict(position=position,standing=True,
                    links=[j for j in (i-1,i+1) if 0<=j<len(positions)])
               for i,position in enumerate(positions)]
        path=Navigation(nodes,geometry).route(positions[0],positions[-1])
        self.assertTrue(path)
        self.assertEqual(path[-1],positions[-1])
        self.assertLessEqual(max(distances),256)
        for a,b in zip([positions[0],*path],path):
            self.assertEqual(trace_box(a,b)['fraction'],1)

    def test_unreachable_endpoint_does_not_probe_distant_waypoints(self):
        from reference_match.navigation import Navigation
        geometry=room(((80,-1000,0),(90,1000,200)))
        trace_box=geometry.trace_box
        queries=[]
        def measured_trace(*args,**kwargs):
            queries.append(args)
            return trace_box(*args,**kwargs)
        geometry.trace_box=measured_trace
        start,end=[0,0,0],[200,0,0]
        self.assertEqual(Navigation([],geometry).route(start,end),[])
        baseline=len(queries)
        queries.clear()
        # Reference nearest_reachable only attaches within 256 units. Unrelated
        # map nodes must not turn one failed attachment into map-wide sweeps.
        nodes=[dict(position=[600+i*10,0,.125],standing=True,links=[]) for i in range(40)]
        self.assertEqual(Navigation(nodes,geometry).route(start,end),[])
        self.assertLessEqual(len(queries),baseline)

    def test_reference_node_heights_follow_current_ground_and_reject_blocked_nodes(self):
        from reference_match.navigation import Navigation
        text='3\n0 0 -.5,1,stand,,,\n200 0 -.25,0,stand,,,\n400 0 0,1,stand,,,\n'
        navigation=Navigation.from_csv(text,room(((390,-20,0),(410,20,100))))
        self.assertEqual(navigation.nodes[0]['position'],[0,0,.125])
        self.assertEqual(navigation.nodes[1]['position'],[200,0,.125])
        self.assertFalse(navigation.nodes[2]['standing'])
        self.assertTrue(navigation.route([0,0,0],[200,0,0]))

    def test_replanning_does_not_send_bot_back_to_a_passed_waypoint(self):
        from reference_match.navigation import Navigation
        geometry=room(((80,-100,0),(90,100,200)))
        path=Navigation.from_csv(CSV,geometry).route([150,160,.125],[0,0,0])
        self.assertTrue(path)
        self.assertLess(path[0][0],150)

    def test_route_uses_movement_step_height_without_crossing_walls_or_low_ceilings(self):
        from reference_match.navigation import Navigation
        start,end=[0,0,0],[200,0,0]
        curb=((80,-100,0),(90,100,12))
        navigation=Navigation([],room(curb))
        self.assertEqual(navigation.route(start,end),[end])
        for geometry in (room(((80,-100,0),(90,100,19))),
                         room(curb,((-100,-100,80),(300,100,90))),
                         room(((-10,-10,0),(10,10,20)))):
            self.assertEqual(Navigation([],geometry).route(start,end),[])

    def test_reference_waypoints_are_only_links_after_current_collision_validation(self):
        from reference_match.navigation import Navigation
        geometry=room(((80,-100,0),(90,100,200)))
        navigation=Navigation.from_csv(CSV,geometry)
        path=navigation.route([200,0,0],[0,0,0])
        self.assertTrue(path)
        self.assertGreater(max(p[1] for p in path),100)
        # Claimed direct adjacency in the CSV must not tunnel through a wall.
        for a,b in zip([[200,0,0],*path],path):
            self.assertEqual(geometry.trace_box(a,b)['fraction'],1)
        for text in (CSV.replace('4\n','5\n',1),CSV.replace('1 3','1 99'),
                     CSV.replace('200 0 .125','nan 0 0')):
            with self.assertRaises(ValueError):
                Navigation.from_csv(text,geometry)

    def test_ai_routes_around_cover_before_shooting(self):
        from reference_match.navigation import Navigation
        geometry=room(((80,-100,0),(90,100,200)))
        world=fixture.MatchWorldTests().world(geometry=geometry,bot=True)
        world.navigation=Navigation.from_csv(CSV,geometry)
        positions=[]
        for _ in range(240):
            world.step(milliseconds=50)
            positions.append(world.players[1].origin[:])
            if world.players[0].health < 100:
                break
        self.assertGreater(max(p[1] for p in positions),100)
        self.assertLess(world.players[0].health,100)
        self.assertLess(world.players[1].clip,36)


if __name__ == '__main__':
    unittest.main()
