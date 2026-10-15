// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.currency
// Analyst label: GetCP 界面回调
// VA: 0x006af9e0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_dd6bb905f94dd76417cc7905a7698bf3275482f637de8665cb25f4a4ebc9fb00
// BEGIN PSEUDOCODE

void FUN_006af9e0(int *param_1)

{
  char *pcVar1;
  int iVar2;
  undefined4 uVar3;
  
  iVar2 = 0;
  pcVar1 = &DAT_0ba0b2c8;
  do {
    if (*pcVar1 == '\x01') {
      uVar3 = *(undefined4 *)(&DAT_0ba0b2cc + iVar2 * 0x20);
      goto LAB_006afa02;
    }
    pcVar1 = pcVar1 + 0x20;
    iVar2 = iVar2 + 1;
  } while ((int)pcVar1 < 0xba0b308);
  uVar3 = 0;
LAB_006afa02:
  iVar2 = *param_1;
  if ((*(uint *)(iVar2 + 0xc) >> 6 & 1) != 0) {
    (**(code **)(**(int **)(iVar2 + 8) + 8))(iVar2,*(undefined4 *)(iVar2 + 0x10));
    *(undefined4 *)(iVar2 + 8) = 0;
  }
  *(undefined4 *)(iVar2 + 0x10) = uVar3;
  *(undefined4 *)(iVar2 + 0xc) = 3;
  return;
}

