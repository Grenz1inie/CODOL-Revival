#include "codol_weapon_2697.h"
#include "codol_weapon_2697_core.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void put(unsigned char *p,unsigned off,unsigned value){memcpy(p+off,&value,4);}
int main(void)
{
    unsigned char data[0xe28]={0};codol_mounted_weapon_t source={0};
    struct WeaponDef out={0},before;codol_weapon_2697_timing_extensions_t extra={0},saved;
    codol_weapon_animation_source_t animations={0};
    source.asset.type=28;source.asset.format_version=423;source.asset.data=data;source.asset.size=sizeof(data);
    /* Fire, reload and change consumers are recorded independently in REA.
     * Poison their old addresses to detect an accidental version-gate change. */
    put(data,0x5cc,9999);put(data,0xb9c,8888);
    put(data,0x6f0,137);put(data,0xd10,173);put(data,0x70c,331);
    put(data,0x71c,1201);put(data,0x728,1403);put(data,0x730,571);
    put(data,0x740,407);put(data,0x744,203);put(data,0x748,109);
    put(data,0x750,307);put(data,0xd28,313);put(data,0xd2c,317);put(data,0xd4c,419);
    put(data,0x76c,211);put(data,0x774,223);put(data,0x784,227);put(data,0x78c,229);
    out.damage=241;
    assert(CODOL_ApplyWeapon2697Timings(&source,&out,&extra)==1);
    assert(out.iFireDelay==137&&out.iFireTime==173&&out.iHoldFireTime==331&&out.damage==241);
    assert(out.iReloadTime==1201&&out.iReloadEmptyTime==1403&&out.iReloadAddTime==571);
    assert(out.iReloadStartTime==407&&out.iReloadStartAddTime==203&&out.iReloadEndTime==109);
    assert(out.iRaiseTime==307&&out.iAltRaiseTime==313&&out.iFirstRaiseTime==419&&extra.empty_alt_raise==317);
    assert(out.sprintInTime==211&&out.sprintOutTime==223&&extra.dive_in==227&&extra.dive_out==229);
    printf("weapon_timing423 fire=%d delay=%d hold=%d\n",out.iFireTime,out.iFireDelay,out.iHoldFireTime);
    before=out;saved=extra;put(data,0xd4c,0x80000000u);
    assert(!CODOL_ApplyWeapon2697Timings(&source,&out,&extra));
    assert(!memcmp(&before,&out,sizeof(out))&&!memcmp(&saved,&extra,sizeof(extra)));
    put(data,0xd4c,0x7fffffffu);
    assert(CODOL_ApplyWeapon2697Timings(&source,&out,&extra)&&out.iFirstRaiseTime==0x7fffffff);
    source.asset.size=0xe27;assert(!CODOL_ApplyWeapon2697Timings(&source,&out,&extra));source.asset.size=sizeof(data);
    put(data,0x6ac,47);put(data,0x6c4,137);put(data,0xd08,19);put(data,0x6c8,3);
    put(data,0x8c0,5);put(data,0x8c4,7);put(data,0x6d4,199);
    data[0xd7b]=1;data[0xd86]=1;data[0xd85]=1;out.iAmmoIndex=23;out.iClipIndex=29;
    assert(CODOL_ApplyWeapon2697AmmoParameters(&source,&out)==1);
    assert(out.iStartAmmo==47&&out.iMaxAmmo==137&&out.iClipSize==19&&out.shotCount==3);
    assert(out.iReloadAmmoAdd==5&&out.iReloadStartAdd==7&&out.iSharedAmmoCap==199);
    assert(out.bClipOnly&&out.bSegmentedReload&&out.bNoPartialReload&&out.iAmmoIndex==23&&out.iClipIndex==29);
    before=out;data[0xd86]=2;
    assert(!CODOL_ApplyWeapon2697AmmoParameters(&source,&out)&&!memcmp(&before,&out,sizeof(out)));
    animations.format_version=423;animations.count=168;animations.slots_per_hand=56;
    animations.names[56+3]="left_fire";animations.names[56+38]="left_ads_fire";
    animations.names[112+3]="right_fire";animations.names[112+38]="right_ads_fire";
    assert(CODOL_ApplyWeapon2697AnimationNames(&animations,1,&out));
    assert(!strcmp(out.szXAnims[3],"left_fire")&&!strcmp(out.szXAnims[28],"left_ads_fire"));
    assert(CODOL_ApplyWeapon2697AnimationNames(&animations,2,&out));
    assert(!strcmp(out.szXAnims[3],"right_fire")&&!strcmp(out.szXAnims[28],"right_ads_fire"));
    before=out;assert(!CODOL_ApplyWeapon2697AnimationNames(&animations,3,&out)&&!memcmp(&before,&out,sizeof(out)));
    animations.count=156;assert(!CODOL_ApplyWeapon2697AnimationNames(&animations,0,&out));
    {
        unsigned char normalized[0xbfc],saved_header[0xbfc];unsigned value;
        codol_weapon_tail_t tail={0},projected={0};codol_weapon_dependency_t preset={0};
        memset(data,0,sizeof(data));
        put(data,0x10,0x11110000);put(data,0x20,0x22220000);put(data,0x28,0x33330000);
        put(data,0x38,0x44440000);put(data,0x78+56*4+38*4,0x55550000);
        put(data,0x478,7);put(data,0x6f0,137);put(data,0xd10,173);
        put(data,0xbb4,17);put(data,0xbc8,19);put(data,0xbcc,0x43c80000);put(data,0xbe0,0x447a0000);
        data[0xd86]=1;data[0xd87]=0;data[0xd88]=1;data[0xd8b]=1;data[0xd91]=1;
        assert(CODOL_ProjectWeapon2697Header(&source,normalized));
#define WORD(off,expected) do{memcpy(&value,normalized+(off),4);assert(value==(expected));}while(0)
        WORD(0x10,0);WORD(0x14,0x11110000);WORD(0x24,0x22220000);WORD(0x2c,0x33330000);
        WORD(0x3c,0x44440000);WORD(0x7c+(48+34)*4,0x55550000);
        WORD(0x33c,7);WORD(0x59c,137);WORD(0xb68,173);
        WORD(0xa30,17);WORD(0xa34,19);WORD(0xa38,0x43c80000);WORD(0xa3c,0x447a0000);
#undef WORD
        assert(normalized[0xbd8]==1&&normalized[0xbd9]==1&&normalized[0xbdc]==1&&normalized[0xbe2]==1);
        put(data,0x6d8,101);put(data,0x6dc,103);put(data,0x7ac,3001);
        put(data,0x8f4,701);put(data,0x8f8,37);put(data,0x8fc,41);put(data,0x914,2);
        assert(CODOL_ApplyWeapon2697CombatParameters(&source,&out));
        assert(out.damage==101&&out.playerDamage==103&&out.minDamage==17&&out.minPlayerDamage==19);
        assert(out.fMaxDamageRange==400&&out.fMinDamageRange==1000&&out.fuseTime==3001);
        assert(out.iProjectileSpeed==701&&out.iProjectileSpeedUp==37&&out.iProjectileSpeedForward==41);
        assert(out.projExplosion==2&&out.timedDetonation&&out.projExplosionEffectForceNormalUp);
        before=out;put(data,0xbb8,1);
        assert(!CODOL_ApplyWeapon2697CombatParameters(&source,&out)&&!memcmp(&before,&out,sizeof(out)));
        put(data,0xbb8,0);put(data,0xbcc,0x7fc00000);
        assert(!CODOL_ApplyWeapon2697CombatParameters(&source,&out)&&!memcmp(&before,&out,sizeof(out)));
        put(data,0xbcc,0x43c80000);
        memcpy(saved_header,normalized,sizeof(normalized));source.asset.size=0xe27;
        assert(!CODOL_ProjectWeapon2697Header(&source,normalized)&&!memcmp(normalized,saved_header,sizeof(normalized)));
        source.asset.size=sizeof(data);
        tail.count=4;tail.entries[0].offset=0x7dc;tail.entries[0].kind=CODOL_WEAPON_DEP_ASSET;tail.entries[0].asset.type=5;
        tail.entries[1].offset=0x8b4;tail.entries[1].kind=CODOL_WEAPON_DEP_ASSET;tail.entries[1].asset.type=0;
        tail.entries[2].offset=0xd20;tail.entries[2].kind=CODOL_WEAPON_DEP_STRING;tail.entries[2].name="alternate";
        tail.entries[3].offset=0xd64;tail.entries[3].kind=CODOL_WEAPON_DEP_POINTS;
        assert(CODOL_ProjectWeapon423Tail(&tail,&projected,&preset));
        assert(projected.count==3&&projected.entries[0].offset==0x684&&projected.entries[1].offset==0xb78&&
            projected.entries[2].offset==0xbb8&&preset.offset==0x78c);
        tail.entries[3].offset=0xd66;assert(!CODOL_ProjectWeapon423Tail(&tail,&projected,&preset));
    }
    puts("weapon_parameters423 complete=1");return 0;
}
