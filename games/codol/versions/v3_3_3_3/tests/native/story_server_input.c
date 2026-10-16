/* Exercise the retained engine bridge under its required 32-bit ABI. */
#include "codol_game.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc,char **argv)
{
    unsigned char data[4096];
    msg_t msg={0};codol_usercmd_t command;
    float origin[3]={0};uint32_t time=0;int ok;
    FILE *input;
    if(argc!=3 || !(input=fopen(argv[1],"rb")))return 2;
    msg.cursize=(int)fread(data,1,sizeof(data),input);fclose(input);
    msg.data=data;msg.maxsize=sizeof(data);
    ok=CODOL_ReadUsermoveMSGFrom(&msg,(uint32_t)strtoul(argv[2],NULL,0),1,NULL,&command,1,origin,&time);
    printf("{\"ok\":%d,\"cursor\":%d,\"time\":%u,\"origin\":[%g,%g,%g]}\n",
        ok,msg.readcount,(unsigned)time,origin[0],origin[1],origin[2]);
    return 0;
}
