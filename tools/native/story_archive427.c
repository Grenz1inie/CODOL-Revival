/* FF423 (0x1a7) add-on entities. REA client 0x48dbc0, 0x48d240, 0x48cf20.
 * Calls the reference replay allocator, retaining source/capacity checks and
 * both replay passes. Linked PC-relative; no imports, globals, or fixed-base use.
 */
typedef unsigned int u32;
#define REGS __attribute__((regparm(3)))
extern int REGS archive_reserve(u32 *, u32, u32, u32, int, int, u32 *);
extern const u32 *REGS archive_bytes(u32 *, u32, u32, u32, int);
extern int REGS archive_string(u32 *, int);
extern int archive_push(u32 *, u32);
extern int archive_pop(u32 *);
extern int REGS archive_asset(u32 *, u32, int, u32);
extern int REGS archive_sound(u32 *, u32, int);
extern int REGS archive_record_asset(u32 *, u32, u32, u32, int);
extern int REGS archive_water(u32 *, int, u32 *);
extern int read_collision_layout423(const u32 *, u32 *);
extern void *native_malloc(u32);
extern void native_free(void *);
extern int native_read_entities(const void *, u32, void *);

/* FF423 moved the stage pointer/count from MapEnts to clipMap. Supply the
 * original reader's 44-byte header in a temporary view; it validates and owns
 * its copied entity/trigger/stage data before this temporary view is freed.
 */
int read_collision_entities423(const u32 *asset, void *out)
{
    u32 layout[86], size, i;
    const unsigned char *body;
    unsigned char *copy;
    const u32 *header;
    int ok;
    if (!out || !read_collision_layout423(asset, layout)) return 0;
    header = (const u32 *)asset[1];
    body = (const unsigned char *)asset[1] + layout[84];
    size = asset[2] - layout[84];
    copy = native_malloc(size + 8);
    if (!copy) return 0;
    for (i = 0; i < 36; ++i) copy[i] = body[i];
    ((u32 *)copy)[9] = header[39];
    ((u32 *)copy)[10] = header[40] & 0xff;
    for (i = 36; i < size; ++i) copy[i + 8] = body[i];
    ok = native_read_entities(copy, size + 8, out);
    native_free(copy);
    return ok;
}

/* Obtain callback addresses relative to this loaded image, including under ASLR.
 * Reuse native reference registration, shared pointers and both replay passes.
 */
static u32 loaded_address(u32 preferred)
{
    u32 anchor;
    __asm__("call 1f\n1: pop %0\naddl $(_archive_push - 1b), %0" : "=r"(anchor));
    return anchor - 0x550a52 + preferred;
}

/* Client 0x488bd0 / 0x4888f0 / 0x487d60: a texture owns a persistent
 * image-pointer slot. Later aliases dereference that slot, not the image bytes.
 * Preserve both holder and optional -2 insertion aliases in the typed registry.
 */
int replay_material423(u32 *ctx, int pass, u32 *encoded)
{
    const unsigned char *h = (const unsigned char *)(ctx[32] + ctx[34]);
    const u32 *textures;
    u32 i, ignored, slots, ref, start, insertion;
    if (ctx[179] != 423 || !archive_reserve(ctx, 0, 104, 4, 1, pass, encoded) ||
        !archive_push(ctx, 3)) return 0;
    if (*(const u32 *)(h + 16) == 0xffffffffu && !archive_string(ctx, pass)) return 0;
    if (!archive_asset(ctx, *(const u32 *)(h + 88), pass, loaded_address(0x551680))) return 0;
    if (*(const u32 *)(h + 92) == 0xffffffffu) {
        slots = 0x30000001u + ((ctx[19] + 3) & ~3u);
        textures = archive_bytes(ctx, h[80], 12, 4, pass);
        if (!textures) return 0;
        for (i = 0; i < h[80]; ++i) {
            ref = textures[3 * i + 2];
            if ((textures[3 * i + 1] >> 24) == 11) {
                if (ref == 0xffffffffu && !archive_water(ctx, pass, &ignored)) return 0;
                continue;
            }
            start = ctx[34];
            insertion = 0x30000001u + ((ctx[19] + 3) & ~3u);
            if (!archive_asset(ctx, ref, pass, loaded_address(0x551141))) return 0;
            if (ref >= 0xfffffffeu) {
                if (!archive_record_asset(ctx, 10, slots + 12 * i + 8, start, pass)) return 0;
                if (ref == 0xfffffffeu &&
                    !archive_record_asset(ctx, 10, insertion, start, pass)) return 0;
            }
        }
    }
    if (*(const u32 *)(h + 96) == 0xffffffffu && !archive_bytes(ctx, h[81], 32, 16, pass)) return 0;
    if (*(const u32 *)(h + 100) == 0xffffffffu && !archive_bytes(ctx, h[82], 8, 4, pass)) return 0;
    return archive_pop(ctx);
}

