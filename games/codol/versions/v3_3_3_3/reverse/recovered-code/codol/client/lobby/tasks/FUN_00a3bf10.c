// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 远程任务缓冲区准备及最终提交包装
// VA: 0x00a3bf10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-task-dispatch.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_00a3bf10(undefined4 *param_1,undefined4 *param_2)

{
  int iVar1;
  int iVar2;
  int *unaff_FS_OFFSET;
  int iStack_10;
  undefined *puStack_c;
  uint uStack_8;
  
  puStack_c = &DAT_00b40b30;
  iStack_10 = *unaff_FS_OFFSET;
  *unaff_FS_OFFSET = (int)&iStack_10;
  uStack_8 = 0;
  if ((*(char *)(param_2 + 5) != '\0') || (param_2[6] != 0)) {
    func_0x00a53d80();
  }
  if ((((*(char *)(param_2 + 5) == '\0') && (param_2[6] == 0)) && (*(char *)(param_2 + 3) != '\0'))
     && ((param_2[4] != 0 && (*(int *)(param_2[4] + 0xc) != 0)))) {
    func_0x00a3b170();
    uStack_8 = CONCAT31(uStack_8._1_3_,1);
    if (param_1 != (undefined4 *)0x0) {
      InterlockedIncrement(param_1 + 1);
    }
    iVar1 = func_0x00a3b8a0();
    if (iVar1 == 0) {
      iVar2 = param_2[8];
      if (((*(char *)(param_2 + 3) != '\0') && ((iVar2 != 0 || (param_2[9] != 0)))) &&
         (param_2[10] != 0)) {
        if (iVar2 == 0) {
          func_0x00a44d20(param_2[9],param_2[10]);
        }
        else {
          func_0x00a44d00(iVar2);
        }
      }
    }
    else {
      func_0x00a53d80(iVar1);
    }
    uStack_8 = uStack_8 & 0xffffff00;
    if (param_2 != (undefined4 *)0x0) {
      iVar2 = InterlockedDecrement(param_2 + 1);
      if (iVar2 == 0) {
        (**(code **)*param_2)(1);
      }
    }
  }
  else {
    func_0x00a53d80();
    iVar1 = 5;
  }
  uStack_8 = 0xffffffff;
  if (param_1 != (undefined4 *)0x0) {
    iVar2 = InterlockedDecrement(param_1 + 1);
    if ((iVar2 == 0) && (param_1 != (undefined4 *)0x0)) {
      (**(code **)*param_1)(1);
    }
  }
  *unaff_FS_OFFSET = iStack_10;
  return iVar1;
}

