// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 公开档案保存任务 8/3
// VA: 0x00a5a420; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/profile-write.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 * FUN_00a5a420(undefined4 *param_1,int *param_2)

{
  int *piVar1;
  uint uVar2;
  int iVar3;
  int iVar4;
  int *unaff_FS_OFFSET;
  int iStack_10;
  undefined *puStack_c;
  uint uStack_8;
  
  piVar1 = param_2;
  puStack_c = &DAT_00b43abc;
  iStack_10 = *unaff_FS_OFFSET;
  uVar2 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  *param_1 = 0;
  uStack_8 = 0;
  iVar3 = (**(code **)(*param_2 + 4))(uVar2);
  iVar4 = func_0x00a38020(0x2c);
  uStack_8 = 1;
  if (iVar4 == 0) {
    param_2 = (undefined4 *)0x0;
  }
  else {
    param_2 = (int *)func_0x00a62db0(iVar3 + 0x49,1);
  }
  if (param_2 != (undefined4 *)0x0) {
    InterlockedIncrement(param_2 + 1);
  }
  uStack_8 = 2;
  func_0x00a3b1b0(&param_2,8,3);
  (**(code **)piVar1[2])(param_2);
  iVar3 = func_0x00a3be40(param_1,&param_2);
  if (iVar3 != 0) {
    func_0x00a53d80(iVar3);
  }
  uStack_8 = uStack_8 & 0xffffff00;
  if (param_2 != (undefined4 *)0x0) {
    iVar3 = InterlockedDecrement(param_2 + 1);
    if ((iVar3 == 0) && (param_2 != (undefined4 *)0x0)) {
      (**(code **)*param_2)(1);
    }
  }
  *unaff_FS_OFFSET = iStack_10;
  return param_1;
}