enum { STRING, MODEL, EFFECT, MATERIAL, PHYSCOLL, PHYSPRESET, TRACER, SOUND };

static int fields(u32 *ctx, int pass, const u32 *data, u32 count, int kind)
{
    u32 target = 0, i;
    if (kind == MODEL) target = 0x552cae;
    if (kind == EFFECT) target = 0x55278e;
    if (kind == MATERIAL) target = 0x551c90;
    if (kind == PHYSCOLL) target = 0x550d80; /* 0x48-byte collision map, client 0x48a0f0. */
    if (kind == PHYSPRESET) target = 0x550d9e; /* 0x44-byte preset, client 0x489e60. */
    if (kind == TRACER) target = 0x5526e1;
    if (target) target = loaded_address(target);
    for (i = 0; i < count; ++i) {
        if (kind == STRING) {
            if (data[i] == 0xffffffffu && !archive_string(ctx, pass)) return 0;
        } else if (kind == SOUND) {
            if (!archive_sound(ctx, data[i], pass)) return 0;
        } else if (!archive_asset(ctx, data[i], pass, target)) return 0;
    }
    return 1;
}

/* 0x492e30: the attachment field type is byte 0, not the old word at +4. */
int replay_attachment423(u32 *ctx, int pass, u32 *encoded)
{
    const u32 *h = (const u32 *)(ctx[32] + ctx[34]), *rows;
    u32 i, kind;
    if (!archive_reserve(ctx, 0, 12, 4, 1, pass, encoded) || !archive_push(ctx, 3) ||
        !fields(ctx, pass, h, 1, STRING)) return 0;
    if (h[2]) {
        rows = archive_bytes(ctx, h[1], 12, 4, pass);
        if (!rows) return 0;
        for (i = 0; i < h[1]; ++i) {
            kind = rows[i * 3] & 255;
            if (((kind < 16 && (kind < 4 || kind > 9)) || kind == 39 || kind == 42 || kind == 43) &&
                !fields(ctx, pass, rows + i * 3 + 2, 1, STRING)) return 0;
        }
    }
    return archive_pop(ctx);
}

/* REA 0x4912f0 adds an effect reference after the tracer material. */
int replay_tracer423(u32 *ctx, int pass, u32 *encoded)
{
    const u32 *h = (const u32 *)(ctx[32] + ctx[34]);
    if (!archive_reserve(ctx, 0, 0x74, 4, 1, pass, encoded) || !archive_push(ctx, 3)) return 0;
    if (!fields(ctx, pass, h, 1, STRING) || !fields(ctx, pass, h + 1, 1, MATERIAL) ||
        !fields(ctx, pass, h + 2, 1, EFFECT)) return 0;
    return archive_pop(ctx);
}

/* REA 0x4915b0: source-order pointer fields in the 0xe28-byte weapon.
 * Script-string IDs are in the fixed header, not additional source streams.
 */
