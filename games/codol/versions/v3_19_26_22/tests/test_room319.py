import struct
import unittest
from pathlib import Path

from games.codol.versions.v3_19_26_22.server import room319


# Decrypted client packet 65 of room-baseline.pcapng; query 3, content 797, playlist 110.
SEARCH = bytes.fromhex('15030508030000000800000000083200000007abad92d6070000000007ff000000'
                       '07010000000700000000071d030000076e000000070100000007000000006b0804'
                       '000000010000000000000000')
FIXTURES = Path(__file__).resolve().parents[1] / 'server/native/match-server/tests/fixtures'
# Actual frames 340 and 356, room-admission.pcapng. The final zero ends the task buffer.
FIRST_BROADCAST = bytes.fromhex('0b03040a010090310000000013081a000000160000000202000000'
                                '30000000e068ab5bab63ab030000000000080100000000')
SESSION_SEARCH = bytes.fromhex('15030508010000000800000000080a00000007abad92d6'
                               '6b0804000000010000000000000000')
# Frame 644, room-ready-gated.pcapng: one aggregate containing native Ready 16/true.
READY_BROADCAST = bytes.fromhex('0b03040a01009031000000001308100000000c000000'
                               '020200000008000000800800080100000000')


def channel_message(channel, payload):
    wrapped = struct.pack('<I', len(payload)) + payload
    return (b'\x0b\x03\x04\x0a' + struct.pack('<Q', channel) + b'\x13\x08'
            + struct.pack('<I', len(wrapped)) + wrapped + b'\x08\x01\0\0\0\0')


class Room319Tests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def manifest(roster=None):
            self.calls.append(roster)
            return {'players': [{'uid': 1000001, 'name': 'Player', 'team': 1, 'slot': 0}]
                    + [{'uid': 0x600000000 + slot, 'name': f'Bot{slot:02}', 'team': 1 if slot < 9 else 2,
                        'slot': slot, 'join': list((FIXTURES / 'join-native.bin').read_bytes())}
                       for slot in range(1, 18)]}
        self.room = room319.Room(1000001, manifest)

    def enter(self):
        self.room.handle(SEARCH, 1)
        response, pushes = self.room.handle(b'\x0b\x03\x0d', 2)
        self.assertFalse(pushes)  # The client has not run the create-channel callback yet.
        self.assertEqual(response[16:26], b'\x08\x01\0\0\0' * 2)
        return self.room.channel

    def test_members_are_announced_before_requesting_the_real_host_roster(self):
        channel = self.enter()
        response, pushes = self.room.handle(channel_message(channel, b'\x2e\x06\0\0\0\0\0\0\0\0'), 3)
        self.assertIsNone(response)
        self.assertEqual([struct.unpack_from('<I', p, 1)[0] for p in pushes], [9] * 17 + [7])
        self.assertEqual(self.calls, [None])
        self.assertEqual(self.room.handle(channel_message(channel, b'\x22\0'), 4)[1], [])

    def test_bot_joins_wait_for_host_state_and_are_not_repeated(self):
        channel = self.enter()
        self.room.handle(channel_message(channel, b'\x2e\x06'), 3)
        roster = (FIXTURES / 'roster-native.bin').read_bytes()
        _, pushes = self.room.handle(channel_message(channel, roster), 4)
        self.assertEqual(len(pushes), 18)  # 17 native joins, then query the resulting roster.
        self.assertEqual(self.calls, [None, roster])
        self.assertEqual(self.room.handle(channel_message(channel, roster), 5)[1], [])
        self.assertEqual(self.room.observed_count, 18)

    def test_other_playlist_wrong_channel_and_truncated_messages_do_not_inject_bots(self):
        self.assertEqual(self.room.handle(b'\x0b\x03\x0d', 1), (None, []))
        channel = self.enter()
        self.assertEqual(self.room.handle(channel_message(channel + 1, b'\x1c\0'), 3)[1], [])
        for invalid in (b'\x0b\x03\x04', channel_message(channel, b'\x02')[:-5]):
            self.assertEqual(self.room.handle(invalid, 4)[1], [])
        other = bytearray(SEARCH)
        struct.pack_into('<I', other, 49, 190)
        self.room.handle(bytes(other), 5)
        self.assertEqual(self.room.handle(b'\x0b\x03\x0d', 6), (None, []))

    def test_real_client_task_terminator_is_accepted(self):
        self.enter()
        _, pushes = self.room.handle(FIRST_BROADCAST, 3)
        self.assertEqual(len(pushes), 18)
        self.assertEqual(self.room.phase, 'host_requested')

    def test_session_refresh_does_not_discard_the_selected_room(self):
        channel = self.enter()
        self.room.handle(SESSION_SEARCH, 3)
        self.assertEqual(self.room.channel, channel)
        self.assertEqual(self.room.phase, 'created')

    def test_ready_and_cancel_are_returned_with_the_human_sender(self):
        channel = self.enter()
        self.room.handle(FIRST_BROADCAST, 3)
        self.room.handle(channel_message(channel, (FIXTURES / 'roster-native.bin').read_bytes()), 4)
        for request, payload in ((READY_BROADCAST, b'\x20\x02'),
                                 (channel_message(channel, b'\x20\0'), b'\x20\0')):
            _, pushes = self.room.handle(request, 5)
            self.assertEqual(pushes, [room319.message_event(channel, self.room.players[0], payload)])
        for payload in (b'\x20', b'\x20\x04', b'\x20\x02\0', b'\x22\0'):
            self.assertEqual(self.room.handle(channel_message(channel, payload), 6)[1], [])
        self.assertEqual(self.room.handle(channel_message(channel + 1, b'\x20\x02'), 7)[1], [])

    def test_match_request_waits_for_roster_confirmation_and_human_ready(self):
        self.enter()
        self.room.handle(FIRST_BROADCAST, 3)
        roster = (FIXTURES / 'roster-native.bin').read_bytes()
        self.room.handle(channel_message(self.room.channel, roster), 4)
        self.room.handle(READY_BROADCAST, 5)
        self.assertIsNone(self.room.match_request())
        self.room.handle(channel_message(self.room.channel, roster), 6)
        request = self.room.match_request()
        self.assertEqual(request, {'uid': 1000001, 'name': 'Player', 'roster': list(roster)})
        self.room.handle(channel_message(self.room.channel, b'\x20\0'), 7)
        self.assertIsNone(self.room.match_request())
        self.room.handle(READY_BROADCAST, 8)
        self.assertEqual(self.room.match_request(), request)
        other = bytearray(SEARCH)
        struct.pack_into('<I', other, 49, 190)
        self.room.handle(bytes(other), 9)
        self.assertIsNone(self.room.match_request())


