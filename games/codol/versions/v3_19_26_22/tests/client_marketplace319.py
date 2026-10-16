"""Captured inventory -> native hash -> shop ownership, in an offline x86 VM.

Registry fixtures retain the observed ID/slot relationships. Only allocator,
random initialization and the optional free-item fallback are substituted;
inventory deserialization, hash insert/lookup and ownership checks run natively.
"""
import struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP
from client_inventory319 import InventoryReader319


class MarketplaceReader319:
    def __init__(self, weapons):
        self.reader = InventoryReader319()
        self.cpu = self.reader.cpu
        for address, size in ((0x7790000, 0x10000), (0x8200000, 0x100000),
                              (0x88b0000, 0x400000), (0xc911000, 0x1000)):
            self.cpu.mem_map(address, size)
        write = self.reader.write32
        write(0x779583c, 0x20400000)
        write(0x7795840, 900)
        write(0x7795844, 0x20410000)
        write(0x7795848, 2000)
        self.cpu.mem_write(0x779584c + 10*2, struct.pack('<H', 1000))
        write(0x7797fe8, 0x20420000)
        write(0x7797fec, len(weapons) + 2)
        write(0x7797ff8, 0x20421000)
        write(0x7797ffc, 256)
        for index, (old, shop, slot, _, product, _) in enumerate(weapons, 1):
            for item in (old % 1000, 1000 + shop % 1000):
                self.cpu.mem_write(0x20410000 + item*2, struct.pack('<H', slot))
            self.cpu.mem_write(0x20400000 + slot*40, struct.pack('<H', shop))
            self.product(index, product, [shop])
        self.product(len(weapons) + 1, 102, [10009, 10013])
        for address in (0x5e9840, 0xb73fc0, 0xb73f40, 0x5e3550, 0x5e3580):
            self.cpu.hook_add(UC_HOOK_CODE, self.environment_hook, begin=address, end=address)

    def product(self, index, product_id, items):
        entry, array = 0x20420000 + index*28, 0x20422000 + index*16
        self.cpu.mem_write(0x20421000 + product_id*2, struct.pack('<H', index))
        self.cpu.mem_write(entry + 14, bytes([len(items)]))
        self.reader.write32(entry + 16, array)
        self.cpu.mem_write(array, b''.join(struct.pack('<HH', i, 1) for i in items))

    def environment_hook(self, cpu, address, size, _):
        sp = cpu.reg_read(UC_X86_REG_ESP)
        if address == 0x5e9840:
            self.reader.write32(0xe585e0, 0x12345678)
            self.reader.write32(0x82e1310, 0x20500000)
            cpu.mem_write(0x20500000, struct.pack('<6I', 0, 64, 0x3f000000, 64, 0x20501000, 0))
            cpu.mem_write(0x20501000, bytes(64*4))
        cpu.reg_write(UC_X86_REG_EAX, 0x13579 if address == 0xb73f40 else 0)
        cpu.reg_write(UC_X86_REG_ESP, sp + 4)
        cpu.reg_write(UC_X86_REG_EIP, self.reader.u32(sp))

    def publish(self, data):
        result = self.reader.parse(data)
        assert result['ok'] == 1 and result['count'] < 64
        self.reader.write32(0x82c4a8c, result['count'])
        if result['count']:
            self.cpu.mem_write(0x88ba0d8, bytes(self.cpu.mem_read(result['items'], result['count']*0xb8)))
        self.reader.call(0x5e9720, 0)

    def permanent(self, product):
        return bool(self.reader.call(0x5e8130, product))

    def product_flags(self, item):
        # Execute the real ProductObj builder through its ownership/expiry decision.
        sp = 0x100f0000
        self.cpu.mem_write(sp - 0x1000, bytes(0x1000))
        self.cpu.mem_write(sp, struct.pack('<III', 0xf00100, item, 0xffffffff))
        self.cpu.reg_write(UC_X86_REG_ESP, sp)
        self.cpu.reg_write(UC_X86_REG_ECX, 0x20080000)
        self.cpu.emu_start(0x5e0d30, 0x5e0e60, count=100000)
        assert self.cpu.reg_read(UC_X86_REG_EIP) == 0x5e0e60
        sp = self.cpu.reg_read(UC_X86_REG_ESP)
        return tuple(bool(self.cpu.mem_read(sp + offset, 1)[0]) for offset in (0x64, 0x52))
