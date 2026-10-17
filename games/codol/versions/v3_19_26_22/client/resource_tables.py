"""Reconstruct 3.19 catalogs from the matching client's loaded resource tables.

Read-only layouts: item lookup 0x779583c, parts 0x1978640, shop 0x7797fe8.
SKU fields use the native address/key XOR and 16/32-bit rotations. These are
resource definitions, never the player's inventory or wallet.
"""
import struct


def catalog(read):
    def u32(address):
        return struct.unpack('<I', read(address, 4))[0]

    def u16(address):
        return struct.unpack('<H', read(address, 2))[0]

    def table(address, stride, label):
        pointer, count = struct.unpack('<II', read(address, 8))
        if not pointer or not 0 < count <= 65536:
            raise ValueError(f'{label} resource table is not loaded or invalid')
        return pointer, count, read(pointer, count * stride)

    def name(pointer):
        data = read(pointer, 256)
        if b'\0' not in data:
            raise ValueError('Unterminated resource name')
        value = data.split(b'\0')[0].decode('ascii')
        if not value or any(c.isspace() for c in value):
            raise ValueError('Invalid resource name')
        return value

    def word(data, offset):
        return struct.unpack_from('<H', data, offset)[0]

    def rol(value, count, bits):
        value &= (1 << bits) - 1
        return ((value << count) | (value >> (bits - count))) & ((1 << bits) - 1)

    _, item_count, entries = table(0x779583c, 40, 'item')
    _, slot_count, slots = table(0x7795844, 2, 'item index')
    _, extension_count, extensions = table(0x77988e4, 144, 'weapon extension')
    buckets = struct.unpack('<70H', read(0x779584c, 140))
    names, items, weapons = {}, [], []
    for item in range(1, 70000):
        slot = (buckets[item // 1000] + item % 1000) & 65535
        if slot >= slot_count:
            continue
        index = word(slots, slot * 2)
        if not 0 < index < item_count:
            continue
        if index not in names:
            names[index] = name(struct.unpack_from('<I', entries, index * 40 + 8)[0])
        items.append((item, index, names[index]))
        extension = word(entries, index * 40 + 2)
        if entries[index * 40 + 5] == 0 and 0 < extension < extension_count:
            parts = list(struct.unpack_from('<15H', extensions, extension * 144 + 0x26))
            weapons.append((item, names[index], extension, parts))
    if not items:
        raise ValueError('Empty item resource table')
    parts = [(index, name(pointer)) for index, pointer in
             enumerate(struct.unpack('<16381I', read(0x1978640, 0x3ffd * 4))) if pointer]

    _, sku_count, sku_slots = table(0x7798008, 2, 'SKU index')
    sku_pointer, row_count, rows = table(0x7798000, 24, 'SKU')
    _, product_slot_count, product_slots = table(0x7797ff8, 2, 'product index')
    _, product_count, products = table(0x7797fe8, 28, 'product')
    extra_count = u16(0x8301ae4)
    if extra_count > 5000:
        raise ValueError('Runtime SKU count exceeds capacity')
    extra_rows = read(0x7798918, extra_count * 24) if extra_count else b''
    extra_slots = read(0x8301ae8, 5000 * 2)
    product_key, currency_key = u16(0xe57360), u16(0xe57364)
    price_key, days_key = u32(0xe57368), u16(0xe5736c)
    skus = []
    for sku in range(1, min(sku_count + 5000, 65536)):
        index = word(sku_slots, sku * 2) if sku < sku_count else word(extra_slots, (sku - sku_count) * 2)
        if not index or index >= row_count + extra_count:
            continue
        if index < row_count:
            address, row = sku_pointer + index * 24, rows[index * 24:(index + 1) * 24]
        else:
            index -= row_count
            address, row = 0x7798918 + index * 24, extra_rows[index * 24:(index + 1) * 24]
        slot = rol(word(row, 4) ^ product_key ^ (address + 4), 4, 16)
        if not 0 < slot < product_slot_count:
            continue
        product = word(product_slots, slot * 2)
        if not 0 < product < product_count:
            continue
        record = products[product * 28:(product + 1) * 28]
        count, pointer = record[14], struct.unpack_from('<I', record, 16)[0]
        if count > 64:
            raise ValueError('Product item count exceeds capacity')
        contents = [word(read(pointer + i * 4, 4), 0) for i in range(count)]
        currency = rol(word(row, 6) ^ currency_key ^ (address + 6), 4, 16)
        price = rol(struct.unpack_from('<I', row, 8)[0] ^ price_key ^ (address + 8), 8, 32)
        days = rol(word(row, 12) ^ days_key ^ (address + 12), 4, 16)
        skus.append((sku, word(record, 0), contents, currency, price, days))
    if not skus:
        raise ValueError('Empty SKU resource table')
    return {'items': items, 'weapons': weapons, 'parts': parts, 'skus': skus}
