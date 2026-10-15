from pathlib import Path
import re
import difflib

ROOT = Path(__file__).resolve().parents[3]
STAGE = Path(__file__).resolve().parent
PORT = STAGE / 'server3333'
REF = STAGE / 'reference-source'
changed = set()

def read(name):
    return (PORT / name).read_text()

def write(name, value):
    (PORT / name).write_text(value, newline='\n')
    changed.add(name)

def edits(name, pairs):
    value = read(name)
    for before, after in pairs:
        assert before in value, (name, before)
        value = value.replace(before, after)
    write(name, value)

def function_bounds(text, name):
    match = re.search(r'^(?:static )?(?:int|uint32_t|u32) '+name+r'\([^;]*?\)\s*\{', text, re.M)
    assert match, name
    first = text.index('{', match.start())
    depth = 1
    last = first + 1
    while depth:
        if text[last] == '{': depth += 1
        if text[last] == '}': depth -= 1
        last += 1
    return match.start(), last

def function(text, name):
    first, last = function_bounds(text, name)
    return text[first:last]

def replace_function(text, name, replacement):
    first, last = function_bounds(text, name)
    return text[:first] + replacement + text[last:]

raw = (ROOT / 'tools/native/story_archive427.c').read_text()
callbacks = {'0x551680':'replay_technique_set','0x551141':'replay_image',
    '0x552cae':'replay_model','0x55278e':'replay_effect','0x551c90':'replay_material',
    '0x550d80':'replay_physics_map_asset','0x550d9e':'replay_preset_asset',
    '0x5526e1':'replay_tracer','0x554ffe':'replay_map_entities'}
def translate(text):
    text = re.sub(r'\bu32\b', 'uint32_t', text)
    text = text.replace('uint32_t *ctx', 'codol_load_blocks_t *ctx')
    text = text.replace('ctx[32] + ctx[34]', 'ctx->source + ctx->source_position')
    for number, field in {34:'source_position',19:'position[3]',179:'format_version',
        168:'collect_asset_aliases',171:'dynamic_record_count',172:'dynamic_record_capacity'}.items():
        text = text.replace(f'ctx[{number}]', 'ctx->'+field)
    for address, callback in callbacks.items():
        text = text.replace('loaded_address('+address+')', callback)
    for old,new in {'archive_reserve':'reserve','archive_bytes':'(const uint32_t *)replay_bytes',
        'archive_string':'replay_string','archive_push':'CODOL_PushLoadBlock',
        'archive_pop':'CODOL_PopLoadBlock','archive_asset':'replay_asset_reference',
        'archive_record_asset':'record_asset','archive_water':'replay_water',
        'archive_sound':'replay_sound_name'}.items():
        text = text.replace(old, new)
    return text

name='src/codol/assets/codol_load_blocks.c'
s=read(name)
# Only layouts independently verified against the current consumer are shared.
# The 365 weapon parser is replaced below, not enabled by its version gate.
s=s.replace('s->format_version==365','(s->format_version==365 || s->format_version==423)')
s=s.replace('s->format_version!=365','(s->format_version!=365 && s->format_version!=423)')
s=s.replace('e[179]+1,48,4,apply','e[179]+1,s->format_version==423 ? 64 : 48,4,apply')
assert 'e[179]+1,48,4,apply' not in s
for old,new in [('replay_material','replay_material423'),('replay_weapon','replay_weapon423'),
                ('replay_tracer','replay_tracer423'),('replay_weapon_attachment','replay_attachment423'),
                ('replay_addon_map_entities','replay_addon427'),('replay_collision','replay_collision423')]:
    body=translate(function(raw,new)).replace('int '+new+'(', 'static int '+old+'(')
    if old=='replay_collision':
        body=body.replace('source, *entry;', 'source;')
        body=body.replace('entry = (uint32_t *)ctx[170] + ctx->dynamic_record_count * 5;\n                entry[0] = (uint32_t)h; entry[1] = (uint32_t)rows; entry[2] = i;\n                entry[3] = count; entry[4] = base;',
            'ctx->dynamic_records[ctx->dynamic_record_count] = (codol_dynamic_records_t){\n                    (const uint8_t *)h, (const uint8_t *)rows, i, count, base};')
    s=replace_function(s,old,body)
