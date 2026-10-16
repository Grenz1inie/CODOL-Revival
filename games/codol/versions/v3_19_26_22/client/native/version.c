/* Forward Windows version APIs; queue the existing local match and mirror PS. */
#include "memory.h"

static char root[MAX_PATH];

static DWORD WINAPI worker(void *argument) {
    (void)argument;
    char marker[MAX_PATH], bridge_path[MAX_PATH], state_path[MAX_PATH];
    snprintf(marker, sizeof(marker), "%sarm-loopback319.txt", root);
    snprintf(bridge_path, sizeof(bridge_path), "%sclient_loopback319.dll", root);
    snprintf(state_path, sizeof(state_path), "%spredicted-ps319.bin", root);
    uint32_t sequence = 0, last_time = 0, ticks = 0;
    HMODULE bridge = NULL;
    int queued = 0;
    for (;;) {
        Sleep(20);
        if (!queued && ticks++ % 50 == 0) {
            FILE *file = fopen(marker, "r");
            unsigned long pid = 0;
            if (file) { fscanf(file, "%lu", &pid); fclose(file); }
            if (pid == GetCurrentProcessId()) {
                if (!bridge) bridge = LoadLibraryA(bridge_path);
                int (*begin)(void) = bridge ? (void *)GetProcAddress(bridge, "LocalMatchBegin319") : NULL;
                int result = begin ? begin() : -1;
                /* LocalMatchBegin319 only queues work; the verified frame hook
                   performs the transition on the client's main thread. */
                queued = result == 2;
                char log_path[MAX_PATH];
                snprintf(log_path, sizeof(log_path), "%sproxy319.log", root);
                file = fopen(log_path, "a");
                if (file) { fprintf(file, "begin_result=%d\n", result); fclose(file); }
            }
        }
        uint32_t index = read_word(0x82c3b58);
        if (index >= 65) continue;
        uint32_t pointer = read_word(0x1c1d188 + index * 4);
        if (!pointer) continue;
        uint32_t output[0x610 / 4] = {0};
        if (!read_bytes(pointer ^ 0xfbb2c97a, output + 3, 0x600) || !output[3] || output[3] == last_time) continue;
        output[0] = 0x39315350;
        output[1] = output[0x60c / 4] = ++sequence;
        output[2] = GetTickCount();
        FILE *file = fopen(state_path, "wb");
        if (file) {
            if (fwrite(output, 1, sizeof(output), file) == sizeof(output)) last_time = output[3];
            fclose(file);
        }
    }
}

BOOL WINAPI DllMain(HINSTANCE module, DWORD reason, LPVOID reserved) {
    (void)reserved;
    if (reason != DLL_PROCESS_ATTACH) return TRUE;
    DisableThreadLibraryCalls(module);
    char executable[MAX_PATH], path[MAX_PATH];
    if (!GetModuleFileNameA(NULL, executable, sizeof(executable))) return TRUE;
    char *name = strrchr(executable, '\\');
    if (!name || _stricmp(name + 1, "codoMP_client_shipRetail.exe")) return TRUE;
    *name = 0;
    snprintf(path, sizeof(path), "%s\\codol319-root.txt", executable);
    FILE *file = fopen(path, "r");
    if (!file) return TRUE;
    char *read = fgets(root, sizeof(root), file);
    fclose(file);
    if (!read) return TRUE;
    root[strcspn(root, "\r\n")] = 0;
    size_t length = strlen(root);
    if (!length || root[length - 1] != '\\') return TRUE;
    HANDLE thread = CreateThread(NULL, 0, worker, NULL, 0, NULL);
    if (thread) CloseHandle(thread);
    return TRUE;
}