int replay_weapon423(u32 *ctx, int pass, u32 *encoded)
{
    const u32 *h = (const u32 *)(ctx[32] + ctx[34]), *sounds;
    const unsigned short *counts = (const unsigned short *)((const char *)h + 0xd5c);
    u32 i;
    if (ctx[179] != 0x1a7 || !archive_reserve(ctx, 0, 0xe28, 4, 1, pass, encoded)) return 0;
    if (!archive_push(ctx, 3)) return 0;
#define F(index, count, kind) if (!fields(ctx, pass, h + (index), count, kind)) return 0
#define GRAPH(index, count) if (h[index] == 0xffffffffu && !archive_bytes(ctx, count, 8, 4, pass)) return 0
    F(0, 4, STRING); F(4, 10, MODEL);
    F(0x1e, 56, STRING); F(0x56, 56, STRING); F(0x8e, 56, STRING);
    F(0xee, 16, EFFECT); F(0x106, 16, EFFECT); F(0x126, 3, EFFECT);
    F(0x129, 53, SOUND);
    for (i = 0x15e; i <= 0x15f; ++i) {
        if (h[i] != 0xffffffffu) continue;
        sounds = archive_bytes(ctx, 31, 4, 4, pass);
        if (!sounds || !fields(ctx, pass, sounds, 31, SOUND)) return 0;
    }
    F(0x160, 4, EFFECT); F(0x164, 2, MATERIAL);
    F(0x19b, 6, MATERIAL); F(0x1a2, 1, MATERIAL); F(0x1a4, 1, MATERIAL);
    F(0x1a7, 4, MATERIAL);
    F(0x1ad, 1, STRING); F(0x1af, 1, STRING); F(0x1b3, 1, STRING);
    F(0x1f7, 4, MATERIAL); F(0x22c, 1, PHYSCOLL); F(0x22d, 1, PHYSPRESET);
    F(0x244, 1, MODEL); F(0x246, 2, EFFECT); F(0x248, 2, SOUND);
    F(0x28e, 2, EFFECT); F(0x296, 1, EFFECT); F(0x297, 1, SOUND); F(0x298, 3, EFFECT);
    F(0x2c9, 1, STRING); GRAPH(0x2cb, counts[0]);
    F(0x2ca, 1, STRING); GRAPH(0x2cc, counts[1]);
    F(0x2e0, 2, STRING); F(0x2e9, 2, STRING); F(0x311, 2, STRING);
    F(0x313, 2, TRACER); F(0x31b, 1, SOUND); F(0x31c, 1, EFFECT);
    F(0x31d, 1, STRING); F(0x321, 11, SOUND); F(0x33c, 6, SOUND);
    F(0x348, 1, STRING); F(0x34c, 2, STRING); F(0x34f, 3, MATERIAL);
    GRAPH(0x358, counts[0]); GRAPH(0x359, counts[1]);
    F(0x382, 1, STRING); F(0x386, 1, STRING);
#undef F
#undef GRAPH
    return archive_pop(ctx);
}

static int inline_array(u32 *ctx, int pass, const u32 *pair, u32 stride, u32 align)
{
    return pair[1] != 0xffffffffu ||
           archive_bytes(ctx, pair[0], stride, align, pass) != 0;
}

static int plane_refs(u32 *ctx, int pass, const u32 *nodes, u32 count)
{
    u32 i;
    for (i = 0; i < count; ++i)
        if (nodes[i * 2] == 0xffffffffu && !archive_bytes(ctx, 1, 20, 4, pass)) return 0;
    return 1;
}

