#include "codol_weapon_attachment.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* The mounted-reader seam supplies resolved dependencies. The image must retain
 * every 423 slot and protect serialized pointers from scalar attachment writes. */
static unsigned version=423;
static unsigned char bytes[0xe28],points[32];
static char animations[168][16],effects[35][16];
static const unsigned visual_offsets[]={0x580,0x584,0x588,0x58c,0x590,0x594,
    0x66c,0x670,0x674,0x678,0x67c,0x680,0x688,0x690,0x69c,0x6a0,0x6a4,0x6a8};
int CODOL_LoadMountedWeapon(const char *name,codol_mounted_weapon_t *out)
{
    memset(out,0,sizeof(*out));out->asset.type=28;out->asset.format_version=version;
    out->asset.data=bytes;out->asset.size=sizeof(bytes);out->strings[0]=name;return 1;
}
int CODOL_LoadMountedWeaponAnimationSource(const char *name,codol_weapon_animation_source_t *out)
{
    unsigned i;memset(out,0,sizeof(*out));out->count=168;out->slots_per_hand=56;out->format_version=423;
    for(i=0;i<168;++i){sprintf(animations[i],"animation_%u",i);out->names[i]=animations[i];}return 1;
}
int CODOL_LoadMountedWeaponEffects(const char *name,codol_weapon_effects_t *out)
{
    unsigned i;memset(out,0,sizeof(*out));out->count=35;
    for(i=0;i<35;++i){sprintf(effects[i],"effect_%u",i);out->names[i]=effects[i];}return 1;
}
int CODOL_LoadMountedWeaponSounds(const char *name,codol_weapon_sounds_t *out)
{ memset(out,0,sizeof(*out));out->names[52]="last_sound";out->arrays[1][30]="bounce";return 1; }
int CODOL_LoadMountedWeaponAmmoNames(const char *name,codol_weapon_ammo_names_t *out)
{ memset(out,0,sizeof(*out));out->ammo="ammo";out->clip="clip";out->shared_cap="shared";return 1; }
int CODOL_LoadMountedWeaponVisuals(const char *name,codol_weapon_visuals_t *out)
{
    unsigned i;memset(out,0,sizeof(*out));out->count=18;
    for(i=0;i<18;++i){out->entries[i].offset=visual_offsets[i];out->entries[i].name="visual";}return 1;
}
int CODOL_LoadMountedWeaponTail(const char *name,codol_weapon_tail_t *out)
{
    static const unsigned offsets[]={0xb2c,0xb30,0xd60,0xd64};unsigned i;
    memset(out,0,sizeof(*out));out->count=6;
    for(i=0;i<4;++i){out->entries[i].offset=offsets[i];out->entries[i].kind=CODOL_WEAPON_DEP_POINTS;
        out->entries[i].point_count=4;out->entries[i].points=points;}
    out->entries[4].offset=0xe08;out->entries[4].name="new_tail";
    out->entries[5].offset=0xe18;out->entries[5].name="last_tail";return 1;
}
int CODOL_LoadMountedWeaponHideTags(const char *name,codol_weapon_hide_tags_t *out)
{ memset(out,0,sizeof(*out));out->names[31]="last_tag";return 1; }
int CODOL_LoadMountedWeaponModel(const char *name,unsigned index,codol_weapon_model_t *out)
{ if(index>=10)return -1;memset(out,0,sizeof(*out));out->name="model";return 1; }
static void check_name(const codol_weapon_source_image_t *image,unsigned offset,const char *expected)
{
    const char *name=NULL;unsigned i;
    assert(CODOL_WeaponSourceName(image,offset,&name)==1);
    assert((!name&&!expected)||(name&&expected&&!strcmp(name,expected)));
    for(i=0;i<4;++i)assert(!image->scalar[offset+i]);
}
int main(void)
{
    codol_weapon_source_image_t image={0};codol_weapon_animation_source_t anim={0};
    codol_weapon_effects_t fx={0};codol_weapon_sounds_t sound={0};codol_weapon_visuals_t visual={0};
    codol_weapon_tail_t tail={0},before;codol_weapon_ammo_names_t ammo={0};
    codol_weapon_animations_t legacy={0};codol_weapon_model_t model={0};unsigned i;
    bytes[0xd5c]=4;bytes[0xd5e]=4;
    assert(CODOL_BeginWeaponSourceImage("test_mp",&image)==1);
    assert(image.data!=bytes&&!memcmp(image.data,bytes,sizeof(bytes)));
    assert(image.format_version==423&&!strcmp(image.context,"test"));
    for(i=0;i<168;++i)check_name(&image,0x78+4*i,animations[i]);
    for(i=0;i<35;++i)check_name(&image,i<16?0x3b8+4*i:i<32?0x418+4*(i-16):0x498+4*(i-32),effects[i]);
    for(i=0;i<18;++i)check_name(&image,visual_offsets[i],"visual");
    check_name(&image,0x574,"last_sound");check_name(&image,0xe18,"last_tail");
    check_name(&image,0x6b4,"ammo");check_name(&image,0x6bc,"clip");check_name(&image,0x6cc,"shared");
    for(i=0x38;i<0x78;++i)assert(!image.scalar[i]);
    for(i=0x578;i<0x580;++i)assert(!image.scalar[i]);
    assert(image.scalar[0x478]&&image.scalar[0x6f0]&&image.scalar[0xd10]);
    assert(CODOL_WeaponSourceModel(&image,9,&model)==1);
    assert(CODOL_WeaponSourceModel(&image,10,&model)==-1);
    assert(CODOL_WeaponSourceAnimations(&image,&legacy)==-1);
    assert(CODOL_WeaponSourceAnimationSource(&image,&anim)==1&&anim.count==168&&anim.slots_per_hand==56);
    assert(CODOL_WeaponSourceEffects(&image,&fx)==1&&fx.count==35&&!strcmp(fx.names[34],"effect_34"));
    assert(CODOL_WeaponSourceSounds(&image,&sound)==1&&!strcmp(sound.arrays[1][30],"bounce"));
    assert(CODOL_WeaponSourceAmmoNames(&image,&ammo)==1&&!strcmp(ammo.shared_cap,"shared"));
    assert(CODOL_WeaponSourceVisuals(&image,&visual)==1&&visual.count==18);
    assert(CODOL_WeaponSourceTail(&image,&tail)==1&&tail.count==6&&tail.entries[0].point_count==4);
    image.data[0xd5c]=2;
    assert(CODOL_WeaponSourceTail(&image,&tail)==1&&tail.entries[0].point_count==2&&tail.entries[2].point_count==2);
    before=tail;image.data[0xd5c]=5;
    assert(CODOL_WeaponSourceTail(&image,&tail)==-1&&!memcmp(&tail,&before,sizeof(tail)));
    { unsigned char *owned=image.data;version=424;
      assert(CODOL_BeginWeaponSourceImage("bad",&image)==-1&&image.data==owned); }
    CODOL_FreeWeaponSourceImage(&image);puts("weapon_source_image423 complete=1");return 0;
}
