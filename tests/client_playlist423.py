"""Run the shipped playlist parser without the game process or renderer."""
import json
import struct

from client_reader423 import ClientReader423, ROOT
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP


class ClientPlaylist423(ClientReader423):
    def __init__(self):
        super().__init__()
        # Map download metadata is an external input, not playlist syntax.
        # Use the no-download-version value returned by 0x5809e0 when disabled.
        self.cpu.hook_add(UC_HOOK_CODE, self._map_version, begin=0x630ab0, end=0x630ab0)
        tables=json.loads((ROOT/'research/evidence/live-marketplace.json').read_text('utf-8'))['tables']
        self.unlock_ids={row[0]:int(row[1]) for row in tables['mp/unlockFlags.csv'] if row[1]}
        self.cpu.hook_add(UC_HOOK_CODE, self._unlock_id, begin=0x4a4b10, end=0x4a4b10)

    def _map_version(self, cpu, address, size, context):
        self._return(cpu, address, size, context)
        cpu.reg_write(UC_X86_REG_EAX, 0)

    def _unlock_id(self, cpu, address, size, context):
        pointer,=struct.unpack('<I',cpu.mem_read(cpu.reg_read(UC_X86_REG_ESP)+4,4))
        name=bytes(cpu.mem_read(pointer,256)).split(b'\0')[0].decode('utf-8')
        self._return(cpu,address,size,context)
        cpu.reg_write(UC_X86_REG_EAX,self.unlock_ids.get(name,0))

    def parse(self, text):
        cpu=self.cpu
        cpu.mem_write(0x30000000,text+b'\0')
        # Registered build-version enum: shipped default is index 1 (release).
        # Read the first category-name slot; this catalogue sets both identically.
        for address,storage,value in ((0x2e8a978,0x303f0000,1),(0x315fbec,0x303f0100,0)):
            cpu.mem_write(address,struct.pack('<I',storage))
            cpu.mem_write(storage+12,struct.pack('<I',value))
        cpu.mem_write(0x303ff000,struct.pack('<2I',0x303ffff0,0x30000000))
        cpu.reg_write(UC_X86_REG_ESP,0x303ff000)
        cpu.emu_start(0x6111d0,0x303ffff0,count=30000000)
        if cpu.reg_read(UC_X86_REG_EIP)!=0x303ffff0 or self.error:
            raise ValueError('current playlist parser did not finish')
        count,=struct.unpack('<I',cpu.mem_read(0x35bce18,4))
        categories=[]
        for i in range(count):
            base=0x783faa0+i*0x454
            category,group=struct.unpack('<2I',cpu.mem_read(base,8))
            length,=struct.unpack('<I',cpu.mem_read(base+0x44c,4))
            entries=list(struct.unpack('<'+'I'*length,cpu.mem_read(base+0x4c,4*length)))
            name=bytes(cpu.mem_read(base+12,64)).split(b'\0')[0].decode('gbk')
            categories.append(dict(id=category,group=group,name=name,playlists=entries))
        return categories

    def menu_type(self, playlist_id):
        """Execute 0x613ed0, which GetPlayList publishes as the UI's `type`."""
        cpu=self.cpu
        # Published catalogue ready, no update pending; no classification is stubbed.
        cpu.mem_write(0xb5e6f78,b'\x01\x00')
        cpu.mem_write(0x303ff000,struct.pack('<I',0x303ffff0))
        cpu.reg_write(UC_X86_REG_ESP,0x303ff000)
        cpu.reg_write(UC_X86_REG_ECX,playlist_id)
        cpu.emu_start(0x613ed0,0x303ffff0,count=10000)
        if cpu.reg_read(UC_X86_REG_EIP)!=0x303ffff0:
            raise ValueError('current playlist UI classification did not finish')
        return cpu.reg_read(UC_X86_REG_EAX)

    def playlist(self, playlist_id):
        base=0x31fe618+playlist_id*0x3ba8
        count,=struct.unpack('<I',self.cpu.mem_read(base+0x3a98,4))
        def string(address, size):
            return bytes(self.cpu.mem_read(address,size)).split(b'\0')[0].decode('gbk')
        return dict(name=string(base,64),description=string(base+64,256),
                    maps=[(string(base+0x960+i*60,32),string(base+0x980+i*60,16))
                          for i in range(count)])
