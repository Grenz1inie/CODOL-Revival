/* ABI harness for the reference server's real message writers. */
#include "codol_2697_gamestate.h"
#include "codol_2697_fields.h"
#include "codol_2697_snapshot.h"
#include "codol_2697_adapter.h"
#include "codol_2697_resources.h"
#include "codol_usercmd.h"
#include "codol_wire.h"
#include "codol_weapon_registry.h"
#include "codol_weapon_2697_registry.h"
#include "codol_glass_map.h"
#include <string.h>

__declspec(dllexport) int native_weapon_keys(unsigned count,const char **names,
    const char **ammo,const char **clips,const unsigned *flags,const unsigned *no_clip,int *out)
{
    codol_weapon_registry_t *r=CODOL_CreateWeaponRegistry();unsigned i;int ok=1;
    if(!r)return 0;
    for(i=0;i<count;++i) {
        if(!CODOL_RegisterWeaponKeys(r,i,names[i],ammo[i],clips[i],flags[i],no_clip[i],-1) ||
           !CODOL_GetWeaponKeys(r,i,out+2*i,out+2*i+1)) {ok=0;break;}
    }
    CODOL_DestroyWeaponRegistry(r);return ok;
}

__declspec(dllexport) int native_resource_slots(unsigned kind,unsigned *out)
{
    codol_netconst_index_t index={0};codol2697_resources_t resources={0};
    codol_configstrings_t bank={0};unsigned base,cap,first;
    const char *names[]={"static","second"};
    codol_netconst_t table={"ncs_test_level",kind,0,2,names};
    codol2697_resource_source_t source={&resources,&bank,NULL};int ok=0;
    if(!CODOL2697_InternalResourceRange(kind,&base,&cap))return 0;
    first=(kind==8||kind==14)?0:1;
    if(!CODOL_BuildNetConstIndex(&table,1,"chi",&index) ||
       !CODOL2697_InstallResources(&resources,&index))goto done;
    for(unsigned i=0;i<3;++i) {
        const char *name=i<2?names[i]:"dynamic";
        if(!CODOL_SetConfigstring(&bank,base+first+i,name) ||
           !CODOL2697_ResolveResource(&source,kind,first+i,out+i) ||
           !CODOL2697_ReverseResource(&source,kind,out[i],out+3+i))goto done;
        const char *actual=CODOL2697_ResourceName(&resources,kind,out[i]);
        if(!actual||strcmp(name,actual))goto done;
    }
    ok=1;
done:
    CODOL_ClearConfigstrings(&bank);CODOL2697_ClearResources(&resources);
    CODOL_FreeNetConstIndex(&index);return ok;
}

static int test_resolve(void *opaque,unsigned kind,unsigned source,unsigned *target)
{(void)opaque;*target=source+10;return kind==0||kind==9||kind==13;}

__declspec(dllexport) size_t native_obituary(void *out,unsigned capacity,unsigned selector)
{
    codol_entity_state_t source={0};codol2697_entity_t target={0},held={0};
    codol2697_adapter_t adapter={test_resolve,NULL};codol_delta_context_t ctx={0};codol_msg_t msg;
    source.type=21+107;ctx.server_time=1000;
    for(unsigned i=0;i<CODOL_ENTITY_FIELDS;++i) {
        unsigned offset=CODOL_EntityField(source.type,i)->offset;
        if(offset==0xac)source.field[i]=selector&255;
        if(offset==0xe0)source.field[i]=selector>>8;
    }
    if(!CODOL2697_AdaptEntity(&target,&source,&adapter))return 0;
    CODOL_MsgWriteInit(&msg,out,capacity);
    if(!CODOL2697_WriteEntityPayload(&msg,NULL,&target,&held,&ctx))return 0;
    CODOL_WriteByte(&msg,6);return msg.failed?0:msg.size;
}

