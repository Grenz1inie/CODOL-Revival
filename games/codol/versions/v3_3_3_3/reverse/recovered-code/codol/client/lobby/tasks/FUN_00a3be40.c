// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 远程任务创建并交给提交器
// VA: 0x00a3be40; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a3be40(int *param_1)

{
  int iVar1;
  int iVar2;
  int *unaff_FS_OFFSET;
  int iStack_10;
  undefined *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &DAT_00b45fbb;
  iStack_10 = *unaff_FS_OFFSET;
  *unaff_FS_OFFSET = (int)&iStack_10;
  iVar1 = func_0x00a38020();
  uStack_8 = 0;
  if (iVar1 == 0) {
    iVar1 = 0;
  }
  else {
    iVar1 = func_0x00a44d90();
  }
  uStack_8 = 0xffffffff;
  if (*param_1 != 0) {
    iVar2 = InterlockedDecrement();
    if ((iVar2 == 0) && ((undefined4 *)*param_1 != (undefined4 *)0x0)) {
      (*(code *)**(undefined4 **)*param_1)();
    }
  }
  *param_1 = iVar1;
  if (iVar1 != 0) {
    InterlockedIncrement();
  }
  if (*param_1 != 0) {
    InterlockedIncrement(*param_1 + 4);
  }
  func_0x00a3b8a0();
  *unaff_FS_OFFSET = iStack_10;
  return;
}

