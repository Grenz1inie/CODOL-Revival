#include <stdio.h>
#include <stdlib.h>
typedef unsigned int u32;
int read_collision_layout423(const u32 *, u32 *);
int main(int argc, char **argv)
{
    FILE *file;
    unsigned char *data;
    long length;
    u32 asset[4], layout[86], i;
    if (argc != 4 || !(file = fopen(argv[1], "rb"))) return 2;
    fseek(file, 0, SEEK_END); length = ftell(file); rewind(file);
    if (length < 0 || !(data = malloc(length ? length : 1))) return 2;
    if (fread(data, 1, length, file) != (size_t)length) return 2;
    fclose(file);
    asset[0] = strtoul(argv[2], 0, 0); asset[1] = (u32)data;
    asset[2] = length; asset[3] = strtoul(argv[3], 0, 0);
    i = read_collision_layout423(asset, layout);
    free(data);
    if (!i) return 1;
    for (i = 0; i < 86; ++i) printf("%u\n", layout[i]);
    return 0;
}
