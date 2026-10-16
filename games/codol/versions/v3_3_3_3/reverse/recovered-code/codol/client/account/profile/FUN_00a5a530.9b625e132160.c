// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 私有档案保存任务 8/6
// VA: 0x00a5a530; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 * FUN_00a5a530(undefined4 *param_1,undefined4 param_2,undefined4 param_3,int *param_4)

{
  int *piVar1;
  char cVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  int *unaff_FS_OFFSET;
  int iStack_10;
  undefined *puStack_c;
  uint uStack_8;
  
  piVar1 = param_4;
  puStack_c = &DAT_00b43b0c;
  iStack_10 = *unaff_FS_OFFSET;
  uVar3 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  *param_1 = 0;
  uStack_8 = 0;
  iVar4 = (**(code **)(*param_4 + 4))(uVar3);
  iVar5 = func_0x00a38020(0x2c);
  uStack_8 = 1;
  if (iVar5 == 0) {
    param_4 = (undefined4 *)0x0;
  }
  else {
    param_4 = (int *)FUN_00a62db0(iVar4 + 0x53,1);
  }
  if (param_4 != (undefined4 *)0x0) {
    InterlockedIncrement(param_4 + 1);
  }
  uStack_8 = 2;
  FUN_00a3b1b0(&param_4,8,6);
  cVar2 = func_0x00a389a0(param_2,param_3);
  (**(code **)piVar1[2])(param_4);
  if (cVar2 == '\x01') {
    iVar4 = FUN_00a3be40(param_1,&param_4);
    if (iVar4 != 0) {
      func_0x00a53d80(iVar4);
    }
  }
  uStack_8 = uStack_8 & 0xffffff00;
  if (param_4 != (undefined4 *)0x0) {
    iVar4 = InterlockedDecrement(param_4 + 1);
    if ((iVar4 == 0) && (param_4 != (undefined4 *)0x0)) {
      (**(code **)*param_4)(1);
    }
  }
  *unaff_FS_OFFSET = iStack_10;
  return param_1;
}

