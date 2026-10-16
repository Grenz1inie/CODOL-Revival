from pathlib import Path
import difflib
import re
ROOT = Path(__file__).resolve().parents[7]
STAGE=ROOT/'research/experiments/story-native'
PORT=STAGE/'server3333';REF=STAGE/'reference-source'
changed=set()
def read(name):return (PORT/name).read_text()
def write(name,s):
    (PORT/name).write_text(s,newline='\n');changed.add(name)
def edits(name,changes):
    s=read(name)
    for before,after in changes:
        assert before in s,(name,before)
        s=s.replace(before,after)
    write(name,s)
def bounds(text,name):
    m=re.search(r'^(?:static )?(?:int|u32) '+name+r'\([^;]*?\)\s*\{',text,re.M)
    assert m,name
    i=text.index('{',m.start())+1;depth=1
    while depth:
        if text[i]=='{':depth+=1
        if text[i]=='}':depth-=1
        i+=1
    return m.start(),i
def getfunc(text,name):
    a,b=bounds(text,name);return text[a:b]
def replacefunc(text,name,value):
    a,b=bounds(text,name);return text[:a]+value+text[b:]

raw=(ROOT/'games/codol/versions/v3_3_3_3/reverse/tools/native/story_collision423.c').read_text()
helper=raw[raw.index('typedef struct'):]
a,b=bounds(helper,'word');helper=helper[:a]+helper[b:]
helper=re.sub(r'\bu32\b','uint32_t',helper).replace('word(', 'u32(')
helper=helper.replace('Cursor','collision_cursor423_t')
helper=helper.replace('uint32_t size, pos;', 'size_t size, pos;')
for name in ['take','string','section','planes']:
    helper=re.sub(r'\b'+name+r'\(',name+'423(',helper)
helper=replacefunc(helper,'section423','''static int section423(collision_cursor423_t *c,codol_collision_layout_t *layout,
    uint32_t row,uint32_t count,uint32_t stride,uint32_t pointer)
{
    codol_collision_span_t *out=layout->sections+row;
    out->offset=pointer==INLINE ? c->pos : SIZE_MAX;
    out->count=count; out->stride=stride; out->reference=pointer;
    if (!pointer && count) return 0;
    return pointer!=INLINE || take423(c,count,stride);
}''')
helper=helper.replace('int read_collision_layout423(const uint32_t *asset, uint32_t *layout)',
    'static int read_collision_layout423(const codol_asset_t *asset,codol_collision_layout_t *out)')
helper=helper.replace('    collision_cursor423_t c;', '    collision_cursor423_t c;\n    codol_collision_layout_t layout={0};')
helper=helper.replace('!asset || !layout', '!asset || !out')
for index,field in {0:'type',1:'data',2:'size',3:'format_version'}.items():
    helper=helper.replace(f'asset[{index}]','asset->'+field)
helper=helper.replace('    for (i = 0; i < 86; ++i) layout[i] = 0;\n','')
helper=helper.replace('section423(&c, layout,','section423(&c, &layout,')
def slot(m):
    index=int(m[1])
    if index==84:return 'layout.map_entities'
    if index==85:return 'layout.name_reference'
    return f'layout.sections[{index//4}].'+['offset','count','stride','reference'][index%4]
helper=re.sub(r'layout\[(\d+)\]',slot,helper)
helper=helper.replace('    return 1;\n#undef SECTION', '    *out=layout; return 1;\n#undef SECTION')
helper+='\n#undef INLINE\n'
name='src/codol/collision/codol_collision_stream.c';s=read(name)
s=s.replace('#include <string.h>','#include <string.h>\n#include <stdlib.h>')
at=s.index('int CODOL_ReadCollisionLayout(')
s=s[:at]+helper+'\n'+s[at:]
s=s.replace('    uint32_t h[64];', '    if (asset && asset->format_version==423) return read_collision_layout423(asset,out);\n    uint32_t h[64];')
s=replacefunc(s,'CODOL_ReadCollisionMapEntities','''int CODOL_ReadCollisionMapEntities(const codol_asset_t *asset,codol_map_entities_t *out)
{
    size_t offset,size;
    uint8_t *copy;
    int ok;
    if (!out || !CODOL_LocateCollisionMapEntities(asset,&offset)) return 0;
    if (asset->format_version!=423) return CODOL_ReadMapEntities(asset->data+offset,asset->size-offset,out);
    /* 423 moves the stage pointer/count from MapEnts into clipMap (+156/+160).
     * The native parser owns its copied strings/arrays before this view dies. */
    size=asset->size-offset;
    if (size<36 || size>CODOL_ASSET_LIMIT-8) return 0;
    copy=malloc(size+8);
    if (!copy) return 0;
    memcpy(copy,asset->data+offset,36);
    memcpy(copy+36,asset->data+156,4);
    memset(copy+40,0,4); copy[40]=asset->data[160];
    memcpy(copy+44,asset->data+offset+36,size-36);
    ok=CODOL_ReadMapEntities(copy,size+8,out);
    free(copy); return ok;
}''')
write(name,s)
edits('src/codol/collision/codol_collision_leaves.c',[
    ('layout.sections[CODOL_COLL_SUBMODELS].offset+68*i','layout.sections[CODOL_COLL_SUBMODELS].offset+layout.sections[CODOL_COLL_SUBMODELS].stride*i'),
    ('leaf(p+28,&layout,&m->leaf)','leaf(p+(asset->format_version==423 ? 32 : 28),&layout,&m->leaf)')])
name='src/codol/collision/codol_collision_map.c';s=read(name)
s=s.replace('    map.checksum=(uint32_t)collision->data[204]|(uint32_t)collision->data[205]<<8|\n        (uint32_t)collision->data[206]<<16|(uint32_t)collision->data[207]<<24;',
    '''    {
        const uint8_t *checksum=collision->data+(collision->format_version==423 ? 232 : 204);
        map.checksum=(uint32_t)checksum[0]|(uint32_t)checksum[1]<<8|
            (uint32_t)checksum[2]<<16|(uint32_t)checksum[3]<<24;
    }''')
write(name,s)
edits('src/codol/collision/codol_dynents.c',[
    ('collision->data+168+2*category','collision->data+(collision->format_version==423 ? 196 : 168)+2*category')])

raw=(ROOT/'games/codol/versions/v3_3_3_3/reverse/tools/native/story_runtime423.c').read_text()
body=getfunc(raw,'read_addon_entities423')
body=body.replace('int read_addon_entities423(const unsigned char *source, u32 size, u32 *out)',
    'int CODOL_ReadAddonMapEntities(const void *data,size_t size,codol_map_entities_t *out)')
body=body.replace('    const u32 *h', '    const unsigned char *source=data;\n    const u32 *h')
body=re.sub(r'\bu32\b','uint32_t',body)
body=body.replace('native_read_map_body','read_map_entities')
name='src/codol/collision/codol_map_entities.c';s=replacefunc(read(name),'CODOL_ReadAddonMapEntities',body)
write(name,s)

patch=ROOT/'games/codol/versions/v3_3_3_3/reverse/tools/native/server3333.patch'
names={line[6:] for line in patch.read_text().splitlines() if line.startswith('--- a/')}
names.update(changed)
patch.write_text(''.join(line for name in sorted(names) for line in difflib.unified_diff(
    (REF/name).read_text().splitlines(True),(PORT/name).read_text().splitlines(True),
    fromfile='a/'+name,tofile='b/'+name)),newline='\n')
print('ported collision source',len(changed),'files')
