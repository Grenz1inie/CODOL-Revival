/* Runtime-only adapters, using the current client's resource semantics. */
typedef unsigned int u32;
#define REGS __attribute__((regparm(3)))
extern u32 REGS native_find_definition(u32, const char *, u32 *);
extern int native_printf(const char *, ...);
extern int REGS native_read_map_body(const void *, u32, u32, u32 *);
extern int REGS native_runtime_dynamic(const char *, void *, void *);
extern int native_load_addon(const char *, u32 *);
extern void native_free_entities(u32 *);

u32 REGS find_dynamic_definition423(u32 kind, const char *name, u32 *asset)
{
    u32 found = native_find_definition(kind, name, asset);
    const unsigned char *source;
    const char *fallback, *message;
    if (found || kind != 0 || asset[0] != 0 || asset[3] != 423 ||
        asset[2] < 70 || !asset[1]) return found;
    source = (const unsigned char *)asset[1];
    /* Only an explicit inline external reference may use this rule. Unknown
     * types, malformed definitions and missing default templates still fail.
     * Client 0x49e570 clones type 0's "default" (table 0xce0540); callback
     * 0xce05f8[0] is null, so the physics fields are copied unchanged. */
    if (*(const u32 *)source != 0xffffffffu || source[68] != ',' ||
        name != (const char *)source + 69 || !*name) return 0;
    /* PC-relative literals preserve ASLR without adding PE relocations. */
    __asm__("call 1f\n.asciz \"default\"\n1: pop %0" : "=r"(fallback));
    found = native_find_definition(0, fallback, asset);
    if (!found) return 0;
    __asm__("call 1f\n.asciz \"runtime_preset default=%%s requested=%%s\\n\"\n1: pop %0"
            : "=r"(message));
    native_printf(message, fallback, name);
    return found;
}

int read_addon_entities423(const unsigned char *source, u32 size, u32 *out)
{
    const u32 *h = (const u32 *)source;
    u32 pos = 52, i, count, stride;
    if (!source || !out || size < 52 || size > 0x20000000 ||
        h[0] != 0xffffffffu || h[10] || h[11] || h[12]) return 0;
    while (pos < size && source[pos]) ++pos;
    if (pos == size) return 0;
    ++pos;
    if (h[2] > size - pos) return 0;
    pos += h[2];
    for (i = 0; i < 3; ++i) {
        count = h[3 + i * 2];
        stride = i == 0 ? 8 : i == 1 ? 32 : 20;
        if (count > (size - pos) / stride) return 0;
        pos += count * stride;
    }
    /* First-map cinfo contains only one empty leaf node. There are no added
     * brushes/submodels to publish. Reject any unconverted geometry rather
     * than silently discarding it when using the legacy entity consumer. */
    if (h[9] == 0xffffffffu) {
        if (size - pos != 84) return 0;
        for (i = 0; i < 84; ++i) {
            unsigned char expected = i == 32 ? 1 : i >= 36 && i < 40 ? 255 : 0;
            if (source[pos + i] != expected) return 0;
        }
    } else if (h[9] || pos != size) return 0;
    /* h[10]==0 also means no legacy stage list. The native reader validates
     * entity termination, trigger indices, finite bounds and owned copies. */
    return native_read_map_body(source, size, 52, out);
}

int REGS probe_story_dynamic423(const char *map, void *collision, void *context)
{
    const char *story, *message;
    u32 entities[14] = {0};
    int ok;
    if (!native_runtime_dynamic(map, collision, context)) return 0;
    __asm__("call 1f\n.asciz \"coop_training_mp_cargoship\"\n1: pop %0" : "=r"(story));
    ok = native_load_addon(story, entities) == 1;
    __asm__("call 1f\n.asciz \"runtime_story_addon ok=%%d text_bytes=%%u triggers=%%u hulls=%%u slabs=%%u\\n\"\n1: pop %0"
            : "=r"(message));
    native_printf(message, ok, entities[4], entities[6], entities[7], entities[8]);
    native_free_entities(entities);
    return ok;
}
