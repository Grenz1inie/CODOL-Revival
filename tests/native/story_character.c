/* Current public schema seam; allocator/engine state is not started. */
#include "codol_profile.h"
#include <string.h>

__declspec(dllexport) int story_character_read(const uint8_t *profile,
    const uint8_t *offsets, size_t offsets_size, uint32_t checksum,
    unsigned record_size, uint16_t *out)
{
    codol_structured_property_t root[]={
        {"characterClasses",{6,1},576,{0,0}},
        {"currentCharacterIndex",{1,0},697,{0,0}}};
    codol_structured_property_t slots={"slots",{6,0},1,{0,0}};
    codol_structured_struct_t structures[]={
        {2,14426,78891,3414,root},{1,40,0,10,&slots}};
    codol_structured_array_t arrays[]={{9,{0,0},4},{12,{5,1},40}};
    codol_structured_definition_t def={0};
    codol_structured_schema_t schema={"mp/playerdata.def",1,&def};
    codol_profile_character_t selected;
    def.version=233;def.checksum=checksum;def.root=(codol_structured_type_t){5,0};
    def.struct_count=2;def.structs=structures;
    def.indexed_count=2;def.indexed_arrays=arrays;
    def.layout=(codol_structured_layout_t){offsets,offsets_size,record_size};
    if(!CODOL_ProfileCharacter(profile,32768,&schema,"tf",&selected))return 0;
    out[0]=(uint16_t)selected.character_index;
    memcpy(out+1,selected.target_slots,sizeof(selected.target_slots));
    return 1;
}