# Generic field helper uses real C callbacks, never old executable addresses.
helper=translate(function(raw,'fields'))
helper=helper.replace('uint32_t target = 0, i;', 'uint32_t i;\n    int (*target)(codol_load_blocks_t *,int,uint32_t *) = NULL;')
for address,callback in callbacks.items(): helper=helper.replace('target = '+address, 'target = '+callback)
helper=helper.replace('    if (target) target = loaded_address(target);\n','')
at=s.index('static int replay_material(codol_load_blocks_t *ctx,')
s=s[:at]+'static int replay_sound_name(codol_load_blocks_t *,uint32_t,int);\n' + \
    'enum { STRING, MODEL, EFFECT, MATERIAL, PHYSCOLL, PHYSPRESET, TRACER, SOUND };\n'+helper+'\n'+s[at:]
helpers='\n\n'.join(translate(function(raw,f)) for f in ['inline_array','plane_refs','collision_info_body','collision_info','collision_info_ref'])+'\n'
helpers=helpers.replace('uint32_t i, count = info[12] & 0xffff;\n    if (!info) return 0;',
    'uint32_t i, count;\n    if (!info) return 0;\n    count = info[12] & 0xffff;')
at=s.index('static int replay_addon_map_entities(')
s=s[:at]+helpers+s[at:]
s=replace_function(s,'replay_collision_planes','')
s=s.replace('return replay_map_entities_body(s,apply,reference,0);',
    'return replay_map_entities_body(s,apply,reference,s->format_version==423);')
s=s.replace('replay_bytes(s,16,140,4,apply)', 'replay_bytes(s,s->format_version==423 ? 19 : 16,140,4,apply)')
s=s.replace('i<560;', 'i<(s->format_version==423 ? 665 : 560);')
catalog=(ROOT / 'tools/native/story_catalog423.c').read_text()
catalog_helpers='\n\n'.join(translate(function(catalog,f)) for f in ['strings','indices','records','replay_catalog423'])
catalog_helpers=catalog_helpers.replace('int replay_catalog423(', 'static int replay_catalog423(')
at=s.index('int CODOL_ReplayZoneAsset(')
s=s[:at]+catalog_helpers+'\n\n'+s[at:]
s=s.replace('case 14: case 15: loader=replay_collision; break;',
    'case 14: case 17: case 18:\n        if (stream->format_version==423) return extent==0 ? 1 : -1;\n        loader=type==14 ? replay_collision : replay_game_world_mp; break;\n    case 15: loader=replay_collision; break;')
s=s.replace('    case 18: loader=replay_game_world_mp; break;\n','')
s=s.replace('case 44: loader=replay_netconststrings; break;',
    'case 44: loader=replay_netconststrings; break;\n    case 45: loader=replay_catalog423; break;')
s=s.replace('    /* Independent versioned extent traversal and block replay must agree. */', '''    if (ref<UINT32_MAX-1) {
        size_t alias;
        if (stream->format_version!=423 || extent || !ref || (ref-1)>>28!=3) return -1;
        /* Parents are appended after children. The registry is sorted only
         * after the entire zone has replayed, so do not binary-search here. */
        for (alias=0;alias<stream->asset_alias_count;++alias) {
            const codol_asset_alias_t *row=stream->asset_aliases+alias;
            if (row->reference==ref && row->asset.type==type && row->asset.format_version==423) return 1;
        }
        return -1;
    }
    /* Independent versioned extent traversal and block replay must agree. */''')
s=s.replace('    if (ref<UINT32_MAX-1) return -1;\n','')
assert 'ctx[' not in s and 'loaded_address' not in s
write(name,s)

# Scalar consumers retain legacy layouts where they are still used internally.
edits('src/codol/assets/codol_fastfile.c', [('version != 334 && version != 365','version != 334 && version != 423')])
s=read('src/codol/assets/codol_client_crypto.c')
s=s.replace('    if (version == 365) return decrypt_material(exe, CODOL_2697_RSA_DER_OFFSET, 1, encrypted, out, 40);',
    '    if (version == 423) return decrypt_material(exe, 0x859fa0u, 1, encrypted, out, 40);')
write('src/codol/assets/codol_client_crypto.c',s)
name='src/codol/assets/codol_asset_stream.c'
s=read(name).replace('version==365','(version==365 || version==423)').replace('version!=365','version!=365 && version!=423')
body=function(s,'CODOL_AdvanceMaterialStreamVersion')
body=body.replace('unsigned i;', 'unsigned i, shift=version==423 ? 8 : 0;')
body=body.replace('take(&p,size,1,96)', 'take(&p,size,1,96+shift)')
body=body.replace('((version==365 || version==423) ? 8 : 0)', '(version==423 ? 16 : version==365 ? 8 : 0)')
for offset in ['0x50','0x54','0x48','0x58','0x49','0x5c','0x4a']:
    body=body.replace('h+'+offset,'h+shift+'+offset)
