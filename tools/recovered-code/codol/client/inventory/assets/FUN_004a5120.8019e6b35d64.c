// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 资产请求和结果绑定
// VA: 0x004a5120; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

void FUN_004a5120(undefined4 param_1,undefined4 param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined4 *puVar4;
  code *pcVar5;
  undefined *puVar6;
  undefined *puVar7;
  undefined4 *puStack_c;
  undefined4 *puStack_8;
  
  iVar3 = 0;
  iVar1 = func_0x006fed10();
  if ((iVar1 != 0) && (iVar1 = func_0x00a3c920(), iVar1 == 2)) {
    iVar3 = func_0x00a421e0(&UNK_00c4e869);
  }
  iVar2 = 0;
  iVar1 = func_0x006fed10();
  if ((iVar1 != 0) && (iVar1 = func_0x00a3c920(), iVar1 == 2)) {
    iVar2 = func_0x00a42310(&UNK_00c4e869);
  }
  if (iVar3 == 0) {
    return;
  }
  if (iVar2 == 0) {
    return;
  }
  FUN_00a472b0(&puStack_c,0x7bdc6f8);
  func_0x00a4bfc0(&puStack_8,param_2,1);
  if (puStack_c != (undefined4 *)0x0) {
    if (puStack_8 == (undefined4 *)0x0) goto LAB_004a524d;
    puVar6 = &UNK_004a5080;
    pcVar5 = FUN_004a5680;
    puVar4 = puStack_c;
    if (puStack_c != (undefined4 *)0x0) {
      InterlockedIncrement(puStack_c + 1);
    }
    FUN_006f6070(0x6b,puVar4,pcVar5,puVar6);
    puVar7 = &UNK_004a4890;
    puVar6 = &UNK_004a5650;
    puVar4 = puStack_8;
    if (puStack_8 != (undefined4 *)0x0) {
      InterlockedIncrement(puStack_8 + 1);
    }
    FUN_006f6070(0x52,puVar4,puVar6,puVar7);
    DAT_07817dd7 = 1;
  }
  if ((puStack_8 != (undefined4 *)0x0) && (iVar1 = InterlockedDecrement(puStack_8 + 1), iVar1 == 0))
  {
    if (puStack_8 != (undefined4 *)0x0) {
      (**(code **)*puStack_8)(1);
    }
    puStack_8 = (undefined4 *)0x0;
  }
LAB_004a524d:
  if (((puStack_c != (undefined4 *)0x0) && (iVar1 = InterlockedDecrement(puStack_c + 1), iVar1 == 0)
      ) && (puStack_c != (undefined4 *)0x0)) {
    (**(code **)*puStack_c)(1);
  }
  return;
}

