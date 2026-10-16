/* Current-process NCS export; data comes from this client's loaded resources. */
#include <stdlib.h>
#include "memory.h"

static int text_hex(FILE *file, uint32_t address) {
    for (unsigned i = 0; i < 2048; ++i) {
        unsigned char value;
        if (!read_bytes(address + i, &value, 1)) return 0;
        if (!value) return 1;
        fprintf(file, "%02x", value);
    }
    return 0;
}

static int asset(FILE *file, const char *origin, uint32_t address) {
    uint32_t value[5];
    if (!read_bytes(address, value, sizeof(value)) || value[1] >= 23 || value[3] > 16384) return 0;
    fprintf(file, "asset origin=%s address=%08x name_hex=", origin, address);
    if (!text_hex(file, value[0])) return 0;
    fprintf(file, " type=%u source=%u count=%u\n", value[1], value[2], value[3]);
    for (unsigned i = 0; i < value[3]; ++i) {
        uint32_t pointer;
        if (!read_bytes(value[4] + i * 4, &pointer, 4)) return 0;
        fprintf(file, "string index=%u hex=", i);
        if (!text_hex(file, pointer)) return 0;
        fputc('\n', file);
    }
    return 1;
}

int capture_ncs(void) {
    char final[80], temporary[84];
    snprintf(final, sizeof(final), "config319-%lu-first-netchan.txt", GetCurrentProcessId());
    snprintf(temporary, sizeof(temporary), "%s.tmp", final);
    FILE *file = fopen(temporary, "wb");
    if (!file) return 0;
    int complete = 0;
    unsigned nodes = 0, assets = 0;
    uint32_t *heads = calloc(120000, 4);
    unsigned char *seen = calloc(150000, 1);
    if (!heads || !seen) goto finish;
    const uint32_t globals[] = {0x77db42c,0x77d8240,0x77db834,0x77d8244,0x7798914,0x77e1760,0x77e1764};
    for (unsigned i = 0; i < sizeof(globals) / sizeof(*globals); ++i) {
        uint32_t value;
        if (!read_bytes(globals[i], &value, 4)) goto finish;
        fprintf(file, "global address=%08x value=%08x readable=1\n", globals[i], value);
    }
    if (!read_bytes(0x1e2d338, heads, 480000)) goto finish;
    for (unsigned i = 0; i < 120000; ++i) {
        uint32_t index = heads[i];
        while (index && index < 150000 && !seen[index]) {
            uint32_t node[7];
            seen[index] = 1;
            if (!read_bytes(0x239b120 + index * 28, node, sizeof(node))) goto finish;
            ++nodes;
            if (node[0] == 44) {
                if (!asset(file, "database", node[2])) goto finish;
                ++assets;
            }
            index = node[5];
        }
    }
    const uint32_t runtime[] = {0x77e08d4,0x77e0de8,0x77e0dfc};
    for (unsigned i = 0; i < 3; ++i) if (!asset(file, "runtime", runtime[i])) goto finish;
    fprintf(file, "database_nodes=%u assets=%u\n", nodes, assets);
    complete = !ferror(file);
finish:
    free(heads);
    free(seen);
    if (fclose(file)) complete = 0;
    if (complete) complete = MoveFileExA(temporary, final, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) != 0;
    if (!complete) DeleteFileA(temporary);
    return complete;
}
