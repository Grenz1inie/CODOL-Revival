from pathlib import Path
import difflib

root=Path(__file__).resolve().parents[7]
stage=root/'research/experiments/story-native'
src=stage/'server3333'
changed=[]
def edit(name, operation):
    p=src/name
    p.write_text(operation(p.read_text()),newline='\n')
    changed.append(name)
def replace(text,old,new):
    assert old in text,old
    return text.replace(old,new)
def section(text,start,end,op):
    a=text.index(start); b=text.index(end,a)
    return text[:a]+op(text[a:b])+text[b:]

def registry(t):
    t=section(t,'int CODOL_LoadMountedWeapon(const','int CODOL_LoadMountedWeaponHideTags',lambda x:replace(replace(x,
        'result.asset.format_version!=334 && result.asset.format_version!=365','result.asset.format_version!=334 && result.asset.format_version!=365 && result.asset.format_version!=423'),
        'pos=result.asset.format_version==365 ? 0xc34 : 0xbfc;','pos=result.asset.format_version==423 ? 0xe28 : result.asset.format_version==365 ? 0xc34 : 0xbfc;'))
    t=section(t,'int CODOL_LoadMountedWeaponHideTags','static const codol_native_weapon_core_t',lambda x:replace(x,
        'weapon.asset.data+0x3c+2*i','weapon.asset.data+(weapon.asset.format_version==423 ? 0x38 : 0x3c)+2*i'))
    t=section(t,'int CODOL_LoadMountedWeaponModel','int CODOL_LoadMountedWeaponAnimationSource',lambda x:replace(x,
        'pos=weapon.dependency_offset;','if(weapon.asset.format_version==423 && index==10) return 0;\n    pos=weapon.dependency_offset;'))
    def animations(x):
        x=replace(x,'i<11;++i','i<(weapon.asset.format_version==423 ? 10 : 11);++i')
        x=replace(x,'result.slots_per_hand=result.format_version==365 ? 52 : 48;','result.slots_per_hand=result.format_version==423 ? 56 : result.format_version==365 ? 52 : 48;')
        return replace(x,'weapon.asset.data+0x7c+4*i','weapon.asset.data+(weapon.asset.format_version==423 ? 0x78 : 0x7c)+4*i')
    t=section(t,'int CODOL_LoadMountedWeaponAnimationSource','int CODOL_LoadMountedWeaponAnimations',animations)
    def effects(x):
        x=replace(x,'for (i=0;i<2;++i) {','''/* REA 0x49190c/0x49195b/0x4919a6: two banks of 16 plus three FX.
     * Keep all source slots; choosing the runtime flash variant is separate. */
    result.count=weapon.asset.format_version==423 ? 35 : 2;
    for (i=0;i<result.count;++i) {''')
        x=replace(x,'weapon.asset.data+(weapon.asset.format_version==365 ? 0x38c : 0x35c)+4*i',
            'weapon.asset.data+(weapon.asset.format_version==423 ? (i<16 ? 0x3b8+4*i : i<32 ? 0x418+4*(i-16) : 0x498+4*(i-32)) : (weapon.asset.format_version==365 ? 0x38c : 0x35c)+4*i)')
        return replace(x,'weapon.asset.format_version!=365 || effect_name','(weapon.asset.format_version!=365 && weapon.asset.format_version!=423) || effect_name')
    t=section(t,'int CODOL_LoadMountedWeaponEffects','static int weapon_sound',effects)
    def sounds(x):
        return replace(replace(x,'weapon.asset.format_version==365 ? 0x394 : 0x364',
            'weapon.asset.format_version==423 ? 0x4a4 : weapon.asset.format_version==365 ? 0x394 : 0x364'),
            'weapon.asset.format_version==365 ? 0x468 : 0x438',
            'weapon.asset.format_version==423 ? 0x578 : weapon.asset.format_version==365 ? 0x468 : 0x438')
    t=section(t,'int CODOL_LoadMountedWeaponSounds','int CODOL_LoadMountedWeaponVisuals',sounds)
    def visuals(x):
        x=replace(x,'static const unsigned dependencies[][3]=','static const unsigned legacy_dependencies[][3]=')
        x=replace(x,'codol_mounted_weapon_t weapon;','''static const unsigned current_dependencies[][3]={{0x580,4,30},{0x590,2,5},
        {0x66c,6,5},{0x688,1,5},{0x690,1,5},{0x69c,4,5}};
    const unsigned (*dependencies)[3]; unsigned groups;
    codol_mounted_weapon_t weapon;''')
        x=replace(x,'pos=sounds.dependency_offset;','''pos=sounds.dependency_offset;
    dependencies=weapon.asset.format_version==423 ? current_dependencies : legacy_dependencies;
    groups=weapon.asset.format_version==423 ? 6 : 5;
    result.count=weapon.asset.format_version==423 ? 18 : 14;''')
        x=replace(x,'i<sizeof(dependencies)/sizeof(dependencies[0])','i<groups')
        return replace(x,'weapon.asset.format_version!=365 || asset_name','(weapon.asset.format_version!=365 && weapon.asset.format_version!=423) || asset_name')
    t=section(t,'int CODOL_LoadMountedWeaponVisuals','int CODOL_LoadMountedWeaponAmmoNames',visuals)
    t=section(t,'int CODOL_LoadMountedWeaponAmmoNames','int CODOL_LoadMountedWeaponTail',lambda x:replace(x,
        'shift=weapon.asset.format_version==365 ? 0x30 : 0;',
        'shift=weapon.asset.format_version==423 ? 0x150 : weapon.asset.format_version==365 ? 0x30 : 0;'))
    def tail(x):
        x=replace(x,'const unsigned (*fields)[4]; size_t field_count;','''/* Ordered dependency fields from current loader 0x4915b0. */
    static const unsigned current_fields[][4]={
        {0x7dc,4,A,5},{0x8b0,1,A,1},{0x8b4,1,A,0},{0x910,1,A,4},
        {0x918,2,A,30},{0x920,2,N,0},{0xa38,2,A,30},
        {0xa58,1,A,30},{0xa5c,1,N,0},{0xa60,3,A,30},
        {0xb24,1,S,0},{0xb2c,1,P,0xd5c},{0xb28,1,S,0},{0xb30,1,P,0xd5e},
        {0xb80,2,S,0},{0xba4,2,S,0},{0xc44,2,S,0},
        {0xc4c,2,A,40},{0xc6c,1,N,0},{0xc70,1,A,30},{0xc74,1,S,0},
        {0xc84,11,N,0},{0xcf0,6,N,0},{0xd20,1,S,0},{0xd30,2,S,0},
        {0xd3c,3,A,5},{0xd60,2,P,0xd5c},{0xe08,1,S,0},{0xe18,1,S,0}
    };
    const unsigned (*fields)[4]; size_t field_count;''')
        x=replace(x,'fields=weapon.asset.format_version==365 ? target_fields : legacy_fields;',
            'fields=weapon.asset.format_version==423 ? current_fields : weapon.asset.format_version==365 ? target_fields : legacy_fields;')
        x=replace(x,'field_count=weapon.asset.format_version==365 ?',
            'field_count=weapon.asset.format_version==423 ? sizeof(current_fields)/sizeof(current_fields[0]) : weapon.asset.format_version==365 ?')
        # Current dependency count is 66, including null entries.
        x=replace(x,'if(result.count>=64)','if(result.count>=sizeof(result.entries)/sizeof(result.entries[0]))')
        return replace(x,'weapon.asset.format_version!=365 || asset_name','(weapon.asset.format_version!=365 && weapon.asset.format_version!=423) || asset_name')
    return section(t,'int CODOL_LoadMountedWeaponTail','static int world_string',tail)