s=replace_function(s,'CODOL_AdvanceMaterialStreamVersion',body);write(name,s)
for name in ['src/codol/assets/codol_xmodel_collision.c','src/codol/collision/codol_world_planes.c']:
    s=read(name)
    s=s.replace('asset->format_version==365','(asset->format_version==365 || asset->format_version==423)')
    write(name,s)
edits('src/codol/assets/codol_effects.c', [('e->visual_sample_count,48,','e->visual_sample_count,asset->format_version==423 ? 64 : 48,')])
edits('src/codol/assets/codol_effects.h', [('codol_effect_prefix_t prefix;','codol_effect_prefix_t prefix;\n    uint32_t format_version;')])
edits('src/codol/assets/codol_effects.c', [('pos=result.prefix.dependency_offset;', 'result.format_version=asset->format_version;\n    pos=result.prefix.dependency_offset;')])
edits('src/codol/assets/codol_effects_native.c', [('(size_t)s->visual_sample_count*48','(size_t)s->visual_sample_count*(source->format_version==423 ? 64 : 48)')])
edits('src/codol/assets/codol_material_native.c', [
    ('flags=source->asset.format_version==365 ? 12 : 4;', 'flags=source->asset.format_version==423 ? 20 : source->asset.format_version==365 ? 12 : 4;'),
    ('h+16,4', 'h+(source->asset.format_version==423 ? 24 : 16),4')])
name='src/codol/assets/codol_netconst.c'
write(name,read(name).replace('!=365','!=423'))
name='src/codol/assets/codol_asset_registry.c';s=read(name)
a=s.index('static const char *dependency_asset_name(const archive_t *archive,')
# Only mounting/registry gates here, not unported weapon decoding branches.
s=s[:a].replace('365','423')+s[a:]
s=s.replace('if (asset->type==28 && asset->format_version==365) header=0xc34;',
    '''if (asset->type==28 && asset->format_version==365) header=0xc34;
    if (asset->format_version==423) {
        if (asset->type==5) header=104;
        if (asset->type==28) header=0xe28;
        if (asset->type==40) header=116;
    }''')
s=s.replace('asset->type==5 && asset->format_version==365 ? 8 : 0',
    'asset->type==5 ? (asset->format_version==423 ? 16 : asset->format_version==365 ? 8 : 0) : 0')
old='archive=find_dependency_definition(type,result.name[0]==\',\' ? result.name+1 : result.name,&result.asset);'
# Explicit physics placeholder semantics verified at client 0x49e570.
start=s.index('int CODOL_LoadMountedDynamicDependency(')
tail=s[start:];assert old in tail
tail=tail.replace(old,'''{
            codol_asset_t placeholder=result.asset;
            archive=find_dependency_definition(type,result.name[0]==',' ? result.name+1 : result.name,&result.asset);
            if (!archive && type==0 && placeholder.format_version==423 && placeholder.size>=70 &&
                world_u32(placeholder.data)==UINT32_MAX && placeholder.data[68]==',' &&
                result.name==(const char *)placeholder.data+68 && result.name[1])
                archive=find_dependency_definition(0,"default",&result.asset);
        }''',1)
s=s[:start]+tail;write(name,s)
edits('src/codol/assets/codol_archive_probe.c', [
    ('header=asset->type==0 ? 68 : asset->type==43 ? 12 : 96;', 'header=asset->type==0 ? 68 : asset->type==43 ? 12 : asset->format_version==423 ? 104 : 96;'),
    ('asset->type==5 && asset->format_version==365 ? 8 : 0', 'asset->type==5 ? (asset->format_version==423 ? 16 : asset->format_version==365 ? 8 : 0) : 0')])

# Generate reproducible patch; source is still the verified read-only archive.
patch=ROOT / 'tools/native/server3333.patch'
names={line[6:] for line in patch.read_text().splitlines() if line.startswith('--- a/')}
names.update(changed)
patch.write_text(''.join(line for name in sorted(names) for line in difflib.unified_diff(
    (REF/name).read_text().splitlines(True), (PORT/name).read_text().splitlines(True),
    fromfile='a/'+name,tofile='b/'+name)),newline='\n')
print('ported resource source',len(changed),'files')
