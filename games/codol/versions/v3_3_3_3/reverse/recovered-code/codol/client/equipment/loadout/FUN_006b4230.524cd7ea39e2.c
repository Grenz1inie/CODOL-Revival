// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.loadout
// Analyst label: WL_EquipWeapon 回调
// VA: 0x006b4230; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006b4230(int param_1)

{
  int iVar1;
  char cVar2;
  uint uVar3;
  int extraout_EDX;
  
  iVar1 = _DAT_078a0470;
  cVar2 = *(char *)(*(int *)(param_1 + 0x10) + 0x30);
  func_0x006bf130();
  iVar1 = iVar1 * 0x3c;
  if (extraout_EDX < 1) {
    *(undefined4 *)(iVar1 + 0x78a0480) = 0;
    *(undefined1 *)(iVar1 + 0x78a047c) = 0;
  }
  else {
    uVar3 = (extraout_EDX << 0x18 | extraout_EDX >> 8) ^ _DAT_00cd64c0;
    *(undefined1 *)(iVar1 + 0x78a047c) = 1;
    *(uint *)(iVar1 + 0x78a0480) = uVar3;
  }
  _DAT_078a0468 = extraout_EDX;
  if (cVar2 == '\0') {
    FUN_006c1e70(extraout_EDX);
  }
  func_0x00699de0();
  func_0x0056dbf0();
  return;
}

