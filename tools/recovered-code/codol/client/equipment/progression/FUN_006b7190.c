// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.progression
// Analyst label: WL_GetWeaponRank 界面回调
// VA: 0x006b7190; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_8dcf063ede6febe5f1fdcb5416895285a3c264d45f8765a5f689880a2e9943ff
// BEGIN PSEUDOCODE

void FUN_006b7190(int *param_1)

{
  int iVar1;
  byte bVar2;
  int iVar3;
  undefined1 local_38 [28];
  undefined4 local_1c;
  
  if (*(int *)(param_1[4] + 0x10) == 0) {
    iVar3 = 0;
  }
  else {
    FUN_00695bc0(*(int *)(param_1[4] + 0x10),local_38);
    iVar3 = FUN_005845b0();
    if (iVar3 == 0) {
      bVar2 = 10;
    }
    else {
      bVar2 = *(byte *)(iVar3 + 6);
    }
    iVar3 = FUN_0046eb20(local_1c,bVar2 < 6);
  }
  iVar1 = *param_1;
  if ((*(uint *)(iVar1 + 0xc) >> 6 & 1) != 0) {
    (**(code **)(**(int **)(iVar1 + 8) + 8))(iVar1,*(undefined4 *)(iVar1 + 0x10));
    *(undefined4 *)(iVar1 + 8) = 0;
  }
  *(int *)(iVar1 + 0x10) = iVar3 + 1;
  *(undefined4 *)(iVar1 + 0xc) = 3;
  return;
}

