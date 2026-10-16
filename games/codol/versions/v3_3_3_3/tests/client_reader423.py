"""Execute the shipped client's configstring reader without starting the game."""
import hashlib
from pathlib import Path
import struct
import sys

import pefile

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'research/experiments/story-native/python-libs'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_ECX, UC_X86_REG_EDI, UC_X86_REG_EAX, UC_X86_REG_ESI,
                               UC_X86_REG_ESP, UC_X86_REG_EBP, UC_X86_REG_EIP)


class ClientReader423:
    """No socket, file, renderer, or Windows API executes in this emulator."""
    def __init__(self):
        path = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != 'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b':
            raise ValueError('client hash mismatch')
        pe = pefile.PE(data=data, fast_load=True)
        self.player_fields = list(struct.iter_unpack('<iii', pe.get_data(
            0xc55f70 - pe.OPTIONAL_HEADER.ImageBase, 235 * 12)))
        self.event_widths = list(struct.unpack('<162I', pe.get_data(
            0xc56d70-pe.OPTIONAL_HEADER.ImageBase, 162*4)))
        self.entity_fields = [list(struct.iter_unpack('<iii', pe.get_data(
            pointer-pe.OPTIONAL_HEADER.ImageBase, count*12))) for pointer,count in
            struct.iter_unpack('<II',pe.get_data(0xc56cb8-pe.OPTIONAL_HEADER.ImageBase,23*8))]
        self.kinds = bytearray([255]) * 7058
        layout = pe.get_data(0xc57118 - pe.OPTIONAL_HEADER.ImageBase, 21 * 12)
        for kind, (start, capacity, reserved) in enumerate(struct.iter_unpack('<3I', layout)):
            self.kinds[start:start + capacity] = bytes([kind]) * capacity
        self.cpu = Uc(UC_ARCH_X86, UC_MODE_32)
        base = pe.OPTIONAL_HEADER.ImageBase
        self.cpu.mem_map(base, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
        self.cpu.mem_write(base, data[:pe.OPTIONAL_HEADER.SizeOfHeaders])
        for section in pe.sections:
            self.cpu.mem_write(base + section.VirtualAddress, section.get_data())
        self.cpu.mem_map(0x30000000, 0x400000)
        self.cpu.hook_add(UC_HOOK_CODE, self._error, begin=0x597d20, end=0x597d20)
        self.cpu.hook_add(UC_HOOK_CODE, self._format, begin=0x637c20, end=0x637c20)
        # UI notification, disconnect/reset, empty spawn-origin sscanf, and
        # post-parse setup are outside this wire seam. No reader/CRC is replaced.
        for address in (0x637c60, 0x5a6510, 0x464420, 0x59e700, 0xaf8ca9,
                        0x46de40, 0x49f930, 0x46d830, 0x46d860):
            self.cpu.hook_add(UC_HOOK_CODE, self._return, begin=address, end=address)
        # Keep imported-call stubs outside the scratch stack used by snapshots.
        self.cpu.mem_map(0x31000000, 0x1000)
        self.cpu.mem_write(0x31000000, b'\x31\xc0\xc3')  # Return 0 for clock/thread ID.
        for address in (0xb5b468, 0xb5b194):
            self.cpu.mem_write(address, struct.pack('<I', 0x31000000))
        self.error = False

    def weapon_fire_timing(self, *, fire, delay, hold, grenade=False, hand=0):
        """Execute 0x4253e0; isolate only the animation-event notification."""
        cpu = self.cpu
        player, weapon, stack, end = 0x30001000, 0x30010000, 0x303ff000, 0x303ffff0
        cpu.mem_write(player, bytes(0x3524))
        cpu.mem_write(weapon, bytes(0xe28))
        cpu.mem_write(0x17f5a44, struct.pack('<I', weapon))
        cpu.mem_write(player+0x340, struct.pack('<I', 1))
        cpu.mem_write(player+0x3e0+4*hand, struct.pack('<I', 1))
        for offset, value in ((0x47c, int(grenade)), (0xd10, fire), (0x6f0, delay), (0x70c, hold)):
            cpu.mem_write(weapon+offset, struct.pack('<I', value))
        hook = cpu.hook_add(UC_HOOK_CODE, self._return, begin=0x4096d0, end=0x4096d0)
        try:
            cpu.mem_write(stack, struct.pack('<5I', end, player, 0, 0, hand))
            cpu.reg_write(UC_X86_REG_ESP, stack)
            cpu.emu_start(0x4253e0, end, count=10000)
            if cpu.reg_read(UC_X86_REG_EIP) != end:
                raise ValueError('client weapon fire phase did not finish')
            return struct.unpack('<2I', cpu.mem_read(player+0x270+hand*0x1c, 8))
        finally:
            cpu.hook_del(hook)

    def weapon_keys(self, rows):
        """Execute stock ammo/clip registrars 0x42bfa0 and 0x42c1b0."""
        cpu=self.cpu
        stack,end=0x303ff000,0x303ffff0
        strings=0x303a0000
        for i,(name,ammo,clip,flags,no_clip) in enumerate(rows):
            source=0x30010000+0x1000*i
            cpu.mem_write(source,bytes(0xe28))
            cpu.mem_write(0x17f5a40+4*i,struct.pack('<I',source))
            for offset,value in ((0,name),(0x6b4,ammo),(0x6bc,clip)):
                text=value.encode()+b'\0'
                cpu.mem_write(strings,text)
                cpu.mem_write(source+offset,struct.pack('<I',strings))
                strings+=len(text)
            for offset,value in ((0xd68,flags&1),(0xd69,bool(flags&2)),
                                 (0xd6a,bool(flags&4)),(0xdad,bool(flags&8)),(0x6b0,no_clip)):
                cpu.mem_write(source+offset,bytes([value]))
        result=[]
        self.error=False
        for i in range(len(rows)):
            source=0x30010000+0x1000*i
            if i:  # Slot zero is initialized by the client's reset routine.
                for address in (0x42bfa0,0x42c1b0):
                    cpu.mem_write(stack,struct.pack('<II',end,i))
                    cpu.reg_write(UC_X86_REG_ESP,stack)
                    cpu.emu_start(address,end,count=200000)
                    if self.error or cpu.reg_read(UC_X86_REG_EIP)!=end:
                        raise ValueError('client weapon registrar did not finish')
            result.append((struct.unpack('<i',cpu.mem_read(source+0x6b8,4))[0],
                           struct.unpack('<i',cpu.mem_read(source+0x6c0,4))[0]))
        return result

    def weapon_registry(self, rows):
        """Run the current recursive registrar; replace only asset lookup."""
        cpu=self.cpu;stack,end=0x303ff000,0x303ffff0;strings=0x303a0000
        pointers={row[0]:0x30010000+i*0x1000 for i,row in enumerate(rows)}
        for name,ammo,clip,flags,noclip,shared,capacity,alt,companion in rows:
            source=pointers[name];cpu.mem_write(source,bytes(0xe28))
            for offset,value in ((0,name),(0x6b4,ammo),(0x6bc,clip),(0x6cc,shared),(0xd20,alt),(0xd34,companion)):
                text=value.encode()+b'\0';cpu.mem_write(strings,text)
                cpu.mem_write(source+offset,struct.pack('<I',strings));strings+=len(text)
            cpu.mem_write(source+0x6d4,struct.pack('<I',capacity))
            for offset,value in ((0xd68,flags&1),(0xd69,bool(flags&2)),(0xd6a,bool(flags&4)),(0xdad,bool(flags&8)),(0x6b0,noclip)):
                cpu.mem_write(source+offset,bytes([value]))
        cpu.mem_write(0x17f5a40,struct.pack('<I',pointers['none']))
        cpu.mem_write(0x7817b88,bytes(4));self.error=False
        def existing(pointer):
            count=struct.unpack('<I',cpu.mem_read(0x7817b88,4))[0]
            for i in range(count+1):
                if struct.unpack('<I',cpu.mem_read(0x17f5a40+4*i,4))[0]==pointer:return i
            return None
        def lookup(cpu,address,size,context):
            sp=cpu.reg_read(UC_X86_REG_ESP);ret,nameptr=struct.unpack('<II',cpu.mem_read(sp,8))
            name=bytes(cpu.mem_read(nameptr,128)).split(b'\0',1)[0].decode()
            pointer=pointers[name];slot=existing(pointer)
            if slot is None:
                cpu.reg_write(UC_X86_REG_EAX,pointer);cpu.reg_write(UC_X86_REG_EIP,0x42c3e0)
            else:
                cpu.reg_write(UC_X86_REG_EAX,slot);cpu.reg_write(UC_X86_REG_ESP,sp+4);cpu.reg_write(UC_X86_REG_EIP,ret)
        hook=cpu.hook_add(UC_HOOK_CODE,lookup,begin=0x42c5c0,end=0x42c5c0)
        try:
            for row in rows[1:]:
                pointer=pointers[row[0]]
                if existing(pointer) is not None:continue
                cpu.mem_write(stack,struct.pack('<I',end));cpu.reg_write(UC_X86_REG_ESP,stack)
                cpu.reg_write(UC_X86_REG_EAX,pointer);cpu.reg_write(UC_X86_REG_EDI,0)
                cpu.emu_start(0x42c3e0,end,count=200000)
                if self.error:return None
                if cpu.reg_read(UC_X86_REG_EIP)!=end:raise ValueError('client recursive registration did not finish')
            return [tuple(struct.unpack('<i',cpu.mem_read(pointers[row[0]]+off,4))[0]
                          for off in (0x6b8,0x6c0,0x6d0)) for row in rows]
        finally:cpu.hook_del(hook)

    def register_composed_weapon(self, *, base, name):
        """Register one resolved recipe fixture after weapon_registry().

        Seed the record layout produced by 0x42e3b0; execute 0x42c3e0 and its
        real ammo/clip registrars. Recipe parsing and asset loading are outside
        this seam. The fixture owns the first composed-record slot.
        """
        cpu=self.cpu;stack,end=0x303ff000,0x303ffff0
        record=0x18178c0;definition=record+0xa0
        def word(address):
            return struct.unpack('<I',cpu.mem_read(address,4))[0]
        def text(address):
            return bytes(cpu.mem_read(address,128)).split(b'\0',1)[0].decode('ascii')
        source=word(0x17f5a40+4*base)
        cpu.mem_write(record,bytes(0x1254))
        cpu.mem_write(record,name.encode('ascii')+b'\0')
        cpu.mem_write(definition,bytes(cpu.mem_read(source,0xe28)))
        # 0x42e4bd/+94 base ID, 0x42e4db/+9c base pointer, +a0 cloned Def.
        for address,value in ((record+0x94,base),(record+0x9c,source),
                              (definition,record),(0x17f5844,1)):
            cpu.mem_write(address,struct.pack('<I',value))
        cpu.mem_write(stack,struct.pack('<I',end));self.error=False
        cpu.reg_write(UC_X86_REG_ESP,stack)
        cpu.reg_write(UC_X86_REG_EAX,definition);cpu.reg_write(UC_X86_REG_EDI,0)
        cpu.emu_start(0x42c3e0,end,count=200000)
        if self.error or cpu.reg_read(UC_X86_REG_EIP)!=end:
            raise ValueError('client composed registration did not finish')
        weapon=cpu.reg_read(UC_X86_REG_EAX)
        registered=word(0x17f5a40+4*weapon)
        return dict(weapon=weapon,definition=registered,name=text(word(registered)),
                    ammo=word(registered+0x6b8),clip=word(registered+0x6c0),
                    base_name=text(word(source)),
                    base_keys=(word(source+0x6b8),word(source+0x6c0)))

    def composed_viewmodels(self, definition, *, view_model, attachments=()):
        """Execute 0x42e800's real lookup and model-list selection.

        Supply distinct view/world XModels at the resolved-asset boundary.
        Stub only 0x49b120's streaming requests; no bones or renderer execute.
        None represents an unpopulated composition, which must return false.
        """
        cpu=self.cpu;stack,end=0x303ff000,0x303ffff0
        record=0x18178c0;models,count=0x30360000,0x30368000
        hand,fallback=0x30370000,0x30371000
        def asset(pointer,name):
            cpu.mem_write(pointer,bytes(0x200))
            cpu.mem_write(pointer,struct.pack('<I',pointer+0x180))
            cpu.mem_write(pointer+0x180,name.encode('ascii')+b'\0')
        asset(hand,'viewhands_tf141');asset(fallback,'tag_origin')
        entries=[(view_model,'wea_acr_acr_blk',0),*attachments] if view_model else []
        # Current composition: tags +f48, world +f68, view +fac; +92 is count.
        cpu.mem_write(record+0x92,bytes([len(entries)]))
        for i,(view,world,tag) in enumerate(entries):
            gun=0x30372000+i*0x800
            asset(gun,view);asset(gun+0x400,world)
            cpu.mem_write(record+0xf48+2*i,struct.pack('<H',tag))
            cpu.mem_write(record+0xf68+4*i,struct.pack('<I',gun+0x400))
            cpu.mem_write(record+0xfac+4*i,struct.pack('<I',gun))
        cpu.mem_write(definition+0x10,struct.pack('<I',fallback))
        cpu.mem_write(models,bytes(0x2c*(len(entries)+1)))
        cpu.mem_write(models,struct.pack('<I',hand))
        cpu.mem_write(count,struct.pack('<H',1))
        cpu.mem_write(stack,struct.pack('<5I',end,0x32d,models,count,0))
        cpu.reg_write(UC_X86_REG_ESP,stack);cpu.reg_write(UC_X86_REG_EAX,definition)
        hook=cpu.hook_add(UC_HOOK_CODE,self._return,begin=0x49b120,end=0x49b120)
        self.error=False
        try:
            cpu.emu_start(0x42e800,end,count=200000)
            stopped=cpu.reg_read(UC_X86_REG_EIP)
            if self.error or stopped!=end:
                raise ValueError('client composed model selection did not finish')
        finally:cpu.hook_del(hook)
        def model_name(pointer_address):
            pointer,=struct.unpack('<I',cpu.mem_read(pointer_address,4))
            name,=struct.unpack('<I',cpu.mem_read(pointer,4))
            return bytes(cpu.mem_read(name,128)).split(b'\0',1)[0].decode('ascii')
        size,=struct.unpack('<H',cpu.mem_read(count,2))
        return dict(models=[model_name(models+i*0x2c) for i in range(size)],
                    tags=[struct.unpack('<H',cpu.mem_read(models+i*0x2c+4,2))[0] for i in range(size)],
                    fallback=model_name(definition+0x10),appended=size>1)

    def usercmd(self, values, *, key, base=None, move=False, reliables=()):
        """Run the shipped 0x5a1be0 writer; inputs use its real usercmd layout."""
        cpu = self.cpu
        msg, data, source, dest = 0x30000000, 0x30001000, 0x30280000, 0x30290000
        stack, end = 0x303ff000, 0x303ffff0
        offsets = {'time': (0, 'I'), 'buttons': (4, 'I'), 'pitch': (8, 'I'),
                   'yaw': (12, 'I'), 'roll': (16, 'I'), 'weapon': (20, 'H'),
                   'alt': (22, 'H'), 'offhand': (24, 'H'), 'forward': (26, 'b'),
                   'right': (27, 'b'), 'melee_yaw': (28, 'f'), 'melee_dist': (32, 'B'),
                   'melee_target': (34, 'H'), 'location_x': (36, 'B'),
                   'location_y': (37, 'B'), 'location_angle': (38, 'B'),
                   'remote_x': (39, 'B'), 'remote_y': (40, 'B')}
        for address, command in ((source, base or {}), (dest, values)):
            cpu.mem_write(address, bytes(44))
            for field, value in command.items():
                offset, form = offsets[field]
                cpu.mem_write(address + offset, struct.pack('<' + form, value))
        from games.codol.versions.v3_3_3_3.server.story_wire423 import _Message
        prefix = _Message()
        if move:
            for sequence, command in reliables:
                prefix.bits(2, 3)
                prefix.data.extend(struct.pack('<I', sequence)+command+b'\0')
            prefix.bits(1, 3)  # moveNoDelta, one command.
            prefix.data.append(1)
            cpu.mem_write(data, bytes(prefix.data))
        cpu.mem_write(msg, struct.pack('<12I', 0, 0, data, 0, 4096, len(prefix.data),
                                      0, 0, prefix.bit, 0, 0, 0))
        cpu.mem_write(stack, struct.pack('<III', end, key, source))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.reg_write(UC_X86_REG_EAX, msg)
        cpu.reg_write(UC_X86_REG_ESI, dest)
        cpu.emu_start(0x5a1be0, end, count=100000)
        overflow, = struct.unpack('<I', cpu.mem_read(msg, 4))
        if overflow or cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError('client failed to encode usercmd')
        size, = struct.unpack('<I', cpu.mem_read(msg + 20, 4))
        if move:
            packet = bytearray(cpu.mem_read(data, size))
            packet.extend(struct.pack('<3fII', 0, 0, 0, values['time'], 0))
            bit, = struct.unpack('<I', cpu.mem_read(msg+32, 4))
            for i in range(3):  # EOF, retaining the writer's interleaved bit pool.
                if bit % 8 == 0:
                    bit = len(packet)*8
                    packet.append(0)
                packet[bit//8] |= ((3 >> i)&1) << (bit%8)
                bit += 1
            return bytes(packet)
        return bytes(cpu.mem_read(data, size))

    def default_usercmd(self, fields):
        cpu = self.cpu
        source, dest, stack, end = 0x30280000, 0x30290000, 0x303ff000, 0x303ffff0
        cpu.mem_write(source, bytes(0x3524))
        for i, value in fields.items():
            offset, bits, _ = self.player_fields[i]
            cpu.mem_write(source+offset, struct.pack('<Q' if bits==-94 else '<I', value))
        cpu.mem_write(stack,struct.pack('<I',end))
        cpu.reg_write(UC_X86_REG_ESP,stack)
        cpu.reg_write(UC_X86_REG_ESI,dest)
        cpu.reg_write(UC_X86_REG_EDI,source)
        cpu.emu_start(0x5a18e0,end,count=100000)
        if cpu.reg_read(UC_X86_REG_EIP)!=end:
            raise ValueError('client default usercmd did not finish')
        command=bytes(cpu.mem_read(dest,44))
        time,buttons,pitch,yaw,roll,weapon,alt,offhand=struct.unpack_from('<5I3H',command)
        melee,=struct.unpack_from('<H',command,34)
        return [time,buttons,pitch,yaw,roll,0,weapon,offhand,alt,0,0,melee,*command[36:41]]

    def _init_player(self, state, protected_value=0):
        cpu = self.cpu
        floats, stack, end = 0x302a0000, 0x303ff000, 0x303ffff0
        cpu.mem_write(state, bytes(0x3524))
        obj = state + 536
        keys = struct.unpack('<II', cpu.mem_read(0xce5184, 8))
        cpu.mem_write(obj + 16, struct.pack('<II', (obj + 20) ^ keys[0] ^ 0x401710,
                                            (obj + 16) ^ keys[1] ^ 0x4017b0))
        cpu.mem_write(floats, struct.pack('<3f', protected_value, 1., 2.))
        cpu.mem_write(stack, struct.pack('<III', end, floats, obj))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.emu_start(0x401710, end, count=10000)

    def playerstate(self, wire, *, server_time, base=None):
        cpu = self.cpu
        msg, data, stack, end = 0x30000000, 0x30001000, 0x303ff000, 0x303ffff0
        source, dest, floats = 0x30280000, 0x30290000, 0x302a0000
        # Deterministic seed only; protected-value storage and every network
        # reader still execute the shipped machine code.
        hook = cpu.hook_add(UC_HOOK_CODE, self._return, begin=0xa6e160, end=0xa6e160)
        try:
            for state in (source, dest):
                self._init_player(state, (base or {}).get(82, 0))
            for index, value in (base or {}).items():
                if index == 82:
                    continue
                offset, bits, _ = self.player_fields[index]
                cpu.mem_write(source + offset, struct.pack('<Q' if bits == -94 else '<I', value))
            self.error = False
            cpu.mem_write(data, wire)
            cpu.mem_write(msg, struct.pack('<12I', 0, 1, data, 0, len(wire), len(wire), 0, 0, 0, 0, 0, 0))
            cpu.mem_write(stack, struct.pack('<III', end, server_time, source))
            cpu.reg_write(UC_X86_REG_ESP, stack)
            cpu.reg_write(UC_X86_REG_ECX, dest)
            cpu.reg_write(UC_X86_REG_ESI, msg)
            cpu.emu_start(0x5a4230, end, count=2000000)
            overflow, = struct.unpack('<I', cpu.mem_read(msg, 4))
            if self.error or overflow or cpu.reg_read(UC_X86_REG_EIP) != end:
                raise ValueError('client rejected playerstate')
            result = [struct.unpack('<Q' if bits == -94 else '<I',
                                    cpu.mem_read(dest + o, 8 if bits == -94 else 4))[0]
                      for o, bits, _ in self.player_fields]
            # The protected byte's getter returns the logical float value.
            cpu.mem_write(stack, struct.pack('<III', end, dest + 536, floats))
            cpu.reg_write(UC_X86_REG_ESP, stack)
            cpu.emu_start(0x4017b0, end, count=10000)
            result[82] = int(struct.unpack('<f', cpu.mem_read(floats, 4))[0])
            cursor, = struct.unpack('<I', cpu.mem_read(msg + 28, 4))
            return result, wire[cursor:]
        finally:
            cpu.hook_del(hook)

    def entity(self, wire, *, base_type=0, base=None):
        cpu=self.cpu
        msg,data,source,dest,stack,end=0x30000000,0x30001000,0x30280000,0x30290000,0x303ff000,0x303ffff0
        keys=struct.unpack('<3I',cpu.mem_read(0xcda23c,12))
        for address in (source,dest):
            cpu.mem_write(address,bytes(0x110))
            for i,key in enumerate(keys):
                offset=0x18+i*4
                cpu.mem_write(address+offset,struct.pack('<I',(~key^(address+offset))&0xffffffff))
        cpu.mem_write(source+4,struct.pack('<I',base_type))
        fields={offset:bits for offset,bits,_ in self.entity_fields[min(base_type,22)]}
        for offset,value in (base or {}).items():
            if offset in (0x18,0x1c,0x20):
                value^=(~keys[(offset-0x18)//4]^(source+offset))&0xffffffff
            cpu.mem_write(source+offset,struct.pack('<Q' if fields[offset]==-94 else '<I',value))
        self.error=False
        cpu.mem_write(data,wire)
        cpu.mem_write(msg,struct.pack('<12I',0,1,data,0,len(wire),len(wire),0,0,0,0,0,0))
        cpu.mem_write(stack,struct.pack('<6I',end,msg,1000,source,dest,7))
        cpu.reg_write(UC_X86_REG_ESP,stack)
        cpu.emu_start(0x5a3670,end,count=500000)
        overflow,=struct.unpack('<I',cpu.mem_read(msg,4))
        if self.error or overflow or cpu.reg_read(UC_X86_REG_EIP)!=end:
            raise ValueError('client rejected entity')
        kind,=struct.unpack('<I',cpu.mem_read(dest+4,4))
        result={offset:struct.unpack('<Q' if bits==-94 else '<I',
            cpu.mem_read(dest+offset,8 if bits==-94 else 4))[0]
            for offset,bits,_ in self.entity_fields[min(kind,22)]}
        for i,key in enumerate(keys):
            offset=0x18+i*4
            result[offset]^=(~key^(dest+offset))&0xffffffff
        cursor,=struct.unpack('<I',cpu.mem_read(msg+28,4))
        return result,wire[cursor:]

    def object_state(self, wire, *, actor=False):
        cpu=self.cpu
        msg,data,source,dest,stack,end=0x30000000,0x30001000,0x30280000,0x30290000,0x303ff000,0x303ffff0
        size,count,table,gap=(0x58,24,0xc54298,3) if actor else (0x134,76,0xc55b68,1)
        initial=bytes(cpu.mem_read(0xc57218,size)) if actor else bytes(size)
        cpu.mem_write(source,initial);cpu.mem_write(dest,bytes(size))
        cpu.mem_write(data,wire)
        # Actor zero: present, sequential number, not removed; its public
        # encoder includes this 3-bit envelope before the generic reader.
        self.error=False
        cpu.mem_write(msg,struct.pack('<12I',0,1,data,0,len(wire),len(wire),0,
            1 if actor else 0,3 if actor else 0,0,0,0))
        cpu.mem_write(stack,struct.pack('<8I',end,msg,1000,source,dest,count,table,gap))
        cpu.reg_write(UC_X86_REG_ESP,stack)
        cpu.emu_start(0x5a34f0,end,count=500000)
        overflow,=struct.unpack('<I',cpu.mem_read(msg,4))
        if self.error or overflow or cpu.reg_read(UC_X86_REG_EIP)!=end:
            raise ValueError('client rejected object state')
        cursor,=struct.unpack('<I',cpu.mem_read(msg+28,4))
        return bytes(cpu.mem_read(dest,size)),wire[cursor:]

    def _return(self, cpu, address, size, context):
        stack = cpu.reg_read(UC_X86_REG_ESP)
        ret, = struct.unpack('<I', cpu.mem_read(stack, 4))
        cpu.reg_write(UC_X86_REG_EAX, 0)
        cpu.reg_write(UC_X86_REG_ESP, stack + 4)
        cpu.reg_write(UC_X86_REG_EIP, ret)

    def _error(self, cpu, address, size, context):
        self.error = True
        cpu.emu_stop()

    def _format(self, cpu, address, size, context):
        # Replace only the CRT formatting dependency, which needs Windows TLS.
        # Network fields and their bit widths are still read by original code.
        stack = cpu.reg_read(UC_X86_REG_ESP)
        ret, end, fmt = struct.unpack('<3I', cpu.mem_read(stack, 12))
        pattern = bytes(cpu.mem_read(fmt, 32)).split(b'\0', 1)[0]
        if pattern not in (b'* %i', b'** %i %i %i', b' %i'):
            raise ValueError(f'unhandled client format {pattern!r}')
        count = pattern.count(b'%i')
        values = struct.unpack('<' + 'I' * count, cpu.mem_read(stack + 12, 4 * count))
        dest = cpu.reg_read(UC_X86_REG_EDI)
        text = pattern % values
        if len(text) >= end - dest:
            raise ValueError('format buffer overflow')
        cpu.mem_write(dest, text + b'\0')
        cpu.reg_write(UC_X86_REG_EAX, dest + len(text))
        cpu.reg_write(UC_X86_REG_ESP, stack + 4)
        cpu.reg_write(UC_X86_REG_EIP, ret)

    def configstrings(self, wire, kinds=None):
        cpu = self.cpu
        self.error = False
        msg, data, stack, end = 0x30000000, 0x30001000, 0x303ff000, 0x303ffff0
        cpu.mem_write(data, wire)
        cpu.mem_write(msg, struct.pack('<10I', 0, 1, data, 0, len(wire), len(wire), 0, 0, 0, 0))
        cpu.mem_write(0x2df7da0, bytes(self.kinds) if kinds is None else kinds)
        cpu.mem_write(stack, struct.pack('<I', end))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.reg_write(UC_X86_REG_ECX, msg)
        cpu.emu_start(0x46db20, end, count=2000000)
        overflow, = struct.unpack('<I', cpu.mem_read(msg, 4))
        if self.error or overflow or cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError('client rejected configstrings')
        offsets = struct.unpack('<7058I', cpu.mem_read(0x796f2dc, 7058 * 4))
        size, = struct.unpack('<I', cpu.mem_read(0x7996124, 4))
        pool = bytes(cpu.mem_read(0x7976124, size))
        rows = {i: pool[o:pool.index(0, o)].decode('ascii') for i, o in enumerate(offsets) if o}
        cursor, = struct.unpack('<I', cpu.mem_read(msg + 28, 4))
        return rows, wire[cursor:]

    def gamestate(self, wire, *, checksum):
        """Stop at loading-screen archive setup, before world/renderer loading."""
        cpu = self.cpu
        msg, data, conn, stack, end = 0x30000000, 0x30001000, 0x30100000, 0x303ff000, 0x303ffff0
        self.error = False
        selected = {}
        def text(address):
            return bytes(cpu.mem_read(address, 64)).split(b'\0', 1)[0].decode('ascii')
        def loading(cpu, address, size, context):
            selected.update(map=text(cpu.reg_read(UC_X86_REG_EDI)),
                            game_type=text(cpu.reg_read(UC_X86_REG_EBP) - 0x88))
            cpu.emu_stop()
        hook = cpu.hook_add(UC_HOOK_CODE, loading, begin=0x4651b0, end=0x4651b0)
        try:
            cpu.mem_write(data, wire)
            cpu.mem_write(msg, struct.pack('<12I', 0, 1, data, 0, len(wire), len(wire), 0, 1, 0, 0, 0, 0))
            for address, value in ((0x1a2a538, conn ^ 0xd362501f), (0x1a2e7ec, 7),
                                   (0x2df9934, 1), (0x2df7d90, checksum), (0x788c760, 1),
                                   (0x35f2238, 0x30180000), (0x78b0bb8, 0)):
                cpu.mem_write(address, struct.pack('<I', value))
            cpu.mem_write(0x1a2e7dd, bytes(4))
            cpu.mem_write(0x17cd27e, b'\0')
            cpu.mem_write(0x2df7da0, bytes(self.kinds))
            cpu.mem_write(stack, struct.pack('<I', end))
            cpu.reg_write(UC_X86_REG_ESP, stack)
            cpu.reg_write(UC_X86_REG_ECX, msg)
            cpu.emu_start(0x46dea0, end, count=2000000)
            overflow, = struct.unpack('<I', cpu.mem_read(msg, 4))
            if self.error or overflow or not selected:
                raise ValueError('client rejected gamestate')
            for name, offset in (('command_sequence', 0x4014c), ('client_number', 4), ('checksum_feed', 0x13c)):
                selected[name], = struct.unpack('<I', cpu.mem_read(conn + offset, 4))
            cursor, = struct.unpack('<I', cpu.mem_read(msg + 28, 4))
            selected['remaining'] = wire[cursor:]
            return selected
        finally:
            cpu.hook_del(hook)

    def reset_netchan(self):
        cpu = self.cpu
        chan = 0x30180158
        cpu.mem_write(chan, bytes(0x6c8))
        cpu.mem_write(chan + 0x30, struct.pack('<II', 0x30200000, 0x20000))
        cpu.mem_write(0x788c760, struct.pack('<I', 1))
        cpu.mem_write(0xca19520, struct.pack('<I', 1))

    def snapshot(self, wire, *, sequence):
        cpu = self.cpu
        msg, data, conn, client = 0x30000000, 0x30001000, 0x30100000, 0x30240000
        stack, end = 0x303ff000, 0x303ffff0
        cpu.mem_write(client, bytes(0x9000))
        # One real snapshot-ring slot, no prior network history.
        for offset, value in ((0x8664, 1), (0x8668, 0), (0x8670,32), (0x8674,32),
                              (0x866c,2048), (0x8678,32),
                              (0x8684,0x30300000^0x4c248306),
                              (0x8690,0x302d0000^0xdf5b8c38),
                              (0x8688,0x302b0000^0x9100d3fb),
                              (0x868c,0x302c0000^0x3613bda3),
                              (0x8680, 0x30260000 ^ 0x336f4a9b),
                              (0x867c, 0x30270000 ^ 0x96b9dc91)):
            cpu.mem_write(client + offset, struct.pack('<I', value))
        cpu.mem_write(0x1a2a538, struct.pack('<I', conn ^ 0xd362501f))
        cpu.mem_write(0x1a2e838, struct.pack('<I', client ^ 0x6891d1c7))
        cpu.mem_write(conn + 0x40148, struct.pack('<I', sequence))
        cpu.mem_write(data, wire)
        cpu.mem_write(msg, struct.pack('<12I', 0, 1, data, 0, len(wire), len(wire), 0, 1, 0, 0, 0, 0))
        self.error = False
        hook = cpu.hook_add(UC_HOOK_CODE, self._return, begin=0xa6e160, end=0xa6e160)
        try:
            self._init_player(client + 12)
            self._init_player(0x30260000)
            cpu.mem_write(stack, struct.pack('<I', end))
            cpu.reg_write(UC_X86_REG_ESP, stack)
            cpu.reg_write(UC_X86_REG_ECX, msg)
            # A real first frame includes the player's inventory; its bounded
            # 128 KiB message needs more instructions than tiny wire fixtures.
            cpu.emu_start(0x46d170, end, count=32000000)
            overflow, = struct.unpack('<I', cpu.mem_read(msg, 4))
            if self.error or overflow or cpu.reg_read(UC_X86_REG_EIP) != end:
                raise ValueError('client rejected snapshot')
            result = {}
            for name, offset in (('command_time', 0), ('flags', 0x3528),
                                 ('server_time', 0x352c), ('sequence', 0x3530),
                                 ('entities', 0x3540), ('clients', 0x3544), ('actors', 0x3548)):
                result[name], = struct.unpack('<I', cpu.mem_read(0x30260000 + offset, 4))
            result['player_data'] = bytes(cpu.mem_read(0x30260000,0x3524))
            cursor, = struct.unpack('<I', cpu.mem_read(msg + 28, 4))
            result['remaining'] = wire[cursor:]
            entities = 0x7999690 if result['flags'] & 8 else 0x30300000
            for name,address,stride in (('entities',entities,0x110),
                                         ('clients',0x302b0000,0x134),('actors',0x302c0000,0x58)):
                if result[name]:
                    result[name+'_data']=[bytes(cpu.mem_read(address+i*stride,stride))
                                         for i in range(result[name])]
            return result
        finally:
            cpu.hook_del(hook)

    def snapshot_frame_ready(self, sequence):
        """Run the native CL_GetSnapshot and CG_DrawActiveFrame early gates.

        This proves delivery to the draw path, not a rendered frame or gameplay.
        """
        cpu=self.cpu
        cg,snapshot,stack,end=0x30010000,0x30020000,0x303ff000,0x303ffff0
        seed=cpu.hook_add(UC_HOOK_CODE,self._return,begin=0xa6e160,end=0xa6e160)
        try:
            self._init_player(snapshot)
            cpu.mem_write(stack,struct.pack('<II',end,snapshot))
            cpu.reg_write(UC_X86_REG_ESP,stack)
            cpu.reg_write(UC_X86_REG_EAX,sequence)
            cpu.emu_start(0x4f8fa0,end,count=1000000)
            if self.error or cpu.reg_read(UC_X86_REG_EIP)!=end or not cpu.reg_read(UC_X86_REG_EAX):
                raise ValueError('native cgame did not receive snapshot')
        finally:
            cpu.hook_del(seed)
        cpu.mem_write(cg+0x356c,struct.pack('<I',1))
        cpu.mem_write(cg+0x357c,struct.pack('<I',snapshot))
        cpu.mem_write(0x17cd282,b'\0')
        cpu.reg_write(UC_X86_REG_ESI,cg)
        def stop(cpu,address,size,context):
            cpu.emu_stop()
        hook=cpu.hook_add(UC_HOOK_CODE,stop,begin=0x541f13,end=0x541f13)
        try:
            cpu.emu_start(0x52639e,0x5263df,count=100)
            return cpu.reg_read(UC_X86_REG_EIP)==0x5263df
        finally:
            cpu.hook_del(hook)

    def packet(self, wire, *, challenge, command=b''):
        """Run actual netchan/reassembly and XOR; keep channel state across calls."""
        cpu = self.cpu
        msg, data, conn, stack, end = 0x30000000, 0x30001000, 0x30100000, 0x303ff000, 0x303ffff0
        self.error = False
        cpu.mem_write(data, wire)
        cpu.mem_write(msg, struct.pack('<12I', 0, 1, data, 0, 0x20000, len(wire), 0, 0, 0, 0, 0, 0))
        cpu.mem_write(stack, struct.pack('<II', end, conn + 0x80158))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.reg_write(UC_X86_REG_EDI, msg)
        cpu.emu_start(0x5a5960, end, count=2000000)
        if self.error or cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError('client netchan failed')
        if not cpu.reg_read(UC_X86_REG_EAX):
            return None
        overflow, _, _, _, _, size = struct.unpack('<6I', cpu.mem_read(msg, 24))
        if overflow or size < 8 or size > 0x20000:
            raise ValueError('client netchan overflow')
        sequence, ack = struct.unpack('<II', cpu.mem_read(data, 8))
        cpu.mem_write(0x1a2a538, struct.pack('<I', conn ^ 0xd362501f))
        for offset, value in ((0x138, challenge), (0x40148, sequence), (0x144, ack)):
            cpu.mem_write(conn + offset, struct.pack('<I', value))
        cpu.mem_write(conn + 0x148 + (ack & 255) * 1024, command + b'\0')
        cpu.mem_write(stack, struct.pack('<III', end, data + 8, size - 8))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.emu_start(0x46bf80, end, count=2000000)
        if cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError('client decryptor did not finish')
        return sequence, ack, bytes(cpu.mem_read(data + 8, size - 8))
