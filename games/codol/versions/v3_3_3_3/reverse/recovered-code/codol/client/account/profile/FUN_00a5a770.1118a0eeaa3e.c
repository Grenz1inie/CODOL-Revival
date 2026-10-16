// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 指定账号私有档案查询任务 8/7
// VA: 0x00a5a770; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 *
FUN_00a5a770(undefined4 *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  char cVar1;
  uint uVar2;
  int iVar3;
  int *unaff_FS_OFFSET;
  undefined4 *puStack_14;
  int iStack_10;
  undefined *puStack_c;
  uint uStack_8;
  
  puStack_c = &DAT_00b427ac;
  iStack_10 = *unaff_FS_OFFSET;
  uVar2 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  *param_1 = 0;
  uStack_8 = 0;
  iVar3 = func_0x00a38020(0x2c,uVar2);
  uStack_8 = 1;
  if (iVar3 == 0) {
    puStack_14 = (undefined4 *)0x0;
  }
  else {
    puStack_14 = (undefined4 *)FUN_00a62db0(0x52,1);
  }
  if (puStack_14 != (undefined4 *)0x0) {
    InterlockedIncrement(puStack_14 + 1);
  }
  uStack_8 = 2;
  FUN_00a3b1b0(&puStack_14,8,7);
  cVar1 = func_0x00a389a0(param_2,param_3);
  if (cVar1 == '\x01') {
    iVar3 = FUN_00a3be40(param_1,&puStack_14);
    if (iVar3 == 0) {
      FUN_00a44d00(param_4,1);
    }
    else {
      func_0x00a53d80(iVar3);
    }
  }
  else {
    func_0x00a53d80();
  }
  uStack_8 = uStack_8 & 0xffffff00;
  if (puStack_14 != (undefined4 *)0x0) {
    iVar3 = InterlockedDecrement(puStack_14 + 1);
    if ((iVar3 == 0) && (puStack_14 != (undefined4 *)0x0)) {
      (**(code **)*puStack_14)(1);
    }
  }
  *unaff_FS_OFFSET = iStack_10;
  return param_1;
}