edit('src/codol/assets/codol_asset_registry.c',registry)
def types(t):
    t=replace(t,'const char *names[156];','const char *names[168];')
    t=replace(t,'const char *names[2];\n    codol_asset_t assets[2];','const char *names[35];\n    codol_asset_t assets[35];\n    unsigned count;')
    t=replace(t,'codol_weapon_dependency_t entries[14]; /* Four FX, then ten materials. */',
        'codol_weapon_dependency_t entries[18]; /* 423 adds four material slots. */\n    unsigned count;')
    t=replace(t,'codol_weapon_dependency_t entries[64];','codol_weapon_dependency_t entries[72];')
    return t
edit('src/codol/assets/codol_assets.h',types)
def probe(t):
    t=replace(t,'if(a!=1 || b!=1 || c!=1 || e!=1 || f!=1 || g!=1 || h!=1 || t!=1) { ok=0; continue; }',
        'if(a!=1 || b!=1 || c!=1 || e!=1 || f!=1 || g!=1 || h!=1 || t!=1) { ok=0; continue; }\n        if(getenv("CODOL_WEAPON_SOURCE_ONLY")) continue;')
    return replace(t,'    {\n        {\n            static const char *tables[]=',
        '    if(getenv("CODOL_WEAPON_SOURCE_ONLY")) return ok;\n    {\n        {\n            static const char *tables[]=')
edit('src/codol/assets/codol_archive_probe.c',probe)
p=root/'games/codol/versions/v3_3_3_3/reverse/tools/native/server3333.patch'
names={x[6:] for x in p.read_text().splitlines() if x.startswith('--- a/')}|set(changed)
p.write_text(''.join(line for n in sorted(names) for line in difflib.unified_diff((stage/'reference-source'/n).read_text().splitlines(True),(src/n).read_text().splitlines(True),fromfile='a/'+n,tofile='b/'+n)),newline='\n')
