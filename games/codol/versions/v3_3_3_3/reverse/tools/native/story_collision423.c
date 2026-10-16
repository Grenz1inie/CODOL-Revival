/* FF423 collision layout -> reference engine section descriptors.
 * Source offsets refer to the verified original asset, never a patched FF.
 */
typedef unsigned int u32;
typedef struct { const unsigned char *data; u32 size, pos; } Cursor;
#define INLINE 0xffffffffu

static u32 word(const unsigned char *data)
{
    return (u32)data[0] | ((u32)data[1] << 8) | ((u32)data[2] << 16) | ((u32)data[3] << 24);
}

static int take(Cursor *c, u32 count, u32 stride)
{
    if (c->pos > c->size || count > (c->size - c->pos) / stride) return 0;
    c->pos += count * stride;
    return 1;
}

static int string(Cursor *c, u32 pointer)
{
    if (pointer != INLINE) return 1;
    while (c->pos < c->size) if (!c->data[c->pos++]) return 1;
    return 0;
}

static int section(Cursor *c, u32 *layout, u32 row, u32 count, u32 stride, u32 pointer)
{
    u32 *out = layout + row * 4;
    out[0] = pointer == INLINE ? c->pos : INLINE;
    out[1] = count; out[2] = stride; out[3] = pointer;
    if (!pointer && count) return 0;
    return pointer != INLINE || take(c, count, stride);
}

static int planes(Cursor *c, u32 offset, u32 count)
{
    u32 i;
    for (i = 0; i < count; ++i)
        if (word(c->data + offset + i * 8) == INLINE && !take(c, 1, 20)) return 0;
    return 1;
}

int read_collision_layout423(const u32 *asset, u32 *layout)
{
    Cursor c;
    u32 h[64], i, j, offset, pointer, count, inline_indices = 0, shared_nodes = 0;
    if (!asset || !layout || asset[0] != 15 || asset[3] != 423 ||
        !asset[1] || asset[2] < 256 || asset[2] > 0x20000000) return 0;
    c.data = (const unsigned char *)asset[1]; c.size = asset[2]; c.pos = 256;
    for (i = 0; i < 64; ++i) h[i] = word(c.data + i * 4);
    for (i = 0; i < 86; ++i) layout[i] = 0;
    if (!string(&c, h[0])) return 0;
#define SECTION(row, count, stride, pointer) if (!section(&c, layout, row, count, stride, pointer)) return 0
    SECTION(0, h[2], 20, h[3]);
    SECTION(2, h[4], 12, h[5]);
    if (h[4] && h[5] != INLINE) return 0;
    for (i = 0; i < h[4]; ++i)
        if (!string(&c, word(c.data + layout[8] + i * 12))) return 0;
    SECTION(3, h[6], 8, h[7]);
    if (h[6] && (h[7] != INLINE || !planes(&c, layout[12], h[6]))) return 0;
    SECTION(4, h[8], 1, h[9]);
    if (h[8] && h[9] != INLINE) return 0;
    SECTION(8, h[10], 20, h[11]);
    if (h[10] && h[11] != INLINE) return 0;
    for (i = 0; i < h[10]; ++i) {
        const unsigned char *node = c.data + layout[32] + i * 20;
        count = (u32)node[2] | ((u32)node[3] << 8);
        if (!count || count >= 0x8000) continue;
        if (word(node + 8) == INLINE) {
            if (!take(&c, count, 2)) return 0;
            inline_indices += count;
        } else ++shared_nodes;
    }
    SECTION(7, h[12], 2, h[13]);
    if (h[12] && h[13] != INLINE) {
        /* The observed 423 map stores every live leaf's brush list inline.
         * h[13] aliases that storage; do not install it twice. Mixed shared
         * leaf references need block relocation and are deliberately rejected.
         */
        if (shared_nodes || h[12] > inline_indices) return 0;
        layout[29] = 0; layout[31] = 0;
    }
    count = h[14] & 0xffff;
    SECTION(17, count, 36, h[15]);
    if (count && h[15] != INLINE) return 0;
    for (i = 0; i < count; ++i) {
        const unsigned char *brush = c.data + layout[68] + i * 36;
        if (word(brush + 4) == INLINE) {
            offset = c.pos;
            if (!take(&c, 1, 8) || !planes(&c, offset, 1)) return 0;
        }
        if (word(brush + 8) == INLINE && !take(&c, 1, 1)) return 0;
    }
    SECTION(18, count, 24, h[16]); SECTION(19, count, 4, h[17]);
    if (count && (h[16] != INLINE || h[17] != INLINE)) return 0;
    /* The extra cinfo points back to the same already loaded geometry. */
    if (h[18] < 0xfffffffeu) return 0;
    offset = c.pos;
    if (!take(&c, 1, 64)) return 0;
    for (i = 0; i < 16; ++i) {
        pointer = word(c.data + offset + i * 4);
        if (i < 12 && !(i & 1)) {
            if (pointer != h[i + 2]) return 0;
        } else if (i == 12) {
            if ((pointer & 0xffff) != count) return 0;
        } else if (pointer >= 0xfffffffeu) return 0;
    }
    SECTION(1, h[19], 76, h[20]);
    if (h[19] && h[20] != INLINE) return 0;
    for (i = 0; i < h[19]; ++i)
        if (word(c.data + layout[4] + i * 76) >= 0xfffffffeu) return 0;
    SECTION(5, h[21], 8, h[22]);
    if (h[21] && (h[22] != INLINE || !planes(&c, layout[20], h[21]))) return 0;
    SECTION(6, h[23], 40, h[24]);
    if (h[23] && h[24] != INLINE) return 0;
    SECTION(9, 0, 4, 0); /* FF423 has no global leaf-surface array. */
    SECTION(10, h[25], 12, h[26]); SECTION(11, h[27], 6, h[28]);
    if (h[27] > (0xffffffffu - 31) / 3) return 0;
    SECTION(12, (h[27] * 3 + 31) >> 5, 4, h[29]);
    SECTION(13, h[30], 28, h[31]); SECTION(14, h[32], 12, h[33]);
    if ((h[25] && h[26] != INLINE) || (h[27] && (h[28] != INLINE || h[29] != INLINE)) ||
        (h[30] && h[31] != INLINE) || (h[32] && h[33] != INLINE)) return 0;
    for (i = 0; i < h[32]; ++i)
        if (word(c.data + layout[56] + i * 12 + 8) == INLINE && !take(&c, 1, 28)) return 0;
    SECTION(15, h[34], 32, h[35]); SECTION(16, h[36], 72, h[37]);
    if ((h[34] && h[35] != INLINE) || (h[36] && h[37] != INLINE)) return 0;
    pointer = 0;
    for (i = 0; i < h[36]; ++i) {
        j = word(c.data + layout[64] + i * 72 + 28);
        if (!j || j >= 0xfffffffeu || (i && j != pointer)) return 0;
        pointer = j;
    }
    SECTION(20, h[47] & 0xffff, 28, h[48]);
    if ((h[47] & 0xffff) && h[48] != INLINE) return 0;
    layout[84] = c.pos; layout[85] = h[0];
    if (h[38] < 0xfffffffeu || !take(&c, 1, 36) ||
        word(c.data + layout[84]) != h[0]) return 0;
    return 1;
#undef SECTION
}
