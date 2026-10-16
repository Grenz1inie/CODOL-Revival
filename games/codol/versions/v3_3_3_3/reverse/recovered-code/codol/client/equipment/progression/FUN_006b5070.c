// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.progression
// Analyst label: 武器最高等级的界面消费
// VA: 0x006b5070; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_47c1325bf052c139c07a7eb1f3bd3ffb507d6b07a36e861c1d2c32bfe1659845
// BEGIN PSEUDOCODE

void FUN_006b5070(int *param_1)

{
  int iVar1;
  byte bVar2;
  int iVar3;
  int iVar4;
  undefined4 uVar5;
  uint uVar6;
  
  iVar1 = *(int *)(param_1[4] + 0x10);
  iVar4 = *param_1;
  if (param_1[1] != 0) {
    iVar3 = FUN_006bed90();
    FUN_00719d30(iVar4);
    if (iVar3 != 0) {
      FUN_006bee50();
    }
  }
  uVar6 = *(uint *)(iVar4 + 0xc) & 0x8f;
  if (uVar6 != 1) {
    if (uVar6 != 0) {
      if ((iVar1 == 0) || (iVar4 = FUN_005845b0(), iVar4 == 0)) {
        bVar2 = 10;
      }
      else {
        bVar2 = *(byte *)(iVar4 + 6);
      }
      uVar5 = FUN_0046ee30(bVar2 < 6);
      FUN_006b4ca0(*param_1,iVar1,uVar5);
      return;
    }
    return;
  }
  return;
}