static int collision_info_body(u32 *ctx, int pass, const u32 *info)
{
    const u32 *nodes;
    u32 i, count = info[12] & 0xffff;
    if (!info) return 0;
    if (!inline_array(ctx, pass, info, 20, 4)) return 0;
    if (info[3] == 0xffffffffu) {
        nodes = archive_bytes(ctx, info[2], 12, 4, pass);
        if (!nodes) return 0;
        for (i = 0; i < info[2]; ++i)
            if (nodes[i * 3] == 0xffffffffu && !archive_string(ctx, pass)) return 0;
    }
    if (info[5] == 0xffffffffu) {
        nodes = archive_bytes(ctx, info[4], 8, 4, pass);
        if (!nodes || !plane_refs(ctx, pass, nodes, info[4])) return 0;
    }
    if (!inline_array(ctx, pass, info + 6, 1, 1)) return 0;
    if (info[9] == 0xffffffffu) {
        nodes = archive_bytes(ctx, info[8], 20, 4, pass);
        if (!nodes) return 0;
        for (i = 0; i < info[8]; ++i) {
            const unsigned short *node = (const unsigned short *)(nodes + i * 5);
            if ((short)node[1] > 0 && nodes[i * 5 + 2] == 0xffffffffu &&
                !archive_bytes(ctx, node[1], 2, 2, pass)) return 0;
        }
    }
    if (!inline_array(ctx, pass, info + 10, 2, 2)) return 0;
    if (info[13] == 0xffffffffu) {
        nodes = archive_bytes(ctx, count, 36, 128, pass);
        if (!nodes) return 0;
        for (i = 0; i < count; ++i) {
            if (nodes[i * 9 + 1] == 0xffffffffu) {
                const u32 *side = archive_bytes(ctx, 1, 8, 4, pass);
                if (!side || !plane_refs(ctx, pass, side, 1)) return 0;
            }
            if (nodes[i * 9 + 2] == 0xffffffffu && !archive_bytes(ctx, 1, 1, 1, pass)) return 0;
        }
    }
    if (info[14] == 0xffffffffu && !archive_bytes(ctx, count, 24, 128, pass)) return 0;
    return info[15] != 0xffffffffu || archive_bytes(ctx, count, 4, 4, pass) != 0;
}

static int collision_info(u32 *ctx, int pass)
{
    const u32 *info = archive_bytes(ctx, 1, 64, 4, pass);
    return info && collision_info_body(ctx, pass, info);
}

static int collision_info_ref(u32 *ctx, int pass, u32 pointer)
{
    u32 alias;
    if (pointer < 0xfffffffeu) return 1;
    if (!archive_push(ctx, 0)) return 0;
    if (pointer == 0xfffffffeu && !archive_reserve(ctx, 3, 4, 4, 0, pass, &alias)) return 0;
    if (!collision_info(ctx, pass)) return 0;
    return archive_pop(ctx);
}

int replay_addon427(u32 *ctx, int pass, u32 *encoded)
{
    const u32 *header = (const u32 *)(ctx[32] + ctx[34]);
    const u32 *models;
    u32 i;
    if (ctx[179] != 0x1a7 || !archive_reserve(ctx, 0, 52, 4, 1, pass, encoded)) return 0;
    if (!archive_push(ctx, 3)) return 0;
    if (header[0] == 0xffffffffu && !archive_string(ctx, pass)) return 0;
    if (header[1] && !archive_bytes(ctx, header[2], 1, 1, pass)) return 0;
    if (!inline_array(ctx, pass, header + 3, 8, 4) ||
        !inline_array(ctx, pass, header + 5, 32, 4) ||
        !inline_array(ctx, pass, header + 7, 20, 4)) return 0;
    if (header[9] == 0xffffffffu && !collision_info(ctx, pass)) return 0;
    if (header[11]) {
        models = archive_bytes(ctx, header[10], 72, 4, pass);
        if (!models) return 0;
        for (i = 0; i < header[10]; ++i)
            if (models[i * 18 + 7] == 0xffffffffu && !collision_info(ctx, pass)) return 0;
    }
    if (header[12] && !archive_bytes(ctx, header[10], 60, 4, pass)) return 0;
    return archive_pop(ctx);
}

/* REA 0x48dea0 and its array consumers. Source parsing only: native collision
 * conversion and dynamic-entity installation remain separate acceptance steps.
 */
