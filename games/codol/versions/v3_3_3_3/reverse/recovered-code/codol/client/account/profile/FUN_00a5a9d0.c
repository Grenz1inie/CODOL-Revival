// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 私有档案查询任务 8/2
// VA: 0x00a5a9d0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_37adaed9d139608621986c84f87a7f3b3b4792d3bdcd6ccefebec572c8a67d02
// BEGIN PSEUDOCODE

undefined4 * FUN_00a5a9d0(undefined4 *param_1,undefined4 param_2)

{
  uint uVar1;
  int iVar2;
  LONG LVar3;
  undefined4 *local_14;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puStack_c = &LAB_00b427ac;
  local_10 = ExceptionList;
  uVar1 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  *param_1 = 0;
  local_8 = 0;
  iVar2 = FUN_00a38020(0x2c,uVar1);
  local_8 = 1;
  if (iVar2 == 0) {
    local_14 = (undefined4 *)0x0;
  }
  else {
    local_14 = (undefined4 *)FUN_00a62db0(0x48,1);
  }
  if (local_14 != (undefined4 *)0x0) {
    InterlockedIncrement(local_14 + 1);
  }
  local_8 = 2;
  FUN_00a3b1b0(&local_14,8,2);
  iVar2 = FUN_00a3be40(param_1,&local_14);
  if (iVar2 == 0) {
    FUN_00a44d00(param_2,1);
  }
  else {
    FUN_00a53d80(iVar2);
  }
  local_8 = local_8 & 0xffffff00;
  if (local_14 != (undefined4 *)0x0) {
    LVar3 = InterlockedDecrement(local_14 + 1);
    if ((LVar3 == 0) && (local_14 != (undefined4 *)0x0)) {
      (**(code **)*local_14)(1);
    }
  }
  ExceptionList = local_10;
  return param_1;
}

