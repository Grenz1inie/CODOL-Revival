// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.loadout
// Analyst label: 当前选择项编码 ID 读取
// VA: 0x00706740; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

uint FUN_00706740(void)

{
  int in_EAX;
  uint uVar1;
  
  if (*(char *)(in_EAX * 8 + 0x7809fa0) != '\0') {
    uVar1 = *(uint *)(in_EAX * 8 + 0x7809fa4) ^ _DAT_00cd64c0;
    return uVar1 << 8 | uVar1 >> 0x18;
  }
  return 0;
}

