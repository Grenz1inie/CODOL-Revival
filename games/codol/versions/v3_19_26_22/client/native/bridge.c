/* 3.19-only local transport. Addresses and guards recovered from ffc616e8... . */
#include <winsock2.h>
#include <stdlib.h>
#include "memory.h"

int capture_ncs(void);
static SOCKET connection = INVALID_SOCKET;
static LONG request_state;
static int armed, captured;
static unsigned char deferred[2048];
static int deferred_size;
void *codol_frame_original = (void *)0x4fe220;

static void log_result(const char *message, int result) {
    FILE *file = fopen("bridge319.log", "a");
    if (file) { fprintf(file, "%s=%d\n", message, result); fclose(file); }
}

static int preconditions(void) {
    unsigned char gate = 0;
    return read_bytes(0x76446a1, &gate, 1) && gate == 1 &&
           read_word(0x76446b0) == 0 && read_word(0x3381398) == 1;
}

static int frontend_matches(void) {
    const unsigned char expected[] = {0x55,0x8b,0xec,0x83,0xec,0x14,0x53,0x56,0x57,0x33,0xdb,0x53,
                                     0xbf,0xd8,0x41,0x73,0x0c,0xe8,0xba,0x07,0x00,0x00};
    return matches(0x616df0, expected, sizeof(expected));
}

static int callback_ready(void) {
    static const uint32_t getters[] = {0x4017c0,0x4018d0,0x4019d0,0x401ae0,0x401c00,0x401d10,
        0x401e20,0x401f40,0x402050,0x402170,0x402290,0x4023b0,0x4024d0,0x4025f0,0x402710,
        0x402820,0x402940,0x402a60,0x402b70,0x402c80,0x402d90,0x402eb0,0x402fd0,0x4030f0,
        0x403210,0x403330,0x403430,0x403540,0x403660,0x403780,0x4038a0,0x4039b0,0x403ad0,0x403bf0};
    uint32_t encoded, key, slot;
    if (!read_bytes(0x76638f4, &encoded, 4) || !read_bytes(0xe60b78, &key, 4)) return 0;
    uint32_t object = encoded ^ 0x6891d1c7;
    if (object < 0x10000 || object > 0xffffffcf || !read_bytes(object + 0x30, &slot, 4)) return 0;
    uint32_t target = (object + 0x2c) ^ slot ^ key;
    int known = 0;
    for (unsigned i = 0; i < sizeof(getters) / sizeof(*getters); ++i) known |= target == getters[i];
    MEMORY_BASIC_INFORMATION info;
    if (!known || !VirtualQuery((void *)target, &info, sizeof(info)) ||
        info.State != MEM_COMMIT || info.Protect & PAGE_GUARD) return 0;
    DWORD protection = info.Protect & 255;
    return protection == PAGE_EXECUTE || protection == PAGE_EXECUTE_READ ||
           protection == PAGE_EXECUTE_READWRITE || protection == PAGE_EXECUTE_WRITECOPY;
}

__attribute__((used, noinline)) int bridge_send(int local_client, const unsigned char *data, int length) {
    if (local_client || connection == INVALID_SOCKET || !data || length < 1 || length > 65507) return 0;
    if (!armed) {
        if (length <= (int)sizeof(deferred)) { memcpy(deferred, data, length); deferred_size = length; }
        return 1;
    }
    if (send(connection, (const char *)data, length, 0) != length) return 0;
    if (!captured && length >= 4 && *(const uint32_t *)data != UINT32_MAX) {
        captured = capture_ncs();
        log_result("ncs_capture", captured);
    }
    return 1;
}

__attribute__((used, noinline)) int bridge_receive(int local_client, uint32_t *address, uint32_t *message) {
    if (local_client || connection == INVALID_SOCKET || !address || !message || !message[2] ||
        !message[4] || message[4] > 0x20000) return 0;
    char *data = (char *)message[2];
    int length = recv(connection, data, message[4], 0);
    if (length <= 0) return 0;
    if (length > 16 && !memcmp(data, "\xff\xff\xff\xffstatResponse", 16) &&
        (data[16] == 0 || data[16] == ' ')) {
        char number[64] = {0};
        memcpy(number, data + 16, length - 16 < 63 ? length - 16 : 63);
        if (!strtol(number, NULL, 10) && !callback_ready()) return 0;
    }
    message[5] = length;
    memset(address, 0, 24);
    address[0] = 2;
    address[5] = 0x9d;
    return 1;
}

