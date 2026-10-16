// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.currency
// Analyst label: 游戏币与点券请求路由
// VA: 0x004a4930; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_296d2b93b307371b810e1d9bb5bd50342d8da71f42587013205af1e8d834737e
// BEGIN PSEUDOCODE

undefined4 FUN_004a4930(undefined4 param_1,undefined4 param_2)

{
  int iVar1;
  LONG LVar2;
  int iVar3;
  int iVar4;
  code *pcVar5;
  code *pcVar6;
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
  if ((iVar4 != 0) && (iVar3 != 0)) {
    FUN_00a461d0(&local_c,param_1,1);
    FUN_00a4bfc0(&local_8,param_2,1);
    if (local_c == (undefined4 *)0x0) {
      if ((local_8 != (undefined4 *)0x0) && (LVar2 = InterlockedDecrement(local_8 + 1), LVar2 == 0))
      {
        if (local_8 != (undefined4 *)0x0) {
          (**(code **)*local_8)(1);
        }
        local_8 = (undefined4 *)0x0;
      }
    }
    else if (local_8 != (undefined4 *)0x0) {
      pcVar6 = FUN_004a47f0;
      pcVar5 = FUN_004a4ab0;
      if (local_c != (undefined4 *)0x0) {
        InterlockedIncrement(local_c + 1);
      }
      FUN_006f6070(0x52,local_c,pcVar5,pcVar6);
      pcVar6 = FUN_004a4890;
      pcVar5 = FUN_004a4ab0;
      if (local_8 != (undefined4 *)0x0) {
        InterlockedIncrement(local_8 + 1);
      }
      FUN_006f6070(0x52,local_8,pcVar5,pcVar6);
      DAT_07817dd7 = 1;
      FUN_00b24750();
      FUN_00b24750();
      return 1;
    }
    if (((local_c != (undefined4 *)0x0) && (LVar2 = InterlockedDecrement(local_c + 1), LVar2 == 0))
       && (local_c != (undefined4 *)0x0)) {
      (**(code **)*local_c)(1);
    }
  }
  return 0;
}

