"""Use the actual 3.3.3.3 usercmd writer as the server decoder's oracle."""
import unittest

from client_reader423 import ClientReader423


class MatchInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ClientReader423()

    def test_unchanged_short_and_full_commands_match_client_writer(self):
        from reference_match.input import decode_usercmd
        cases = [({'time':5}, {'time':5}),
                 ({'time':20,'buttons':1,'forward':127,'right':-127,'pitch':65535,'yaw':16384},
                  {'time':20,'buttons':1,'direction':9,'pitch':65535,'yaw':16384}),
                 ({'time':1000,'buttons':0x220005,'weapon':1023,'offhand':2,'alt':3,'roll':32768,
                   'melee_yaw':90.,'melee_dist':255,'melee_target':2047,'location_x':31,
                   'location_y':128,'location_angle':255,'remote_x':9,'remote_y':200},
                  {'time':1000,'buttons':0x220005,'weapon':1023,'offhand':2,'alt':3,'roll':32768,
                   'melee_yaw':16384,'melee_dist':255,'melee_target':2047,'location_x':31,
                   'location_y':128,'location_angle':255,'remote_x':9,'remote_y':200})]
        for key in (0,1,0xfedcba98):
            base, previous = {}, {}
            for command, expected in cases:
                wire = self.client.usercmd(command,key=key,base=base)
                result = decode_usercmd(wire,key=key,base=previous)
                self.assertEqual({k:v for k,v in result.items() if v}, expected)
                with self.assertRaises(ValueError):
                    decode_usercmd(wire[:-1],key=key,base=previous)
                base, previous = command, result

    def test_move_message_preserves_interleaved_bits_and_trailer(self):
        from reference_match.input import decode_move
        values={'time':1000,'buttons':1,'forward':127,'weapon':7}
        wire=self.client.usercmd(values,key=55,move=True)
        commands=decode_move(wire,key=55)
        self.assertEqual(len(commands),1)
        self.assertEqual((commands[0]['time'],commands[0]['buttons'],commands[0]['weapon']),
                         (1000,1,7))
        self.assertNotEqual(commands[0]['direction'],0)
        for value in (wire[:-1],wire+b'x',wire[:1]+b'\0'+wire[2:]):
            with self.assertRaises(ValueError):
                decode_move(value,key=55)

    def test_snapshot_default_command_matches_actual_client(self):
        import struct
        from reference_match.input import default_usercmd, FIELDS
        word=lambda n:struct.unpack('<I',struct.pack('<f',n))[0]
        for state in ({},{39:7,40:9,53:4,19:word(90),18:word(-45)},
                      {54:0x1000,28:8,41:word(0.5),70:word(30),45:word(15)}):
            expected=self.client.default_usercmd(state)
            result=default_usercmd(state)
            self.assertEqual([result[k] for k in FIELDS],expected)


if __name__ == '__main__':
    unittest.main()
