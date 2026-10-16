/* A separate x86 process with controlled client pages; no original game or old DLL. */
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

unsigned char game_pages[224 * 1024 * 1024];
int capture_ncs(void);
static void *at(uintptr_t address, unsigned length) {
    if (address < (uintptr_t)game_pages || address + length > (uintptr_t)game_pages + sizeof(game_pages)) ExitProcess(20);
    return (void *)address;
}
static void word(uintptr_t address, uint32_t value) { memcpy(at(address, 4), &value, 4); }

int main(int argc, char **argv) {
    if (argc != 2) return 21;
    char path[MAX_PATH];
    snprintf(path, sizeof(path), "%s\\client_loopback319.dll", argv[1]);
    HMODULE bridge = LoadLibraryA(path);
    if (!bridge) { fprintf(stderr, "load bridge: %lu\n", GetLastError()); return 22; }
    int (*begin)(void) = (int (*)(void))GetProcAddress(bridge, "LocalMatchBegin319");
    if (!begin || begin() != -10) return 23;
    word(0x3381398, 1);
    *(unsigned char *)at(0x76446a1, 1) = 1;
    if (begin() != -11) return 24;
    const unsigned char frontend[] = {0x55,0x8b,0xec,0x83,0xec,0x14,0x53,0x56,0x57,0x33,0xdb,0x53,
                                     0xbf,0xd8,0x41,0x73,0x0c,0xe8,0xba,0x07,0x00,0x00};
    memcpy(at(0x616df0, sizeof(frontend)), frontend, sizeof(frontend));
    if (begin() != -14) return 25;
    word(0x7886e68, GetCurrentThreadId());
    if (begin() != -15) return 26;
    const unsigned char frame[] = {0xe8,0x8b,0xf7,0xff,0xff};
    memcpy(at(0x4fea90, 5), frame, 5);
    if (begin() != 2 || *(unsigned char *)at(0x4fea90, 1) != 0xe8 || !memcmp((void *)0x4fea90, frame, 5)) return 27;
    if (begin() != 0) return 31;
    /* Do not execute synthetic game functions. The fixture checks queueing guards. */
    if (capture_ncs()) return 32;
    const char *strings[][3] = {{"runtime_a", "runtime_b"}, {"runtime_c"}, {"runtime_d"},
        {"alpha", "shared", "shared"}, {"shared", "beta", "gamma"}, {"skip_me"}};
    const char *names[] = {"runtime_20", "runtime_21", "runtime_22", "strings/common_a", "strings/common_b", "strings/skipped"};
    const unsigned types[] = {20, 21, 22, 0, 0, 15}, counts[] = {2, 1, 1, 3, 3, 1};
    const uintptr_t runtime[] = {0x77e08d4, 0x77e0de8, 0x77e0dfc};
    uint32_t descriptors[6][5];
    for (unsigned i = 0; i < 6; ++i) {
        uint32_t value[] = {(uintptr_t)names[i], types[i], i < 3 ? 0 : 1, counts[i], (uintptr_t)strings[i]};
        memcpy(descriptors[i], value, sizeof(value));
        if (i < 3) memcpy(at(runtime[i], sizeof(value)), value, sizeof(value));
        else {
            uint32_t node[] = {44, 0, (uintptr_t)descriptors[i], 0, 0, i == 5 ? 0 : i - 1, 0};
            memcpy(at(0x239b120 + (i - 2) * 28, sizeof(node)), node, sizeof(node));
        }
    }
    word(0x1e2d338, 1);
    word(0x77db834, 0x12345678);
    if (!capture_ncs()) return 33;
    descriptors[3][3] = 16385;
    if (capture_ncs()) return 34;
    word(0x82c3b58, 0);
    word(0x1c1d188, 0x05000000 ^ 0xfbb2c97a);
    word(0x05000000, 0x12345678);
    snprintf(path, sizeof(path), "%s\\version.dll", argv[1]);
    HMODULE proxy = LoadLibraryA(path);
    if (!proxy) return 28;
    DWORD (WINAPI *size)(LPCWSTR, LPDWORD) = (void *)GetProcAddress(proxy, "GetFileVersionInfoSizeW");
    wchar_t system[MAX_PATH];
    GetSystemDirectoryW(system, MAX_PATH);
    wcscat(system, L"\\version.dll");
    DWORD ignored;
    if (!size || !size(system, &ignored)) return 29;
    snprintf(path, sizeof(path), "%s\\predicted-ps319.bin", argv[1]);
    for (int i = 0; i < 100; ++i) {
        Sleep(20);
        FILE *file = fopen(path, "rb");
        if (file) { fclose(file); return 0; }
    }
    return 30;
}
