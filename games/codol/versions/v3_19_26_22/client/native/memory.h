#ifndef CODOL319_MEMORY_H
#define CODOL319_MEMORY_H
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static inline int read_bytes(uintptr_t address, void *destination, size_t length) {
    SIZE_T count = 0;
    return ReadProcessMemory(GetCurrentProcess(), (const void *)address, destination, length, &count) && count == length;
}
static inline uint32_t read_word(uintptr_t address) {
    uint32_t value = 0;
    read_bytes(address, &value, 4);
    return value;
}
static inline int matches(uintptr_t address, const void *bytes, size_t length) {
    unsigned char buffer[32];
    return length <= sizeof(buffer) && read_bytes(address, buffer, length) && !memcmp(buffer, bytes, length);
}
static inline int patch_bytes(uintptr_t address, const void *original, const void *replacement, size_t length) {
    if (!matches(address, original, length)) return 0;
    DWORD protection, previous;
    if (!VirtualProtect((void *)address, length, PAGE_EXECUTE_READWRITE, &protection)) return 0;
    memcpy((void *)address, replacement, length);
    int flushed = FlushInstructionCache(GetCurrentProcess(), (void *)address, length);
    return VirtualProtect((void *)address, length, protection, &previous) && flushed;
}
#endif
