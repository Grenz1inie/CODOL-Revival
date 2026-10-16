#include "codol_load_blocks.h"
#include <stdio.h>
int main(int argc,char **argv){
 codol_zone_t zone={0};codol_load_blocks_t blocks={0};unsigned failed=~0u;
 if(argc!=3 || !CODOL_OpenZoneFile(&zone,argv[1]))return 2;
 zone.format_version=423;
 int ok=CODOL_ReplayZone(&zone,&blocks,&failed);
 printf("replay=%d failed=%u bytes=%zu\n",ok,failed,blocks.written[3]);
 if(ok){FILE *f=fopen(argv[2],"wb");ok=f && fwrite(blocks.data[3],1,blocks.written[3],f)==blocks.written[3];if(f)fclose(f);}
 CODOL_FreeLoadBlocks(&blocks);CODOL_CloseZone(&zone);return ok?0:1;
}