class NativeRoomPush319Tests(unittest.TestCase):
    def test_native_ready_message_updates_only_its_sender(self):
        from client_inventory319 import InventoryReader319
        from unicorn import UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX
        m = InventoryReader319()
        cpu, room, buffer, vtable = m.cpu, m.object, 0x20070000, 0x20050000
        cpu.mem_map(0x82e1000, 0x1000)
        m.write32(room, vtable)
        m.write32(room + 0x1c, 0x20060000)
        m.write32(room + 0x105d8, 18)
        for slot in range(18):
            cpu.mem_write(room + 0xe368 + slot * 0x1d0,
                          struct.pack('<Q', 1000001 if slot == 0 else 0x600000000 + slot))
        m.write32(vtable + 0x60, 0xf00200)
        def hook(cpu, address, size, _):
            # Room availability and downstream notifications; native parsing and
            # member lookup/write in 0x634870/0x629090 execute without replacements.
            sp = cpu.reg_read(UC_X86_REG_ESP)
            cpu.reg_write(UC_X86_REG_EAX, int(address == 0xf00200))
            cpu.reg_write(UC_X86_REG_ESP, sp + (8 if address == 0x632d00 else 4))
            cpu.reg_write(UC_X86_REG_EIP, m.u32(sp))
        for address in (0xf00200, 0x632d00, 0x632a70):
            cpu.hook_add(UC_HOOK_CODE, hook, begin=address, end=address)
        for ready in (1, 0):
            cpu.mem_write(m.data, bytes([0x20, ready * 2]))
            m.call(0xb779a0, buffer, m.data, 16, 1)
            m.write32(buffer + 4, 100)
            m.call(0x634870, 0, room, 0, 0, 1000001, 0, buffer)
            self.assertEqual([cpu.mem_read(room + 0xe3f8 + i * 0x1d0, 1)[0]
                              for i in range(18)], [ready] + [0] * 17)

    def test_native_channel_decoders_receive_owner_name_and_room_payload(self):
        try:
            from client_inventory319 import InventoryReader319
            from unicorn import UC_HOOK_CODE
            from unicorn.x86_const import (UC_X86_REG_ESP, UC_X86_REG_EIP,
                                           UC_X86_REG_ESI, UC_X86_REG_EDI)
            machine = InventoryReader319()
        except (ImportError, FileNotFoundError) as error:
            self.skipTest('Captured 3.19 native code unavailable: ' + str(error))
        machine.cpu.mem_map(0x1539f000, 0x1000)
        machine.cpu.mem_map(0x153a1000, 0x1000)
        machine.write32(0x1539fe2c, 0xf00000)
        machine.write32(0x153a13d4, 0xf00010)
        machine.write32(machine.object + 0x4f0, 0x20008000)
        machine.write32(0x20008000, 0x20009000)
        machine.write32(0x20009010, 0xf00200)
        machine.write32(0x20009018, 0xf00210)
        callbacks = []
        def callback(cpu, address, size, data):
            sp = cpu.reg_read(UC_X86_REG_ESP)
            arg = lambda n: machine.u32(sp + n * 4)
            if address == 0xf00200:
                channel, member = arg(1), arg(2)
                callbacks.append((machine.u32(channel + 8), machine.u32(channel + 0x18),
                                  bytes(cpu.mem_read(member + 8, 8)),
                                  bytes(cpu.mem_read(member + 0x10, 64)).split(b'\0')[0], arg(3)))
                pop = 12
            else:
                callbacks.append((arg(1), arg(3), arg(4),
                                  bytes(cpu.mem_read(arg(5), 64)).split(b'\0')[0], arg(6),
                                  bytes(cpu.mem_read(arg(7), arg(8)))))
                pop = 32
            cpu.reg_write(UC_X86_REG_ESP, sp + 4 + pop)
            cpu.reg_write(UC_X86_REG_EIP, machine.u32(sp))
        for address in (0xf00200, 0xf00210):
            machine.cpu.hook_add(UC_HOOK_CODE, callback, begin=address, end=address)
        bot = {'uid': 0x600000001, 'name': 'Bot01'}
        payload = (FIXTURES / 'join-native.bin').read_bytes()
        pushes = [(room319.member_event(9, 91, 1000001, bot, 2), 0xb7b4b0, (9,)),
                  (room319.message_event(91, bot, payload), 0xb7b300, ())]
        for push, address, args in pushes:
            data = push[5:]  # The parent dispatch already read the typed event ID.
            machine.cpu.mem_write(machine.data, data)
            machine.cpu.mem_write(machine.buffer, struct.pack('<6I', 0xdb7154, 100, len(data),
                machine.data, machine.data, machine.data + len(data)) + b'\1\0\0\0')
            machine.call(address, machine.object, machine.buffer, *args)
        def client_name(wire_name):
            # 0x7e7a50 consumes the event member through this native decoder.
            machine.cpu.mem_write(machine.data, wire_name + b'\0')
            machine.cpu.reg_write(UC_X86_REG_ESI, machine.data)
            machine.cpu.reg_write(UC_X86_REG_EDI, machine.buffer)
            self.assertEqual(machine.call(0x7f3440, 0), 1)
            return bytes(machine.cpu.mem_read(machine.buffer, 64)).split(b'\0')[0]
        member, message = callbacks
        self.assertEqual((*member[:3], client_name(member[3]), member[4]),
                         (91, 1000001, struct.pack('<Q', bot['uid']), b'Bot01', 1))
        self.assertEqual((*message[:3], client_name(message[3]), *message[4:]),
                         (91, 1, 6, b'Bot01', 1, struct.pack('<I', len(payload)) + payload))
        # Real namesTable.csv row 0, UTF-8 bytes captured from the current client.
        self.assertEqual(client_name(room319.text('AK47宝贝')[1:-1]),
                         bytes.fromhex('414b3437e5ae9de8b49d'))