__declspec(dllexport) size_t native_engine_snapshot(void *out,unsigned capacity)
{
    codol2697_adapter_t adapter={test_resolve,NULL};codol_delta_context_t ctx={0};
    codol2697_snapshot_t frame={0};codol2697_player_fields_t player={0};
    codol2697_entity_t entities[2]={0};codol2697_client_t client={0};codol2697_actor_t actor={0};
    codol_entity_state_t source={0};codol_client_state_t source_client={0};
    codol_client_appearance_t appearance={0};codol_actor_state_t source_actor={0};codol_msg_t msg;
    for(unsigned i=0;i<CODOL_ENTITY_FIELDS;++i) {
        unsigned offset=CODOL_EntityField(0,i)->offset;
        if(offset==0x98)source.field[i]=5;
        if(offset==0x18)source.field[i]=0x41400000;
    }
    if(!CODOL2697_AdaptEntity(entities,&source,&adapter))return 0;
    memset(&source,0,sizeof(source));source.number=1;source.type=21+107;
    for(unsigned i=0;i<CODOL_ENTITY_FIELDS;++i)
        if(CODOL_EntityField(source.type,i)->offset==0xac)source.field[i]=5;
    if(!CODOL2697_AdaptEntity(entities+1,&source,&adapter))return 0;
    appearance.model=5;appearance.attach_model[0]=6;appearance.attach_tag[0]=2;
    if(!CODOL_OverlayClientAppearance(&source_client,&appearance) ||
       !CODOL2697_AdaptClient(&client,&source_client,&adapter))return 0;
    unsigned model=5,speed=0x3f000000;
    memcpy(source_actor.data+0xc,&model,4);memcpy(source_actor.data+0x50,&speed,4);
    if(!CODOL2697_AdaptActor(&actor,&source_actor,&adapter))return 0;
    player.field[0]=1000;ctx.server_time=1000;frame.sequence=1;frame.player=&player;
    frame.entities=entities;frame.entity_count=2;frame.clients=&client;frame.client_count=1;
    frame.actors=&actor;frame.actor_count=1;
    CODOL_MsgWriteInit(&msg,out,capacity);
    return CODOL2697_WriteSnapshot(&msg,&frame,NULL,NULL,8,&ctx)?msg.size:0;
}

__declspec(dllexport) size_t native_entity(void *out,unsigned capacity,unsigned type,
    unsigned previous_type,const unsigned *offsets,const uint64_t *previous,
    const uint64_t *values,unsigned count,uint64_t *reached)
{
    codol2697_entity_t from={0},to={0},held={0};codol_msg_t msg;codol_delta_context_t ctx={0};
    from.number=to.number=7;from.type=previous_type;to.type=type;ctx.server_time=1000;
    for(unsigned i=0;i<CODOL2697_ENTITY_FIELDS;++i)for(unsigned j=0;j<count;++j) {
        if(CODOL2697_EntityField(type,i)->offset==offsets[j])to.field[i]=values[j];
        if(previous_type!=UINT32_MAX && CODOL2697_EntityField(previous_type,i)->offset==offsets[j])
            from.field[i]=previous[j];
    }
    CODOL_MsgWriteInit(&msg,out,capacity);
    if(!CODOL2697_WriteEntityPayload(&msg,previous_type==UINT32_MAX?NULL:&from,&to,&held,&ctx))return 0;
    for(unsigned i=0;i<CODOL2697_ENTITY_FIELDS;++i)for(unsigned j=0;j<count;++j)
        if(CODOL2697_EntityField(type,i)->offset==offsets[j])reached[j]=held.field[i];
    CODOL_WriteByte(&msg,6);return msg.failed?0:msg.size;
}

__declspec(dllexport) size_t native_object_state(void *out,unsigned capacity,
    unsigned actor,const void *raw,void *reached)
{
    codol_msg_t msg;codol_delta_context_t ctx={0};ctx.server_time=1000;
    CODOL_MsgWriteInit(&msg,out,capacity);
    if(actor) {
        codol2697_actor_t to={0},held={0};memcpy(to.data,raw,sizeof(to.data));
        if(!CODOL2697_WriteActors(&msg,NULL,0,&to,1,&held,&ctx))return 0;
        memcpy(reached,held.data,sizeof(held.data));
    } else {
        codol2697_client_t to={0},held={0};
        for(unsigned i=0;i<CODOL2697_CLIENT_FIELDS;++i) {
            unsigned offset=CODOL2697_ClientField(i)->offset;
            if(offset<0x134)memcpy(to.field+i,(const char *)raw+offset,4);
        }
        if(!CODOL2697_WriteClientPayload(&msg,NULL,&to,&ctx) ||
           !CODOL2697_ReachClient(&held,NULL,&to,&ctx))return 0;
        memset(reached,0,0x134);
        for(unsigned i=0;i<CODOL2697_CLIENT_FIELDS;++i) {
            unsigned offset=CODOL2697_ClientField(i)->offset;
            if(offset<0x134)memcpy((char *)reached+offset,held.field+i,4);
        }
    }
    CODOL_WriteByte(&msg,6);return msg.failed?0:msg.size;
}

