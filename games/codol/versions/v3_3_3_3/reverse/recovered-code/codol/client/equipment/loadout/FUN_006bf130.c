// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.loadout
// Analyst label: 装备槽位上下文辅助
// VA: 0x006bf130; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/profile-write.json
// BEGIN PSEUDOCODE

void FUN_006bf130(void)

{
  int iVar1;
  int in_ECX;
  
  iVar1 = in_ECX * 0x3c;
  *(undefined1 *)(iVar1 + 0x78a0478) = 1;
  *(undefined4 *)(iVar1 + 0x78a0480) = 0;
  *(undefined1 *)(iVar1 + 0x78a047c) = 0;
  *(undefined1 *)(iVar1 + 0x78a0484) = 0;
  *(undefined4 *)(iVar1 + 0x78a0488) = 0;
  *(undefined4 *)(iVar1 + 0x78a0490) = 0;
  *(undefined1 *)(iVar1 + 0x78a048c) = 0;
  *(undefined4 *)(iVar1 + 0x78a0498) = 0;
  *(undefined1 *)(iVar1 + 0x78a0494) = 0;
  *(undefined4 *)(iVar1 + 0x78a04a0) = 0;
  *(undefined1 *)(iVar1 + 0x78a049c) = 0;
  *(undefined4 *)(iVar1 + 0x78a04a8) = 0;
  *(undefined1 *)(iVar1 + 0x78a04a4) = 0;
  *(undefined4 *)(iVar1 + 0x78a04b0) = 0;
  *(undefined1 *)(iVar1 + 0x78a04ac) = 0;
  return;
}

