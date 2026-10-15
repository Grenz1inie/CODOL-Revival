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
    def test_reference_node_heights_follow_current_ground_and_reject_blocked_nodes(self):
        from match_server.navigation import Navigation
        text='3\n0 0 -.5,1,stand,,,\n200 0 -.25,0,stand,,,\n400 0 0,1,stand,,,\n'
        navigation=Navigation.from_csv(text,room(((390,-20,0),(410,20,100))))
        self.assertEqual(navigation.nodes[0]['position'],[0,0,.125])
        self.assertEqual(navigation.nodes[1]['position'],[200,0,.125])
        self.assertFalse(navigation.nodes[2]['standing'])
        self.assertTrue(navigation.route([0,0,0],[200,0,0]))

    def test_replanning_does_not_send_bot_back_to_a_passed_waypoint(self):
        from match_server.navigation import Navigation
        geometry=room(((80,-100,0),(90,100,200)))
        path=Navigation.from_csv(CSV,geometry).route([150,160,.125],[0,0,0])
        self.assertTrue(path)
        self.assertLess(path[0][0],150)

    def test_route_uses_movement_step_height_without_crossing_walls_or_low_ceilings(self):
        from match_server.navigation import Navigation
        start,end=[0,0,0],[200,0,0]
        curb=((80,-100,0),(90,100,12))
        navigation=Navigation([],room(curb))
        self.assertEqual(navigation.route(start,end),[end])
        for geometry in (room(((80,-100,0),(90,100,19))),
                         room(curb,((-100,-100,80),(300,100,90))),
                         room(((-10,-10,0),(10,10,20)))):
            self.assertEqual(Navigation([],geometry).route(start,end),[])

    def test_reference_waypoints_are_only_links_after_current_collision_validation(self):
        from match_server.navigation import Navigation
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
        from match_server.navigation import Navigation
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