__declspec(dllexport) size_t native_adapt_player(void *out,unsigned capacity,
    const unsigned *offsets,const unsigned *values,unsigned count)
{
    codol_player_fields_t engine={0};codol2697_player_fields_t target={0},from={0},held={0};
    codol2697_adapter_t adapter={test_resolve,NULL};codol_delta_context_t context={0};codol_msg_t msg;
    for(unsigned j=0;j<count;++j) {
        unsigned i;for(i=0;i<CODOL_PLAYER_FIELDS;++i)if(CODOL_PlayerField(i)->offset==offsets[j])break;
        if(i==CODOL_PLAYER_FIELDS)return 0;engine.field[i]=values[j];
    }
    if(!CODOL2697_AdaptPlayer(&target,&engine,&adapter))return 0;
    CODOL_MsgWriteInit(&msg,out,capacity);
    if(!CODOL2697_WritePlayerFields(&msg,&from,&target,&held,&context))return 0;
    CODOL_WriteBits(&msg,0,14);CODOL_WriteByte(&msg,6);return msg.failed?0:msg.size;
}

__declspec(dllexport) size_t native_packet(void *out, unsigned capacity, const void *data,
    unsigned length, unsigned index, unsigned sequence, unsigned ack, unsigned challenge)
{
    unsigned char message[0x20000];codol_msg_t msg;
    if(length>sizeof(message)-4)return 0;
    CODOL_MsgWriteInit(&msg,message,sizeof(message));CODOL_WriteLong(&msg,ack);
    memcpy(message+4,data,length);
    CODOL_Xor(message+4,length,(unsigned char)(challenge^sequence),(const uint8_t *)"move%\xff",6);
    return CODOL_WritePacket(out,capacity,sequence,-1,message,length+4,index);
}

__declspec(dllexport) size_t native_snapshot(void *out, unsigned capacity, unsigned time)
{
    codol_msg_t msg;
    codol2697_player_fields_t player={0};
    codol2697_snapshot_t state={0};
    codol_delta_context_t context={0};
    player.field[0]=time;context.server_time=time;state.sequence=1;state.player=&player;
    CODOL_MsgWriteInit(&msg,out,capacity);
    return CODOL2697_WriteSnapshot(&msg,&state,NULL,NULL,8,&context) ? msg.size : 0;
}

__declspec(dllexport) size_t native_inventory(void *out, unsigned capacity,
    unsigned weapon, unsigned clip, unsigned reserve, unsigned slot)
{
    codol_msg_t msg;
    codol2697_player_fields_t from={0},to={0},held={0};
    codol_delta_context_t context={0};
    codol_player_array_updates_t updates={0};
    if(slot>=16)return 0;
    updates.stats_mask=1;updates.stats[0]=100;
    updates.clip_mask=1u<<slot;updates.clip_index[slot]=weapon;
    updates.clip_presence[slot]=1;updates.clip_ammo[slot][0]=clip;
    updates.weapons_mask=updates.weapon_index_mask=1;updates.weapon_index[0]=weapon;
    updates.weapon_flags[0]=31;
    updates.reserve_mask=1u<<slot;updates.reserve_type[slot]=weapon;updates.reserve_ammo[slot]=reserve;
    CODOL_MsgWriteInit(&msg,out,capacity);
    if(!CODOL2697_WritePlayerFields(&msg,&from,&to,&held,&context) ||
       !CODOL2697_WritePlayerArrays(&msg,&updates,NULL,NULL,&context))return 0;
    CODOL_WriteByte(&msg,6);
    return msg.failed?0:msg.size;
}

