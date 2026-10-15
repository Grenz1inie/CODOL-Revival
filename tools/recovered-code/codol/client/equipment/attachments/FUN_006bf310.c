// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: 配件编辑槽的编码值和有效标志写入
// VA: 0x006bf310; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006bf310(int param_1)

{
  int in_ECX;
  int in_EDX;
  uint uVar1;
  
  param_1 = param_1 * 0x3c;
  if (*(char *)(param_1 + 0x78a0478) != '\0') {
    if (0 < in_ECX) {
      uVar1 = (in_ECX << 0x18 | in_ECX >> 8) ^ _DAT_00cd64c0;
      *(undefined1 *)(param_1 + 0x78a0484 + in_EDX * 8) = 1;
      *(uint *)(param_1 + 0x78a0488 + in_EDX * 8) = uVar1;
      return;
    }
    *(undefined4 *)(param_1 + 0x78a0488 + in_EDX * 8) = 0;
    *(undefined1 *)(param_1 + 0x78a0484 + in_EDX * 8) = 0;
  }
  return;
}

