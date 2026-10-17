"""Loaded catalog reconstruction, without a reference package or player data."""
import struct
import unittest

from games.codol.versions.v3_19_26_22.client.resource_tables import catalog


class Memory:
    def __init__(self):
        self.blocks = {}

    def put(self, address, value):
        self.blocks[address] = bytes(value)

    def words(self, address, *values):
        self.put(address, struct.pack('<' + 'I' * len(values), *values))

    def read(self, address, size):
        for start, value in self.blocks.items():
            if start <= address and address + size <= start + len(value):
                return value[address - start:address - start + size]
        raise OSError('unreadable resource')


def fixture():
    m = Memory()
    m.words(0x779583c, 0x10000000, 3, 0x10001000, 3)
    m.put(0x779584c, struct.pack('<70H', 200, 0, 0, *([200] * 67)))
    m.put(0x10001000, struct.pack('<3H', 0, 1, 2))
    items = bytearray(120)
    struct.pack_into('<H', items, 40+2, 1)
    struct.pack_into('<I', items, 40+8, 0x10002000)
    items[80+5] = 1  # non-weapon item: do not read weapon extension
    struct.pack_into('<I', items, 80+8, 0x10002100)
    m.put(0x10000000, items)
    m.put(0x10002000, b'm4_mp\0' + bytes(250))
    m.put(0x10002100, b'character\0' + bytes(246))
    m.words(0x77988e4, 0x10003000, 2)
    extension = bytearray(288)
    struct.pack_into('<15H', extension, 144+0x26, *range(15))
    m.put(0x10003000, extension)
    parts = bytearray(0x3ffd*4)
    struct.pack_into('<I', parts, 7*4, 0x10002200)
    m.put(0x1978640, parts)
    m.put(0x10002200, b'sco_none\0' + bytes(247))

    # One ordinary SKU, one runtime SKU, and empty/out-of-range entries.
    m.words(0x7798008, 0x10004000, 4)
    m.put(0x10004000, struct.pack('<4H', 0, 1, 0, 99))
    m.words(0x7798000, 0x10005000, 2)
    m.put(0x8301ae4, struct.pack('<H', 1))
    m.put(0x8301ae8, struct.pack('<5000H', 2, *([0] * 4999)))
    m.words(0x7797ff8, 0x10006000, 3)
    m.put(0x10006000, struct.pack('<3H', 0, 1, 0))
    m.words(0x7797fe8, 0x10007000, 2)
    product = bytearray(56)
    struct.pack_into('<H', product, 28, 19)
    product[28+14] = 2
    struct.pack_into('<I', product, 28+16, 0x10008000)
    m.put(0x10007000, product)
    m.words(0x10008000, 1001, 1002)
    m.put(0xe57358, struct.pack('<9I', 0, 0, 0x1234, 0x5678, 0x9abcdef0, 0x4321, 0, 0, 0))
    def sku(address, currency, price, days):
        data = bytearray(24)
        def enc16(offset, value, key):
            struct.pack_into('<H', data, offset, ((value >> 4) | (value << 12)) & 65535 ^ key ^ ((address+offset) & 65535))
        enc16(4, 1, 0x1234)
        enc16(6, currency, 0x5678)
        struct.pack_into('<I', data, 8, ((price >> 8) | (price << 24)) & 0xffffffff ^ 0x9abcdef0 ^ (address+8))
        enc16(12, days, 0x4321)
        return data
    m.put(0x10005000, bytes(24) + sku(0x10005018, 1, 3400, 0))
    m.put(0x7798918, sku(0x7798918, 2, 1780, 7))
    return m


class ResourceTablesTests(unittest.TestCase):
    def test_catalog_preserves_item_aliases_parts_and_native_encoded_shop_values(self):
        data = catalog(fixture().read)
        self.assertEqual(data['items'], [(1001, 1, 'm4_mp'), (1002, 2, 'character'),
                                         (2001, 1, 'm4_mp'), (2002, 2, 'character')])
        self.assertEqual(data['parts'], [(7, 'sco_none')])
        self.assertEqual(data['weapons'], [(1001, 'm4_mp', 1, list(range(15))),
                                           (2001, 'm4_mp', 1, list(range(15)))])
        self.assertEqual(data['skus'], [(1, 19, [1001, 1002], 1, 3400, 0),
                                       (4, 19, [1001, 1002], 2, 1780, 7)])

    def test_unloaded_or_corrupt_tables_never_look_like_an_empty_catalog(self):
        m = fixture()
        m.words(0x779583c, 0, 0, 0, 0)
        with self.assertRaisesRegex(ValueError, 'item'):
            catalog(m.read)
        m = fixture()
        m.words(0x7797fe8, 0x10007000, 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'product'):
            catalog(m.read)

    def test_unterminated_names_and_failed_memory_reads_are_rejected(self):
        m = fixture()
        m.put(0x10002000, b'x'*256)
        with self.assertRaisesRegex(ValueError, 'name'):
            catalog(m.read)
        m = fixture()
        del m.blocks[0x10007000]
        with self.assertRaises(OSError):
            catalog(m.read)