static void command_values(const codol_usercmd_t *command, unsigned *out)
{
    codol_usercmd_t to=*command;
    out[0]=to.serverTime;out[1]=to.buttons;
    for(unsigned i=0;i<3;++i)out[2+i]=to.angles[i];
    out[5]=to.direction;out[6]=to.weapon;out[7]=to.offHandIndex;out[8]=to.altModeWeapon;
    out[9]=to.meleeChargeYaw;out[10]=to.meleeChargeDist;out[11]=0;
#ifdef CODOL3333_USERCMD
    out[11]=to.meleeTarget;
#endif
    out[12]=to.selectedLocation[0];out[13]=to.selectedLocation[1];out[14]=to.selectedLocationAngle;
    out[15]=to.remoteAngles[0];out[16]=to.remoteAngles[1];
}

__declspec(dllexport) void native_default_usercmd(const uint64_t *values, unsigned *out)
{
    codol2697_player_fields_t state={0};codol_usercmd_t command;
    for(unsigned i=0;i<CODOL2697_PLAYER_FIELDS && i<235;++i)state.field[i]=values[i];
    CODOL2697_DefaultUsercmd(&state,&command);command_values(&command,out);
}

__declspec(dllexport) int native_usercmd(const void *data, unsigned length, unsigned key,
    const unsigned *previous, unsigned *out)
{
    codol_msg_t msg;
    codol_usercmd_t from={0},to={0};
    from.serverTime=previous[0];from.buttons=previous[1];
    for(unsigned i=0;i<3;++i)from.angles[i]=previous[2+i];
    from.direction=previous[5];from.weapon=previous[6];from.offHandIndex=previous[7];
    from.altModeWeapon=previous[8];from.meleeChargeYaw=previous[9];from.meleeChargeDist=previous[10];
#ifdef CODOL3333_USERCMD
    from.meleeTarget=previous[11];
#endif
    from.selectedLocation[0]=previous[12];from.selectedLocation[1]=previous[13];
    from.selectedLocationAngle=previous[14];from.remoteAngles[0]=previous[15];from.remoteAngles[1]=previous[16];
    CODOL_MsgReadInit(&msg,data,length);
    if(!CODOL_ReadUsercmd(&msg,key,&from,&to))return 0;
    command_values(&to,out);
    return 1;
}

__declspec(dllexport) int native_registry(const codol_netconst_t *tables, unsigned count,
    unsigned seed, unsigned *summary, char *out, unsigned capacity)
{
    codol_netconst_index_t index={0};
    unsigned offset=0;
    if(!CODOL_BuildNetConstIndexSeeded(tables,count,"chi",seed,&index))return 0;
    memset(summary,0,64*sizeof(*summary));
    summary[63]=index.checksum;
    for(unsigned k=0;k<CODOL2697_NCS_KINDS && k<21;++k) {
        const codol_netconst_kind_t *kind=index.kinds+k;
        summary[k*3]=kind->base;summary[k*3+1]=kind->capacity;summary[k*3+2]=kind->count;
        for(unsigned i=0;i<kind->count;++i) {
            size_t length=strlen(kind->values[i])+1;
            if(length>capacity-offset){CODOL_FreeNetConstIndex(&index);return 0;}
            memcpy(out+offset,kind->values[i],length);offset+=(unsigned)length;
        }
    }
    CODOL_FreeNetConstIndex(&index);
    return 1;
}

__declspec(dllexport) size_t native_playerstate(void *out, unsigned capacity,
    const uint64_t *previous, const uint64_t *values, unsigned server_time)
{
    codol_msg_t msg;
    codol2697_player_fields_t from={0},to={0},held={0};
    codol_delta_context_t context={0};
    context.server_time=server_time;
    for(unsigned i=0;i<CODOL2697_PLAYER_FIELDS && i<235;++i) {
        from.field[i]=previous[i];to.field[i]=values[i];
    }
    CODOL_MsgWriteInit(&msg,out,capacity);
    if(!CODOL2697_WritePlayerFields(&msg,&from,&to,&held,&context))return 0;
    CODOL_WriteBits(&msg,0,14); /* Current reader's unchanged array sections. */
    CODOL_WriteByte(&msg,6);
    return msg.failed?0:msg.size;
}

