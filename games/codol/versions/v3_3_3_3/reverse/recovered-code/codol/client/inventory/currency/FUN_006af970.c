// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.currency
// Analyst label: GetCC 界面回调
// VA: 0x006af970; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_f0c881a331858e72900836fedf11e8cb87c22838c1c2da4c8bc3dc6458447b42
// BEGIN PSEUDOCODE

void FUN_006af970(int *param_1)

{
  char *pcVar1;
  int iVar2;
  undefined4 uVar3;
  
  iVar2 = 0;
  pcVar1 = &DAT_0ba0b2c8;
  do {
    if (*pcVar1 == '\x02') {
      uVar3 = *(undefined4 *)(&DAT_0ba0b2cc + iVar2 * 0x20);
      goto LAB_006af992;
    }
    pcVar1 = pcVar1 + 0x20;
    iVar2 = iVar2 + 1;
  } while ((int)pcVar1 < 0xba0b308);
  uVar3 = 0;
LAB_006af992:
  iVar2 = *param_1;
  if ((*(uint *)(iVar2 + 0xc) >> 6 & 1) != 0) {
    (**(code **)(**(int **)(iVar2 + 8) + 8))(iVar2,*(undefined4 *)(iVar2 + 0x10));
    *(undefined4 *)(iVar2 + 8) = 0;
  }
  *(undefined4 *)(iVar2 + 0x10) = uVar3;
  *(undefined4 *)(iVar2 + 0xc) = 3;
  return;
}

