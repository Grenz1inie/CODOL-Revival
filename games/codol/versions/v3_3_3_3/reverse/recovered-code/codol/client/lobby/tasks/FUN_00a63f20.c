// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 服务号和任务号参数对象构造
// VA: 0x00a63f20; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a63f20(undefined1 param_1,undefined1 param_2,uint param_3,uint param_4)

{
  int *piVar1;
  int *piVar2;
  uint uVar3;
  int iVar4;
  int iVar5;
  undefined4 *in_ECX;
  int *unaff_FS_OFFSET;
  int iStack_10;
  undefined *puStack_c;
  undefined1 uStack_8;
  undefined3 uStack_7;
  
  puStack_c = &DAT_00b44879;
  iStack_10 = *unaff_FS_OFFSET;
  uVar3 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  in_ECX[1] = param_3;
  in_ECX[2] = param_4;
  *(undefined1 *)(in_ECX + 3) = 1;
  in_ECX[4] = 0;
  *(undefined1 *)(in_ECX + 5) = 0;
  in_ECX[6] = 0;
  *(undefined1 *)(in_ECX + 7) = param_1;
  piVar1 = in_ECX + 0xb;
  *in_ECX = &UNK_00c080a8;
  *(undefined1 *)((int)in_ECX + 0x1d) = param_2;
  in_ECX[8] = 0;
  in_ECX[9] = 0;
  in_ECX[10] = 0;
  *piVar1 = 0;
  uStack_8 = 3;
  uStack_7 = 0;
  if (param_4 < 0x4c) {
    func_0x00a53d80(0x4c,uVar3);
    in_ECX[2] = 0x4c;
  }
  _param_1 = 0x4c;
  if (0x4b < param_3) {
    _param_1 = param_3;
  }
  if (param_4 < _param_1) {
    _param_1 = param_4;
  }
  iVar4 = func_0x00a38020(0x2c);
  uStack_8 = 4;
  if (iVar4 == 0) {
    iVar4 = 0;
  }
  else {
    iVar4 = func_0x00a62db0(_param_1,1);
  }
  _uStack_8 = CONCAT31(uStack_7,3);
  if (*piVar1 != 0) {
    iVar5 = InterlockedDecrement(*piVar1 + 4);
    if ((iVar5 == 0) && ((undefined4 *)*piVar1 != (undefined4 *)0x0)) {
      (*(code *)**(undefined4 **)*piVar1)(1);
    }
  }
  *piVar1 = iVar4;
  if (iVar4 != 0) {
    InterlockedIncrement(iVar4 + 4);
  }
  piVar2 = in_ECX + 4;
  if (piVar2 != piVar1) {
    if (*piVar2 != 0) {
      iVar4 = InterlockedDecrement(*piVar2 + 4);
      if ((iVar4 == 0) && ((undefined4 *)*piVar2 != (undefined4 *)0x0)) {
        (*(code *)**(undefined4 **)*piVar2)(1);
      }
    }
    iVar4 = *piVar1;
    *piVar2 = iVar4;
    if (iVar4 != 0) {
      InterlockedIncrement(iVar4 + 4);
    }
  }
  if (*piVar2 == 0) {
    func_0x00a53d80();
    *(undefined1 *)(in_ECX + 3) = 0;
  }
  else {
    func_0x00a3b1b0(piVar1,*(undefined1 *)(in_ECX + 7),*(undefined1 *)((int)in_ECX + 0x1d));
  }
  *unaff_FS_OFFSET = iStack_10;
  return;
}