__attribute__((naked)) static void send_entry(void) {
    __asm__("push %ebp\nmov %esp,%ebp\npush %edi\npush 12(%ebp)\npush 8(%ebp)\n"
            "call _bridge_send\nadd $12,%esp\npop %ebp\nret");
}
__attribute__((naked)) static void receive_entry(void) {
    __asm__("push %ebp\nmov %esp,%ebp\npush 12(%ebp)\npush %esi\npush 8(%ebp)\n"
            "call _bridge_receive\nadd $12,%esp\npop %ebp\nret");
}

static int hook(uintptr_t address, void *target) {
    const unsigned char expected[] = {0x55,0x8b,0xec,0x53,0x8b,0x5d,0x08};
    unsigned char replacement[] = {0xe9,0,0,0,0,0x90,0x90};
    uint32_t displacement = (uintptr_t)target - address - 5;
    memcpy(replacement + 1, &displacement, 4);
    return patch_bytes(address, expected, replacement, 7);
}

static int connect_local(void) {
    if (!preconditions()) return -10;
    if (!frontend_matches()) return -11;
    const unsigned char ui[] = {0x55,0x8b,0xec,0x83,0xec,0x0c,0x53,0x56,0x57,0x68,0x58,0x5f,0xdb,0x00};
    if (!matches(0x4fe830, ui, sizeof(ui))) return -16;
    WSADATA data;
    if (WSAStartup(MAKEWORD(2, 2), &data)) return -2;
    connection = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    struct sockaddr_in address = {0};
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    int result = -3;
    if (connection == INVALID_SOCKET) goto failed;
    result = -4;
    if (bind(connection, (struct sockaddr *)&address, sizeof(address))) goto failed;
    address.sin_port = htons(28970);
    result = -5;
    if (connect(connection, (struct sockaddr *)&address, sizeof(address))) goto failed;
    u_long nonblocking = 1;
    if (ioctlsocket(connection, FIONBIO, &nonblocking)) goto failed;
    result = -7;
    if (!hook(0x6750a0, send_entry)) goto failed;
    result = -8;
    if (!hook(0x674fe0, receive_entry)) goto failed;
    ((void (*)(void))0x4fe830)();
    ((void (*)(void))0x616df0)();
    unsigned char initialized = 1, active = 1, pending = 1;
    result = -12;
    if (!read_bytes(0xc7341db, &initialized, 1) || !read_bytes(0xc7341dc, &active, 1) ||
        !read_bytes(0xc7341d8, &pending, 1) || initialized || active || pending) goto failed;
    ((void (*)(void))0x5be730)();
    result = -13;
    if (!callback_ready() || read_word(0x76446b0) != 4) goto failed;
    armed = 1;
    if (deferred_size) {
        if (send(connection, (const char *)deferred, deferred_size, 0) != deferred_size) goto failed;
        deferred_size = 0;
    }
    return 1;
failed:
    armed = 0;
    if (connection != INVALID_SOCKET) closesocket(connection);
    connection = INVALID_SOCKET;
    WSACleanup();
    return result;
}

__attribute__((used, noinline)) void bridge_frame(void) {
    if (GetCurrentThreadId() == read_word(0x7886e68) && InterlockedCompareExchange(&request_state, 2, 1) == 1) {
        log_result("main_frame_result", connect_local());
        InterlockedExchange(&request_state, 3);
    }
}

__attribute__((naked)) static void frame_entry(void) {
    __asm__("pushfl\npushal\nmov %esp,%ebp\nand $-16,%esp\nsub $512,%esp\nfxsave (%esp)\n"
            "cld\ncall _bridge_frame\nfxrstor (%esp)\nmov %ebp,%esp\npopal\npopfl\njmp *_codol_frame_original");
}

__declspec(dllexport) int LocalMatchBegin319(void) {
    if ((uintptr_t)GetModuleHandleA(NULL) != 0x400000) return -1;
    if (InterlockedCompareExchange(&request_state, 0, 0)) return 0;
    if (!preconditions()) return -10;
    if (!frontend_matches()) return -11;
    if (!read_word(0x7886e68)) return -14;
    const unsigned char original[] = {0xe8,0x8b,0xf7,0xff,0xff};
    unsigned char replacement[] = {0xe8,0,0,0,0};
    uint32_t displacement = (uintptr_t)frame_entry - 0x4fea95;
    memcpy(replacement + 1, &displacement, 4);
    if (!patch_bytes(0x4fea90, original, replacement, 5)) return -15;
    InterlockedExchange(&request_state, 1);
    return 2;
}
