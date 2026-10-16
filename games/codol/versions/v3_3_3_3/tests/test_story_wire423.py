"""Wire compatibility is checked by the current client, not a mirror decoder."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
from games.codol.versions.v3_3_3_3.server.story_wire423 import encode_configstrings, encode_gamestate
from games.codol.versions.v3_3_3_3.server import story_wire423
from client_reader423 import ClientReader423


class Configstrings423Tests(unittest.TestCase):
    def setUp(self):
        self.client = ClientReader423()

    def test_interleaved_bit_and_byte_fields_reach_current_client(self):
        # One short count, next-index bit, a NUL string, two 10-bit counts, EOF.
        wire = encode_configstrings([(0, 'x')])
        self.assertEqual(wire, bytes.fromhex('0100017800000006'))
        self.assertEqual(self.client.configstrings(wire), ({0: 'x'}, b'\x06'))

    def test_current_ten_bit_alias_count_does_not_shift_following_fields(self):
        wire = encode_configstrings([(0, 'first'), (344, 'value')],
                                    aliases=[(5444, 1), (5445, 1023)])
        self.assertEqual(self.client.configstrings(wire),
                         ({0: 'first', 344: 'value', 5444: '* 1', 5445: '* 1023'}, b'\x06'))

    def test_current_recipe_fields_include_optional_nine_bit_value(self):
        # 0x46da00: weapon 10, camo 8, optional 9, count 4, attachments 14.
        recipes = [(5446, 1023, 255, 511, [0, 16383]), (5447, 1, 0, 0, [])]
        wire = encode_configstrings([], aliases=[(5444, 1)], recipes=recipes)
        self.assertEqual(self.client.configstrings(wire),
                         ({5444: '* 1', 5446: '** 1023 255 511 0 16383',
                           5447: '** 1 0 0'}, b'\x06'))

    def test_recipe_fields_and_attachment_count_do_not_wrap(self):
        invalid = [(5444, 1024, 0, 0, []), (5444, -1, 0, 0, []),
                   (5444, 1, 256, 0, []), (5444, 1, -1, 0, []),
                   (5444, 1, 0, 512, []), (5444, 1, 0, -1, []),
                   (5444, 1, 0, 0, [16384]), (5444, 1, 0, 0, [-1]),
                   (5444, 1, 0, 0, [1] * 16)]
        for recipe in invalid:
            with self.subTest(recipe=recipe), self.assertRaises(ValueError):
                encode_configstrings([], recipes=[recipe])
        with self.assertRaisesRegex(ValueError, 'count'):
            encode_configstrings([], recipes=[(5444, 1, 0, 0, [])] * 1024)
        wire = encode_configstrings([], recipes=[(5444, 1, 0, 0, [1] * 15)])
        self.assertEqual(self.client.configstrings(wire), ({5444: '** 1 0 0' + ' 1' * 15}, b'\x06'))

    def test_invalid_rows_cannot_be_truncated_or_overwrite_registered_resources(self):
        cases = [([(7058, 'x')], {}, 'index'), ([(-1, 'x')], {}, 'index'),
                 ([(2052, 'model')], {}, 'registered'), ([(343, 'name')], {}, 'registered'),
                 ([(0, 'x'), (0, 'y')], {}, 'duplicate'),
                 ([(0, 'x')], {'aliases': [(0, 1)]}, 'duplicate'),
                 ([], {'aliases': [(5444, 1024)]}, 'weapon'),
                 ([], {'aliases': [(5444, -1)]}, 'weapon'),
                 ([], {'aliases': [(5444, 0)] * 1024}, 'count'),
                 ([(0, 'a\0b')], {}, 'string'), ([(0, '100%')], {}, 'string')]
        for ordinary, extra, message in cases:
            with self.subTest(message=message, ordinary=ordinary[:2]):
                with self.assertRaisesRegex(ValueError, message):
                    encode_configstrings(ordinary, **extra)
        wire = encode_configstrings([(344, 'runtime value'), (7057, 'last')])
        self.assertEqual(self.client.configstrings(wire),
                         ({344: 'runtime value', 7057: 'last'}, b'\x06'))

    def test_string_and_shared_pool_limits_prevent_client_truncation(self):
        text = 'a' * 8191
        self.assertEqual(self.client.configstrings(encode_configstrings([(0, text)])),
                         ({0: text}, b'\x06'))
        with self.assertRaisesRegex(ValueError, 'string'):
            encode_configstrings([(0, text + 'a')])
        with self.assertRaisesRegex(ValueError, 'pool'):
            encode_configstrings([(i, text) for i in range(16)])

    def test_gamestate_reaches_loading_screen_context_with_matching_crc(self):
        wire = encode_gamestate('mp_cargoship', 'coop', 0xc6280541,
                                command_sequence=7, client_number=0, checksum_feed=123,
                                ordinary=[(0, r'\mapname\mp_cargoship\g_gametype\coop')])
        self.assertEqual(wire[0], 3)
        result = self.client.gamestate(wire, checksum=0xc6280541)
        self.assertEqual(result, {'map': 'mp_cargoship', 'game_type': 'coop',
                                 'command_sequence': 7, 'client_number': 0,
                                 'checksum_feed': 123, 'remaining': b'\x06'})

    def test_packet_reaches_current_netchan_and_decryptor(self):
        # Sequence and acknowledgement stay clear; only message bytes use XOR.
        packets = story_wire423.encode_packets(b'\x06', sequence=1,
                                               acknowledgement=0, challenge=0x42)
        self.assertEqual(packets, [bytes.fromhex('010000000000000045')])
        self.client.reset_netchan()
        self.assertEqual(self.client.packet(packets[0], challenge=0x42),
                         (1, 0, b'\x06'))
        self.assertIsNone(self.client.packet(packets[0], challenge=0x42))

    def test_next_packet_remains_readable_after_snapshot(self):
        self.client.reset_netchan()
        for sequence in (1, 2):
            wire = story_wire423.encode_snapshot({0: sequence*1000},
                                                  server_time=sequence*1000)
            packet, = story_wire423.encode_packets(wire, sequence=sequence,
                                                   acknowledgement=0, challenge=0x42)
            number, _, body = self.client.packet(packet, challenge=0x42)
            result = self.client.snapshot(body, sequence=number)
            self.assertEqual(result['command_time'], sequence*1000)
            self.assertEqual(result['remaining'], b'\x06')

    def test_fragment_boundaries_and_out_of_order_duplicate_reassembly(self):
        for size in (1149, 1150, 2304, 2305, 0x20000 - 8):
            with self.subTest(size=size):
                payload = (bytes(range(256)) * (size // 256 + 1))[:size]
                packets = story_wire423.encode_packets(payload, sequence=0x1fffffff,
                    acknowledgement=0x7fffffff, challenge=0x89abcdef, command=b'userinfo test')
                self.assertEqual(len(packets), (size + 4 + 1153) // 1154)
                self.assertLessEqual(max(map(len, packets)), 1164)
                self.client.reset_netchan()
                if len(packets) > 1:
                    # Last arrives first and repeats before the missing parts.
                    self.assertIsNone(self.client.packet(packets[-1], challenge=0x89abcdef))
                    self.assertIsNone(self.client.packet(packets[-1], challenge=0x89abcdef))
                    order = list(reversed(packets[:-1]))
                else:
                    order = packets
                for packet in order[:-1]:
                    self.assertIsNone(self.client.packet(packet, challenge=0x89abcdef))
                self.assertEqual(self.client.packet(order[-1], challenge=0x89abcdef,
                                                     command=b'userinfo test'),
                                 (0x1fffffff, 0x7fffffff, payload))

    def test_packet_bounds_do_not_wrap_sequence_flags_or_client_buffers(self):
        args = dict(sequence=1, acknowledgement=0, challenge=0)
        for field, value in (('sequence', 0), ('sequence', 0x20000000),
                             ('acknowledgement', -1), ('acknowledgement', 0x80000000),
                             ('challenge', -1), ('challenge', 0x100000000),
                             ('command', b'x\0y'), ('command', b'x' * 1024)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                story_wire423.encode_packets(b'\x06', **(args | {field: value}))
        for payload in (b'', bytes(0x20000 - 7)):
            with self.assertRaisesRegex(ValueError, 'buffer'):
                story_wire423.encode_packets(payload, **args)

    def test_playerstate_uses_current_235_field_table_and_reader(self):
        self.assertEqual([tuple(f) for f in story_wire423.PLAYER_FIELDS], self.client.player_fields)
        wire = story_wire423.encode_playerstate({}, server_time=1000)
        values, remaining = self.client.playerstate(wire, server_time=1000)
        self.assertEqual(len(values), 235)
        self.assertEqual(values, [0] * 235)
        self.assertEqual(remaining, b'\x06')

    def test_playerstate_delta_preserves_position_time_and_signed_words(self):
        word = lambda f: struct.unpack('<I', struct.pack('<f', f))[0]
        values = {0: 1000, 1: 8, 3: 0xffff8000, 8: word(124.5),
                  10: word(-46.25), 11: word(333.75), 20: 0xfedcba98}
        wire = story_wire423.encode_playerstate(values, server_time=1000)
        result, remaining = self.client.playerstate(wire, server_time=1000)
        for index, value in values.items():
            self.assertEqual(result[index], value, index)
        changed = values | {0: 1050, 1: 13, 8: word(125.5), 20: 0}
        wire = story_wire423.encode_playerstate(changed, base=values, server_time=1050)
        result, remaining = self.client.playerstate(wire, base=values, server_time=1050)
        for index, value in changed.items():
            self.assertEqual(result[index], value, index)
        self.assertEqual(remaining, b'\x06')

    def test_playerstate_rejects_truncation_and_unsupported_changed_fields(self):
        wire = story_wire423.encode_playerstate({0: 1000}, server_time=1000)
        with self.assertRaises(ValueError):
            self.client.playerstate(wire[:8], server_time=1000)
        for values in ({235: 0}, {-1: 0}, {7: 2048}, {3: 32768},
                       {0: 0x100000000}, {0: -1}, {21: 162}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                story_wire423.encode_playerstate(values, server_time=1000)

    def test_initial_snapshot_reaches_current_baseline_store(self):
        wire = story_wire423.encode_snapshot({0: 1000}, server_time=1000)
        result = self.client.snapshot(wire, sequence=1)
        self.assertEqual(result, {'server_time': 1000, 'sequence': 1,
                                 'flags': 8, 'command_time': 1000,
                                 'entities': 0, 'clients': 0, 'actors': 0,
                                 'remaining': b'\x06'})
        with self.assertRaises(ValueError):
            self.client.snapshot(wire[:-4], sequence=2)

    def test_late_player_fields_keep_deferred_bits_and_protected_byte_aligned(self):
        values = {82: 63, 89: 1, 93: 1, 98: 1, 101: 1, 104: 65535, 106: 1, 122: 1,
                  234: (1 << story_wire423.PLAYER_FIELDS[234][1]) - 1}
        wire = story_wire423.encode_playerstate(values, server_time=2000)
        result, tail = self.client.playerstate(wire, server_time=2000)
        for index, value in values.items():
            self.assertEqual(result[index], value, index)
        self.assertEqual(tail, b'\x06')
        reset = {234: 1}
        wire = story_wire423.encode_playerstate(reset, base=values, server_time=2050)
        result, tail = self.client.playerstate(wire, base=values, server_time=2050)
        for index in values:
            self.assertEqual(result[index], reset.get(index, 0), index)
        self.assertEqual(tail, b'\x06')

    def test_gamestate_crc_truncation_and_current_player_limit(self):
        args = dict(command_sequence=0, client_number=18, checksum_feed=0xffffffff,
                    ordinary=[(0, r'\mapname\mp_cargoship\g_gametype\coop')])
        wire = encode_gamestate('mp_cargoship', 'coop', 123, **args)
        self.assertEqual(self.client.gamestate(wire, checksum=123)['client_number'], 18)
        for bad_wire, crc in ((wire, 124), (wire[:-3], 123), (wire[:10], 123)):
            with self.subTest(crc=crc, length=len(bad_wire)), self.assertRaises(ValueError):
                self.client.gamestate(bad_wire, checksum=crc)
        for field, value in (('client_number', 19), ('client_number', -1),
                             ('command_sequence', -1), ('checksum_feed', 0x100000000)):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                encode_gamestate('mp_cargoship', 'coop', 123, **(args | {field: value}))
        for name in ('', 'a' * 32, 'a\0b'):
            with self.subTest(map=name), self.assertRaises(ValueError):
                encode_gamestate(name, 'coop', 123, **args)

    def test_gamestate_header_counts_toward_outer_message_limit(self):
        rows = [(i, 'a' * 8190) for i in range(16)]
        self.assertLessEqual(len(encode_configstrings(rows)), 0x20000)
        with self.assertRaisesRegex(ValueError, 'message'):
            encode_gamestate('mp_cargoship', 'coop', 123, command_sequence=0,
                             client_number=0, checksum_feed=0, ordinary=rows)


if __name__ == '__main__':
    unittest.main()
