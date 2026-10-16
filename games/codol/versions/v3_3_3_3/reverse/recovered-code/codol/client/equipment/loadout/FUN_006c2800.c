// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.loadout
// Analyst label: 当前选择项分类不为 3 的判定
// VA: 0x006c2800; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

bool FUN_006c2800(void)

{
  int in_EAX;
  int iVar1;
  uint uVar2;
  int unaff_ESI;
  
  if (in_EAX == -1) {
    FUN_007051e0();
  }
  if (*(char *)(unaff_ESI * 8 + 0x7809fa0) == '\0') {
    uVar2 = 0;
  }
  else {
    uVar2 = *(uint *)(unaff_ESI * 8 + 0x7809fa4) ^ _DAT_00cd64c0;
    uVar2 = uVar2 << 8 | uVar2 >> 0x18;
  }
  iVar1 = func_0x006c2780(uVar2);
  return iVar1 != 3;
}

