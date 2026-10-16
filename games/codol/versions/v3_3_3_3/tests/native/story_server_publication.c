/* Exercise native publication with only the owning server replaced by fixtures. */
#include "codol_2697_server.h"
#include "codol_sv_state.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static codol2697_resources_t resources;
static codol_configstrings_t bank;
static codol2697_resource_source_t source={&resources,&bank,NULL};
static codol2697_registration_t registration;
codol2697_resource_source_t *CODOL_Server2697ResourceSource(void){return &source;}
const codol2697_registration_t *CODOL_Server2697Registration(void){return &registration;}
codol_configstrings_t *CODOL_ServerConfigstrings(void){return &bank;}
const char *CODOL_ServerMapName(void){return "mp_cargoship";}
const char *CODOL_ServerZoneType(void){return "mp";}
void Com_Printf(int channel,const char *format,...){(void)channel;(void)format;}

int main(int argc,char **argv)
{
    codol_netconst_index_t constants={0};
    const char *menus[]={"staticmenu"},*tags[]={"tag_origin"};
    codol_netconst_t tables[]={{"ncs_menu_level",8,0,1,menus},{"ncs_tag_level",9,0,1,tags}};
    if(argc<3)return 2;
    if(!strcmp(argv[1],"registration")) {
        int ok=CODOL2697_ReadRegistration(argv[2],&registration);
        printf("[%d,%u,%u]\n",ok,registration.count,registration.codinfo_count);return 0;
    }
    if(!CODOL_BuildNetConstIndex(tables,2,"chi",&constants) ||
       !CODOL2697_InstallResources(&resources,&constants))return 3;
    registration.count=2;registration.codinfo_count=1;registration.verified=1;
    strcpy(registration.names[0],"known");strcpy(registration.names[1],"new_name");
    strcpy(registration.codinfo_names[0],"known");
    CODOL_SetConfigstring(&bank,24,"known");CODOL_SetConfigstring(&bank,25,"new_name");
    CODOL_SetConfigstring(&bank,224,"42");CODOL_SetConfigstring(&bank,225,"7");
    CODOL_SetConfigstring(&bank,CODOL_CS_MENUS,"staticmenu");
    CODOL_SetConfigstring(&bank,CODOL_CS_MENUS+1,"dynamicmenu");
    CODOL_SetConfigstring(&bank,CODOL_CS_TAGS+1,"tag_origin");
    if(!strcmp(argv[1],"map")) {
        printf("[");
        for(int i=2;i<argc;++i) {
            unsigned target=UINT32_MAX,index=(unsigned)strtoul(argv[i],NULL,0);
            int mapped=CODOL2697_MapConfigIndex(index,&target);
            printf("%s[%u,%d,%u]",i==2?"":",",index,mapped,target);
        }
        printf("]\n");
    } else if(!strcmp(argv[1],"link")) {
        char out[128]={0};int ok=CODOL2697_LinkTagCommand(out,sizeof(out),argv[2]);
        printf("[%d,\"%s\"]\n",ok,out);
    } else return 2;
    CODOL_ClearConfigstrings(&bank);CODOL2697_ClearResources(&resources);
    CODOL_FreeNetConstIndex(&constants);return 0;
}
