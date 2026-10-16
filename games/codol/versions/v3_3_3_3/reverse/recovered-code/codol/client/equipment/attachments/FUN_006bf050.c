// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: 武器与六槽配件组合有效性检查
// VA: 0x006bf050; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_006bf050(undefined4 param_1)

{
  char cVar1;
  int iVar2;
  int iVar3;
  
  if ((_DAT_077ea4ec == 0) ||
     ((-1 < _DAT_077ea4ec && (cVar1 = func_0x006c4160(param_1), cVar1 != '\0')))) {
    iVar3 = 0;
    iVar2 = _DAT_077ea4ec;
    while( true ) {
      if ((*(int *)(&DAT_077ea4fc + iVar3 * 4) != 0) &&
         ((*(int *)(&DAT_077ea4fc + iVar3 * 4) < 0 ||
          (cVar1 = func_0x006c41c0(iVar2), iVar2 = _DAT_077ea4ec, cVar1 == '\0')))) break;
      iVar3 = iVar3 + 1;
      if (5 < iVar3) {
        return 1;
      }
    }
  }
  return 0;
}

