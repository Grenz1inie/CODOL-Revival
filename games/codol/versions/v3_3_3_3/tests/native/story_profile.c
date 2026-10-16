/* Exercise the original storage reader; only allocator/process glue lives here. */
#include "codol_profile.h"
#include "codol_stats.h"
#include "zlib/zlib.h"
#include <stdlib.h>
#include <stdio.h>
#include <io.h>
#include <fcntl.h>

voidpf zcalloc(voidpf opaque, unsigned items, unsigned size)
{ (void)opaque; return calloc(items, size); }
void zcfree(voidpf opaque, voidpf ptr)
{ (void)opaque; free(ptr); }

int main(int argc, char **argv)
{
    uint8_t profile[CODOL_STATS_SIZE];
    if(argc != 3) return 2;
    if(CODOL_ReadSecureProfile(argv[1], strtoull(argv[2], NULL, 10), 1,
        NULL, profile, sizeof(profile)) != 1) return 1;
    if(_setmode(_fileno(stdout), _O_BINARY) == -1) return 2;
    return fwrite(profile, 1, sizeof(profile), stdout) == sizeof(profile) ? 0 : 3;
}
