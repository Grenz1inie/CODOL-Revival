// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.progression
// Analyst label: 引导角色或特殊物品的库存缺省判定
// VA: 0x00695a10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

undefined4 FUN_00695a10(void)

{
  char cVar1;
  int iVar2;
  int unaff_ESI;
  undefined *puStack_14;
  int iStack_10;
  undefined4 uStack_c;
  
  puStack_14 = &UNK_00c78d5c;
  iStack_10 = func_0x006da140();
  iStack_10 = iStack_10 + 0x90;
  uStack_c = 0x7ffc;
  iVar2 = func_0x00592930(&puStack_14);
  if (unaff_ESI == iVar2) {
    return 1;
  }
  if ((0 < unaff_ESI) && (cVar1 = func_0x00706700(), cVar1 != '\0')) {
    return 1;
  }
  return 0;
}