int replay_collision423(u32 *ctx, int pass, u32 *encoded)
{
    const u32 *h = (const u32 *)(ctx[32] + ctx[34]), *rows;
    u32 i, j, count, unused, base, source, *entry;
    if (ctx[179] != 0x1a7 || !archive_reserve(ctx, 0, 256, 4, 1, pass, encoded)) return 0;
    if (!archive_push(ctx, 3) || !fields(ctx, pass, h, 1, STRING)) return 0;
    if (!collision_info_body(ctx, pass, h + 2) || !collision_info_ref(ctx, pass, h[0x12])) return 0;
    if (h[0x14]) {
        rows = archive_bytes(ctx, h[0x13], 76, 4, pass);
        if (!rows) return 0;
        for (i = 0; i < h[0x13]; ++i)
            if (!fields(ctx, pass, rows + i * 19, 1, MODEL)) return 0;
    }
    if (h[0x16]) {
        rows = archive_bytes(ctx, h[0x15], 8, 4, pass);
        if (!rows || !plane_refs(ctx, pass, rows, h[0x15])) return 0;
    }
#define ARRAY(index, count, stride, align) if (h[index] && !archive_bytes(ctx, count, stride, align, pass)) return 0
    ARRAY(0x18, h[0x17], 40, 4); ARRAY(0x1a, h[0x19], 12, 4);
    ARRAY(0x1c, h[0x1b], 6, 2); ARRAY(0x1d, ((h[0x1b] * 3 + 31) >> 5), 4, 1);
    ARRAY(0x1f, h[0x1e], 28, 4);
    if (h[0x21]) {
        rows = archive_bytes(ctx, h[0x20], 12, 4, pass);
        if (!rows) return 0;
        for (i = 0; i < h[0x20]; ++i)
            if (rows[i * 3 + 2] == 0xffffffffu && !archive_bytes(ctx, 1, 28, 4, pass)) return 0;
    }
    ARRAY(0x23, h[0x22], 32, 16);
    if (h[0x25]) {
        rows = archive_bytes(ctx, h[0x24], 72, 4, pass);
        if (!rows) return 0;
        for (i = 0; i < h[0x24]; ++i)
            if (!collision_info_ref(ctx, pass, rows[i * 18 + 7])) return 0;
    }
    ARRAY(0x30, h[0x2f] & 0xffff, 28, 4);
    if (!archive_asset(ctx, h[0x26], pass, loaded_address(0x554ffe))) return 0;
    if (h[0x27]) {
        rows = archive_bytes(ctx, h[0x28] & 0xff, 20, 4, pass);
        if (!rows) return 0;
        for (i = 0; i < (h[0x28] & 0xff); ++i)
            if (!fields(ctx, pass, rows + i * 5, 1, STRING)) return 0;
    }
    if (!inline_array(ctx, pass, h + 0x29, 8, 4) ||
        !inline_array(ctx, pass, h + 0x2b, 32, 4) ||
        !inline_array(ctx, pass, h + 0x2d, 20, 4)) return 0;
    for (i = 0; i < 2; ++i) {
        count = (h[0x31] >> (i * 16)) & 0xffff;
        if (!h[0x32 + i]) continue;
        base = 0x30000001u + ((ctx[19] + 3) & ~3u);
        rows = archive_bytes(ctx, count, 92, 4, pass);
        if (!rows) return 0;
        /* Reference 0x5555d8 publishes this registry after its allocation pass. */
        if (ctx[168]) {
            if (pass) {
                if (ctx[171] >= ctx[172]) return 0;
                entry = (u32 *)ctx[170] + ctx[171] * 5;
                entry[0] = (u32)h; entry[1] = (u32)rows; entry[2] = i;
                entry[3] = count; entry[4] = base;
            }
            ++ctx[171];
        }
        for (j = 0; j < count; ++j) {
#define DEP(field, type, kind) \
            source = ctx[34]; \
            if (!fields(ctx, pass, rows + j * 23 + field, 1, kind)) return 0; \
            if (rows[j * 23 + field] >= 0xfffffffeu && \
                !archive_record_asset(ctx, type, base + j * 92 + field * 4, source, pass)) return 0
            DEP(8, 4, MODEL); DEP(10, 30, EFFECT); DEP(11, 0, PHYSPRESET);
#undef DEP
        }
    }
    for (j = 0; j < 3; ++j) {
        for (i = 0; i < 2; ++i) {
            count = (h[0x31] >> (i * 16)) & 0xffff;
            if (h[0x34 + j * 2 + i] &&
                !archive_reserve(ctx, 2, count * (j == 0 ? 32 : j == 1 ? 12 : 20), 4, 0, pass, &unused)) return 0;
        }
    }
#undef ARRAY
    return archive_pop(ctx);
}
