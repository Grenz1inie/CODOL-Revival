// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 私有档案查询任务 8/2
// VA: 0x00a5a9d0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 * FUN_00a5a9d0(undefined4 *param_1,undefined4 param_2)

{
  uint uVar1;
  int iVar2;
  int *unaff_FS_OFFSET;
  undefined4 *puStack_14;
  int iStack_10;
  undefined *puStack_c;
  uint uStack_8;
  
  puStack_c = &DAT_00b427ac;
  iStack_10 = *unaff_FS_OFFSET;
  uVar1 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  *param_1 = 0;
  uStack_8 = 0;
  iVar2 = func_0x00a38020(0x2c,uVar1);
  uStack_8 = 1;
  if (iVar2 == 0) {
    puStack_14 = (undefined4 *)0x0;
  }
  else {
    puStack_14 = (undefined4 *)FUN_00a62db0(0x48,1);
  }
  if (puStack_14 != (undefined4 *)0x0) {
    InterlockedIncrement(puStack_14 + 1);
  }
  uStack_8 = 2;
  FUN_00a3b1b0(&puStack_14,8,2);
  iVar2 = FUN_00a3be40(param_1,&puStack_14);
  if (iVar2 == 0) {
    FUN_00a44d00(param_2,1);
  }
  else {
    func_0x00a53d80(iVar2);
  }
  uStack_8 = uStack_8 & 0xffffff00;
  if (puStack_14 != (undefined4 *)0x0) {
    iVar2 = InterlockedDecrement(puStack_14 + 1);
    if ((iVar2 == 0) && (puStack_14 != (undefined4 *)0x0)) {
      (**(code **)*puStack_14)(1);
    }
  }
  *unaff_FS_OFFSET = iStack_10;
  return param_1;
}

