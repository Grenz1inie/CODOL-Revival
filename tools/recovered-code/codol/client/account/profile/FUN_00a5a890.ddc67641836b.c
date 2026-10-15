// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 公开档案查询任务 8/1
// VA: 0x00a5a890; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 * FUN_00a5a890(undefined4 *param_1,int param_2,undefined4 param_3,undefined4 *param_4)

{
  bool bVar1;
  uint uVar2;
  char cVar3;
  uint uVar4;
  int iVar5;
  int iVar6;
  int *unaff_FS_OFFSET;
  int iStack_10;
  undefined *puStack_c;
  uint uStack_8;
  
  uVar2 = (uint)param_4;
  puStack_c = &DAT_00b43b0c;
  iStack_10 = *unaff_FS_OFFSET;
  uVar4 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  *param_1 = 0;
  uStack_8 = 0;
  iVar6 = (int)param_4 * 9;
  iVar5 = func_0x00a38020(0x2c,uVar4);
  uStack_8 = 1;
  if (iVar5 == 0) {
    param_4 = (undefined4 *)0x0;
  }
  else {
    param_4 = (undefined4 *)FUN_00a62db0(iVar6 + 0x48,1);
  }
  if (param_4 != (undefined4 *)0x0) {
    InterlockedIncrement(param_4 + 1);
  }
  uStack_8 = 2;
  FUN_00a3b1b0(&param_4,8,1);
  uVar4 = 0;
  bVar1 = true;
  if (uVar2 != 0) {
    do {
      if ((bVar1) &&
         (cVar3 = func_0x00a389a0(*(undefined4 *)(param_2 + uVar4 * 8),
                                  *(undefined4 *)(param_2 + 4 + uVar4 * 8)), cVar3 != '\0')) {
        bVar1 = true;
      }
      else {
        bVar1 = false;
      }
      uVar4 = uVar4 + 1;
    } while (uVar4 < uVar2);
    if (!bVar1) {
      func_0x00a53d80();
      goto LAB_00a5a98f;
    }
  }
  iVar6 = FUN_00a3be40(param_1,&param_4);
  if (iVar6 == 0) {
    FUN_00a44d00(param_3,uVar2);
  }
  else {
    func_0x00a53d80(iVar6);
  }
LAB_00a5a98f:
  uStack_8 = uStack_8 & 0xffffff00;
  if (((param_4 != (undefined4 *)0x0) && (iVar6 = InterlockedDecrement(param_4 + 1), iVar6 == 0)) &&
     (param_4 != (undefined4 *)0x0)) {
    (**(code **)*param_4)(1);
  }
  *unaff_FS_OFFSET = iStack_10;
  return param_1;
}

