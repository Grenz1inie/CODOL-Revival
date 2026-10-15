// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 资产请求和结果绑定
// VA: 0x004a5120; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_753b822071512c172aea6e1d3b587980eb2e1da9998b38c837defd2598498d7d
// BEGIN PSEUDOCODE

void FUN_004a5120(undefined4 param_1,undefined4 param_2)

{
  int iVar1;
  LONG LVar2;
  int iVar3;
  int iVar4;
  undefined4 *puVar5;
  code *pcVar6;
  code *pcVar7;
  undefined4 *local_c;
  undefined4 *local_8;
  
  iVar4 = 0;
  iVar1 = FUN_006fed10();
  if ((iVar1 != 0) && (iVar1 = FUN_00a3c920(), iVar1 == 2)) {
    iVar4 = FUN_00a421e0(&DAT_00c4e869);
  }
  iVar3 = 0;
  iVar1 = FUN_006fed10();
  if ((iVar1 != 0) && (iVar1 = FUN_00a3c920(), iVar1 == 2)) {
    iVar3 = FUN_00a42310(&DAT_00c4e869);
  }
  if (iVar4 == 0) {
    return;
  }
  if (iVar3 == 0) {
    return;
  }
  FUN_00a472b0(&local_c,&DAT_07bdc6f8);
  FUN_00a4bfc0(&local_8,param_2,1);
  if (local_c != (undefined4 *)0x0) {
    if (local_8 == (undefined4 *)0x0) goto LAB_004a524d;
    pcVar7 = FUN_004a5080;
    pcVar6 = FUN_004a5680;
    puVar5 = local_c;
    if (local_c != (undefined4 *)0x0) {
      InterlockedIncrement(local_c + 1);
    }
    FUN_006f6070(0x6b,puVar5,pcVar6,pcVar7);
    pcVar7 = FUN_004a4890;
    pcVar6 = FUN_004a5650;
    puVar5 = local_8;
    if (local_8 != (undefined4 *)0x0) {
      InterlockedIncrement(local_8 + 1);
    }
    FUN_006f6070(0x52,puVar5,pcVar6,pcVar7);
    DAT_07817dd7 = 1;
  }
  if ((local_8 != (undefined4 *)0x0) && (LVar2 = InterlockedDecrement(local_8 + 1), LVar2 == 0)) {
    if (local_8 != (undefined4 *)0x0) {
      (**(code **)*local_8)(1);
    }
    local_8 = (undefined4 *)0x0;
  }
LAB_004a524d:
  if (((local_c != (undefined4 *)0x0) && (LVar2 = InterlockedDecrement(local_c + 1), LVar2 == 0)) &&
     (local_c != (undefined4 *)0x0)) {
    (**(code **)*local_c)(1);
  }
  return;
}

