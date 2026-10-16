/* Controlled child: consumes the same TCLS records and protected patch pages. */
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

unsigned char reserved_game_pages[16 * 1024 * 1024];

static const unsigned char *record(const unsigned char *base, unsigned table, unsigned key) {
    unsigned offset = *(const uint32_t *)(base + table + key * 4);
    return base + offset;
}

int main(void) {
    const uintptr_t addresses[] = {0xd5a2cc, 0x62136e, 0xbae861};
    const unsigned char *original[] = {(const unsigned char *)"https://%s:%d/auth/",
        (const unsigned char *)"\x8a\x45\x08", (const unsigned char *)"\xb8\x02\x0c\x00\x00"};
    const unsigned char *expected[] = {(const unsigned char *)"http://%s:%d/auth/\0",
        (const unsigned char *)"\x30\xc0\x90", (const unsigned char *)"\xb8\x04\x0c\x00\x00"};
    const unsigned sizes[] = {19, 3, 5};
    for (unsigned i = 0; i < 3; ++i) {
        if (addresses[i] < (uintptr_t)reserved_game_pages ||
            addresses[i] + sizes[i] > (uintptr_t)reserved_game_pages + sizeof(reserved_game_pages)) return 10;
        void *page = (void *)(addresses[i] & ~(uintptr_t)0xfff);
        memcpy((void *)addresses[i], original[i], sizes[i]);
        DWORD previous;
        if (!VirtualProtect(page, 0x1000, PAGE_EXECUTE_READ, &previous)) return 11;
    }
    char name[80];
    sprintf(name, "TCLS_SHAREDMEMEMORY%lu", GetCurrentProcessId());
    HANDLE map = NULL;
    for (unsigned i = 0; i < 200 && !map; ++i) {
        Sleep(50);
        map = OpenFileMappingA(FILE_MAP_READ, FALSE, name);
    }
    if (!map) return 12;
    const unsigned char *data = MapViewOfFile(map, FILE_MAP_READ, 0, 0, 0x100000);
    if (!data) return 13;
    for (unsigned attempt = 0; attempt < 100; ++attempt) {
        Sleep(50);
        if (*(const uint32_t *)data != 64) continue;
        int ready = 1;
        for (unsigned i = 0; i < 3; ++i)
            ready &= memcmp((void *)addresses[i], expected[i], sizes[i]) == 0;
        if (!ready) continue;
        const unsigned char *uid = record(data, 0, 2);
        const unsigned char *endpoint = record(data, 0, 7);
        unsigned group_index = *(const uint32_t *)(data + 0x50);
        unsigned group = *(const uint32_t *)(data + group_index);
        const unsigned char *port = record(data, group, 5);
        if (*(const uint32_t *)uid != 4 || *(const uint32_t *)(uid + 4) != 1000001 ||
            strcmp((const char *)endpoint + 4, "127.0.0.1:31900") ||
            *(const uint32_t *)(port + 4) != 31900) return 14;
        for (unsigned i = 0; i < 3; ++i) {
            MEMORY_BASIC_INFORMATION info;
            if (!VirtualQuery((void *)addresses[i], &info, sizeof(info)) ||
                info.Protect != PAGE_EXECUTE_READ) return 15;
        }
        UnmapViewOfFile(data);
        CloseHandle(map);
        return 0;
    }
    return 16;
}
