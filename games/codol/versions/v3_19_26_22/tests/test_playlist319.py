import unittest
import zlib

from games.codol.versions.v3_19_26_22.server import playlist319


SOURCE = (b'playlist 110\r\nname chinese "\xba\xcb\xb5\xaf\xd0\xa1\xd5\xf2"\r\n'
          b'rule party_minplayers 1\r\nrule party_maxplayers 18\r\n'
          b'rule scr_cha_scorelimit 150\r\nmp_nuked,cha,1\r\n'
          b'playlist 190\r\nrule party_maxplayers 18\r\n')


class Playlist319Tests(unittest.TestCase):
    def test_nuketown_uses_actual_client_dvar_names_without_changing_other_rules(self):
        actual = zlib.decompress(playlist319.nuketown_rules(zlib.compress(SOURCE)))
        expected = SOURCE.replace(b'rule party_minplayers ', b'rule 1011 ', 1)
        expected = expected.replace(b'rule party_maxplayers ', b'rule 3265 ', 1)
        self.assertEqual(actual, expected)

    def test_already_adapted_and_unrelated_playlists_keep_original_bytes(self):
        adapted = playlist319.nuketown_rules(zlib.compress(SOURCE))
        self.assertEqual(playlist319.nuketown_rules(adapted), adapted)
        other = zlib.compress(b'playlist 111\nrule party_maxplayers 18\n')
        self.assertEqual(playlist319.nuketown_rules(other), other)


class NativePlaylist319Tests(unittest.TestCase):
    def test_native_room_creation_finds_both_limits_only_after_alias_translation(self):
        try:
            from client_inventory319 import InventoryReader319
            from unicorn import UC_HOOK_CODE
            from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX
            machine = InventoryReader319()
        except (ImportError, FileNotFoundError) as error:
            self.skipTest('Captured 3.19 native code unavailable: ' + str(error))
        machine.cpu.mem_map(0x7b25000, 0x5000)
        machine.cpu.mem_map(0x333a000, 0x1000)
        machine.write32(0x333abdc, machine.object)
        commands = []
        def boundary(cpu, address, size, data):
            stack = cpu.reg_read(UC_X86_REG_ESP)
            if address == 0x4f3890:
                commands.append(bytes(cpu.mem_read(machine.u32(stack + 12), 256)).split(b'\0')[0])
            cpu.reg_write(UC_X86_REG_EAX, 0)
            cpu.reg_write(UC_X86_REG_ESP, stack + 4)
            cpu.reg_write(UC_X86_REG_EIP, machine.u32(stack))
        # Only the selected playlist index and final command execution are mocked.
        # 0x761c30's real rule scanning, matching and copying execute unchanged.
        for address in (0x761740, 0x4f3890):
            machine.cpu.hook_add(UC_HOOK_CODE, boundary, begin=address, end=address)
        adapted = zlib.decompress(playlist319.nuketown_rules(zlib.compress(SOURCE)))
        for data, expected in ((SOURCE, []), (adapted, [b'1011 1', b'3265 18'])):
            rules = b'\n'.join(line[5:] for line in data.split(b'playlist 190')[0].splitlines()
                               if line.startswith(b'rule ')) + b'\n\0'
            machine.cpu.mem_write(0x7b25d00, rules)
            commands.clear()
            for name in (b'1011\0', b'3265\0'):
                machine.cpu.mem_write(machine.data, name)
                machine.call(0x761c30, 0, machine.data)
            self.assertEqual(commands, expected)
