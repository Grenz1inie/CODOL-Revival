/* FF423 type 45, client 0x496ca0 and its 0x496010..0x496c30 readers.
 * Preserve all source arrays and block allocations; this publishes no gameplay
 * implementation of the catalog. Strings retain their original alias rules.
 */
typedef unsigned int u32;
#define REGS __attribute__((regparm(3)))
extern int REGS archive_reserve(u32 *, u32, u32, u32, int, int, u32 *);
extern const u32 *REGS archive_bytes(u32 *, u32, u32, u32, int);
extern int REGS archive_string(u32 *, int);
extern int archive_push(u32 *, u32);
extern int archive_pop(u32 *);

/* Extend only the dispatcher's range branch. Keep its original validation,
 * two-pass replay, exact consumption check, and rejection of unknown types.
 */
__asm__(".text\n.global _route_asset45\n_route_asset45:\n"
        "cmpl $44, %eax\njbe _archive_dispatch_table\n"
        "cmpl $45, %eax\njne _archive_unknown_asset\n"
        "call 1f\n1: pop %esi\naddl $(_replay_catalog423 - 1b), %esi\n"
        "jmp _archive_selected_asset\n");

__asm__(".text\n.global _route_shared_asset\n_route_shared_asset:\n"
        "cmpl $0xfffffffd, -0x304(%ebp)\nja _archive_inline_asset\n"
        "pushl -0x300(%ebp)\npushl -0x304(%ebp)\npushl -0x2f4(%ebp)\n"
        "pushl 0x10(%ebp)\ncall _validate_shared_asset423\naddl $16, %esp\n"
        "movl -8(%ebp), %esi\nmovl -4(%ebp), %edi\nmovl -12(%ebp), %ebx\n"
        "leave\nret\n");

int validate_shared_asset423(u32 *ctx, u32 kind, u32 pointer, u32 size)
{
    const u32 *rows = (const u32 *)ctx[165];
    u32 i;
    if (ctx[179] != 423 || size || !pointer || (pointer - 1) >> 28 != 3 ||
        !rows || ctx[166] > ctx[167]) return -1;
    /* The runtime alias resolver binary-searches only after ReplayZone sorts
     * this registry. During replay a parent is recorded after its children. */
    for (i = 0; i < ctx[166]; ++i)
        if (rows[i * 5] == pointer && rows[i * 5 + 1] == kind && rows[i * 5 + 4] == 423)
            return 1;
    return -1;
}

static int strings(u32 *ctx, int pass, const u32 *p, u32 count)
{
    u32 i;
    for (i = 0; i < count; ++i)
        if (p[i] == 0xffffffffu && !archive_string(ctx, pass)) return 0;
    return 1;
}

static int indices(u32 *ctx, int pass, u32 pointer, u32 count, u32 stride, u32 align)
{
    return !pointer || archive_bytes(ctx, count, stride, align, pass) != 0;
}

/* Each case is a client record reader; nested arrays follow source order. */
static int records(u32 *ctx, int pass, u32 pointer, u32 count, u32 stride, int kind)
{
    const u32 *p, *q, *nested;
    u32 i, j, n;
    if (!pointer) return 1;
    p = archive_bytes(ctx, count, stride, 4, pass);
    if (!p) return 0;
    for (i = 0; i < count; ++i) {
        q = (const u32 *)((const char *)p + i * stride);
        if (kind == 0 && !strings(ctx, pass, q + 1, 1)) return 0; /* 0x496010 */
        if (kind == 1) { /* 0x4961e0 */
            if (!strings(ctx, pass, q + 3, 4) ||
                !indices(ctx, pass, q[9], q[8] >> 16, 2, 2)) return 0;
        }
        if (kind == 2) { /* 0x496410 */
            if (!indices(ctx, pass, q[3], (q[2] >> 16) & 255, 4, 4) ||
                !indices(ctx, pass, q[5], q[4] & 255, 2, 2)) return 0;
        }
        if (kind == 3 && !strings(ctx, pass, q, 3)) return 0;
        if (kind == 4 && !indices(ctx, pass, q[2], q[1] & 65535, 2, 2)) return 0;
        if (kind == 5 && !indices(ctx, pass, q[1], q[0], 2, 2)) return 0;
        if (kind == 6) { /* 0x496820 / 0x496760 */
            if (!strings(ctx, pass, q + 4, 4)) return 0;
            n = q[17] & 65535;
            if (q[18]) {
                nested = archive_bytes(ctx, n, 12, 4, pass);
                if (!nested) return 0;
                for (j = 0; j < n; ++j)
                    if (!strings(ctx, pass, nested + j * 3 + 1, 1)) return 0;
            }
        }
        if (kind == 7) { /* 0x496930 */
            if (!strings(ctx, pass, q + 1, 1)) return 0;
            if (q[2]) {
                nested = archive_bytes(ctx, q[3], 4, 4, pass);
                if (!nested || !strings(ctx, pass, nested, q[3])) return 0;
            }
        }
        if (kind == 8 && !indices(ctx, pass, q[9], q[8], 2, 2)) return 0;
        if (kind == 9 && !strings(ctx, pass, q + 1, 4)) return 0;
    }
    return 1;
}

int replay_catalog423(u32 *ctx, int pass, u32 *encoded)
{
    const u32 *h = (const u32 *)(ctx[32] + ctx[34]);
    u32 i;
    if (ctx[179] != 423 || !archive_reserve(ctx, 0, 0x2fa4, 4, 1, pass, encoded) ||
        !archive_push(ctx, 3) || !strings(ctx, pass, h, 1)) return 0;
#define R(p, n, stride, kind) if (!records(ctx, pass, h[p], h[n], stride, kind)) return 0
#define I(p, n, stride, align) if (!indices(ctx, pass, h[p], h[n], stride, align)) return 0
    R(1, 2, 8, 0); I(3, 4, 2, 2); R(5, 6, 40, 1); I(7, 8, 2, 2);
    I(0x2a, 0x2b, 2, 2);
    R(0x9f0, 0x9f1, 24, 2); R(0x9f2, 0x9f3, 12, 3);
    I(0x9f4, 0x9f5, 2, 2); I(0x9f6, 0x9f7, 24, 4); I(0x9f8, 0x9f9, 2, 2);
    R(0x9fa, 0x9fb, 12, 4);
    /* 12 inline groups of 20 index lists; their headers are already consumed. */
    for (i = 0x9fc; i < 0xbdc; i += 2)
        if (!indices(ctx, pass, h[i + 1], h[i], 2, 2)) return 0;
    R(0xbdc, 0xbde, 8, 5); R(0xbdd, 0xbde, 8, 5);
    R(0xbdf, 0xbe0, 76, 6); I(0xbe1, 0xbe2, 14, 4);
    R(0xbe3, 0xbe4, 16, 7); R(0xbe5, 0xbe6, 40, 8); R(0xbe7, 0xbe8, 20, 9);
#undef R
#undef I
    return archive_pop(ctx);
}