__declspec(dllexport) size_t native_configstrings(void *out, unsigned capacity,
    unsigned index, unsigned aliases, unsigned camo, unsigned extra, unsigned attachment)
{
    codol_msg_t msg;
    codol_netconst_index_t constants = {0};
    codol2697_configstring_t row = {index, "current"};
    codol2697_weapon_alias_t alias[1024];
    codol2697_weapon_recipe_t recipe = {0};
    if (aliases > 1024) return 0;
    for (unsigned i=0; i<aliases; ++i) {
        alias[i].index=5444+i; alias[i].weapon=1;
    }
    recipe.index=5444+aliases; recipe.weapon=1; recipe.camo=camo;
    recipe.count=1; recipe.attachment[0]=attachment;
#ifdef CODOL3333_PORT
    recipe.extra9=extra;
#else
    (void)extra;
#endif
    CODOL_MsgWriteInit(&msg,out,capacity);
    return CODOL2697_WriteConfigstrings(&msg,&constants,&row,1,alias,aliases,&recipe,1)
        ? msg.size : 0;
}

__declspec(dllexport) size_t native_gamestate(void *out, unsigned capacity,
    const char *map, const char *category, unsigned client)
{
    codol_msg_t msg;
    codol_netconst_index_t constants = {0};
    codol2697_gamestate_t state = {7,0xc6280541u,123,0,0};
    codol2697_configstring_t row = {0,"\\mapname\\mp_cargoship\\g_gametype\\coop"};
    state.map_name=map; state.client_number=client;
#ifdef CODOL3333_CATEGORY
    state.category=category;
#else
    (void)category;
#endif
    CODOL_MsgWriteInit(&msg,out,capacity);
    return CODOL2697_WriteGamestate(&msg,&state,&constants,&row,1,0,0,0,0)
        ? msg.size : 0;
}

__declspec(dllexport) int native_glass_source(unsigned variant,unsigned *out)
{
    uint8_t bytes[116+52]={0};uint32_t count=1;codol_glass_map_source_t result={77,NULL,NULL};
    codol_asset_t asset={0};codol_load_blocks_t blocks={0};codol_glass_span_t span={0};
    memcpy(bytes+24,&count,4);asset.type=20;asset.format_version=423;asset.data=bytes;asset.size=sizeof(bytes);
    span.world=bytes;span.group=UINT32_MAX-1;span.pieces=bytes+116;span.piece_count=1;
    blocks.source=bytes;blocks.source_size=sizeof(bytes);blocks.glass_records=&span;
    blocks.glass_record_count=blocks.glass_record_capacity=1;
    if(variant==1)blocks.glass_record_count=0;
    if(variant==2)asset.size--;
    if(variant==3)span.piece_count=2;
    if(variant==4){count=2048;memcpy(bytes+24,&count,4);span.piece_count=count;}
    if(variant==5)span.pieces=bytes+115;
    int ok=CODOL_ReadGlassMap(NULL,NULL,&blocks,&asset,&result);
    out[0]=result.count;out[1]=result.initial_pieces==bytes+116;
    return ok;
}

static int registry_source(void *context,const char *name,codol_weapon_2697_keys_source_t *out)
{
    const codol_weapon_2697_keys_source_t *rows=context;
    for(unsigned i=0;rows[i].name;++i)if(!strcmp(rows[i].name,name)){*out=rows[i];return 1;}
    return 0;
}
__declspec(dllexport) int native_weapon_registry(unsigned count,void *rows,const char **names,int *out)
{
    codol_netconst_t table={"ncs_weapons",13,0,count-1,names+1};codol_netconst_index_t index={0};
    codol_weapon_2697_registry_t *r=NULL;int ok=0;
    if(!count || !CODOL_BuildNetConstIndex(&table,1,"chi",&index) ||
       !CODOL_BuildWeapon2697Registry(&index,registry_source,rows,&r,NULL))goto done;
    const codol_weapon_registry_t *keys=CODOL_Weapon2697RegistryKeys(r);
    for(unsigned i=0;i<count;++i)if(!CODOL_GetWeaponKeys(keys,i,out+3*i,out+3*i+1) ||
        !CODOL_Weapon2697SharedKey(r,i,out+3*i+2,NULL))goto done;
    ok=1;
done:
    CODOL_FreeWeapon2697Registry(r);CODOL_FreeNetConstIndex(&index);return ok;
}
