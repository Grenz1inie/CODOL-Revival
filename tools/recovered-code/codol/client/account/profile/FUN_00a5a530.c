// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 私有档案保存任务 8/6
// VA: 0x00a5a530; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_37adaed9d139608621986c84f87a7f3b3b4792d3bdcd6ccefebec572c8a67d02
// BEGIN PSEUDOCODE

undefined4 * FUN_00a5a530(undefined4 *param_1,undefined4 param_2,undefined4 param_3,int *param_4)

{
  int *piVar1;
  char cVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  LONG LVar6;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  piVar1 = param_4;
  puStack_c = &LAB_00b43b0c;
  local_10 = ExceptionList;
  uVar3 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  *param_1 = 0;
  local_8 = 0;
  iVar4 = (**(code **)(*param_4 + 4))(uVar3);
  iVar5 = FUN_00a38020(0x2c);
  local_8 = 1;
  if (iVar5 == 0) {
    param_4 = (undefined4 *)0x0;
  }
  else {
    param_4 = (int *)FUN_00a62db0(iVar4 + 0x53,1);
  }
  if (param_4 != (undefined4 *)0x0) {
    InterlockedIncrement(param_4 + 1);
  }
  local_8 = 2;
  FUN_00a3b1b0(&param_4,8,6);
  cVar2 = FUN_00a389a0(param_2,param_3);
  (**(code **)piVar1[2])(param_4);
  if (cVar2 == '\x01') {
    iVar4 = FUN_00a3be40(param_1,&param_4);
    if (iVar4 != 0) {
      FUN_00a53d80(iVar4);
    }
  }
  local_8 = local_8 & 0xffffff00;
  if (param_4 != (undefined4 *)0x0) {
    LVar6 = InterlockedDecrement(param_4 + 1);
    if ((LVar6 == 0) && (param_4 != (undefined4 *)0x0)) {
      (**(code **)*param_4)(1);
    }
  }
  ExceptionList = local_10;
  return param_1;
}

