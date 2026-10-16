/* IFS2.dll (5b0324e0...) read interface recovered with REA.
 * Only archive copies belong here. Output uses numeric names, never archive paths.
 * Build x86: gcc -O2 -Wall -static-libgcc -o <experiment>/ifs-read.exe tools/ifs-read.c
 * ABI evidence: story-ifs-{open,read,close}-abi.json and archive-interface.json.
 */
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef void *(__stdcall *Create)(void *);
typedef void (__stdcall *Destroy)(void **);
typedef void *(__thiscall *Open)(void *, const char *, int);
typedef void (__thiscall *Close)(void *, void *, int);
#define SLOT(obj, n, type) ((type)(*(void ***)(obj))[n])

int main(int argc, char **argv) {
    if (argc != 4 && argc != 5) {
        fprintf(stderr, "usage: ifs-read DLL ARCHIVE_COPY EXISTING_OUTPUT_DIR|--list [PREFIX]\n");
        return 2;
    }
    fprintf(stderr, "Loading IFS DLL\n");
    HMODULE dll = LoadLibraryExA(argv[1], NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!dll) { fprintf(stderr, "LoadLibrary: %lu\n", GetLastError()); return 3; }
    Create create = (Create)GetProcAddress(dll, "CreateIFSLibDll");
    Destroy destroy = (Destroy)GetProcAddress(dll, "DestoryIFSLibDll");
    if (!create || !destroy) { FreeLibrary(dll); return 4; }
    fprintf(stderr, "Creating IFS library\n");
    void *lib = create(NULL);
    if (!lib) { FreeLibrary(dll); return 5; }
    fprintf(stderr, "IFS library created\n");
    void *archive = SLOT(lib, 0, Open)(lib, argv[2], 0);
    if (!archive) {
        fprintf(stderr, "OpenArchive: %lu\n", GetLastError());
        destroy(&lib); FreeLibrary(dll); return 6;
    }
    /* OpenArchive parsed/verified BET; these are its own entries, before the
     * optional cross-archive file-ID table is initialized. Evidence: 100177e0.
     * This extractor supports stored payloads only, as observed in first-map IFS.
     */
    unsigned count = *(unsigned *)((char *)archive + 0x134);
    uint8_t *entries = *(uint8_t **)((char *)archive + 0x68);
    FILE *input = fopen(argv[2], "rb");
    int result = 0;
    if (!input) result = 7;
    for (unsigned i = 0; !result && i < count; ++i) {
        uint32_t *entry = (uint32_t *)(entries + i * 0x80);
        unsigned flags = entry[9], size = entry[7];
        if (!(flags & 0x80000000u) || (flags & 0x08000000u)) continue;
        const char *name = (const char *)entry[14];
        if (name && (!strcmp(name, "(listfile)") || !strcmp(name, "(attributes)"))) continue;
        if (!name || flags != 0x80000000u || size != entry[8] || entry[3] ||
            size > 512u * 1024u * 1024u) {
            fprintf(stderr, "Unsupported entry %u %s flags=%x\n", i, name ? name : "(null)", flags); result = 8; break;
        }
        /* Retain the listfile as well: its original filename casing supplies
         * the AES nonce for loose resources. Output remains numeric. */
        if (argc == 5 && _strnicmp(name, argv[4], strlen(argv[4])) &&
            (strlen(name) < 4 || _stricmp(name + strlen(name) - 4, ".lst"))) continue;
        if (!strcmp(argv[3], "--list")) {
            printf("%u\t%u\t%s\n", i, size, name);
            continue;
        }
        void *data = malloc(size ? size : 1);
        if (!data) { result = 9; break; }
        if (fseek(input, entry[2], SEEK_SET) || fread(data, 1, size, input) != size) {
            free(data); result = 10; break;
        }
        char output[32768];
        int length = snprintf(output, sizeof(output), "%s/%u.bin", argv[3], i);
        if (length < 0 || (unsigned)length >= sizeof(output)) { free(data); result = 11; break; }
        HANDLE file = CreateFileA(output, GENERIC_WRITE, 0, NULL, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
        DWORD written = 0;
        if (file == INVALID_HANDLE_VALUE) { free(data); result = 12; break; }
        BOOL ok = WriteFile(file, data, size, &written, NULL);
        CloseHandle(file);
        free(data);
        if (!ok || written != size) { result = 13; break; }
        printf("%u\t%u\t%s\n", i, size, name);
    }
    if (input) fclose(input);
    SLOT(lib, 2, Close)(lib, archive, 0); /* No flush. */
    destroy(&lib);
    FreeLibrary(dll);
    return result;
}
