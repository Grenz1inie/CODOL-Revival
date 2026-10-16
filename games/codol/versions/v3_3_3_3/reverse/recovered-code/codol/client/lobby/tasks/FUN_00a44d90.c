// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 远程任务状态对象初始化
// VA: 0x00a44d90; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby-tail.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a44d90(void)

{
  uint uVar1;
  undefined4 *in_ECX;
  int *unaff_FS_OFFSET;
  int iStack_10;
  undefined *puStack_c;
  undefined4 uStack_8;
  
  puStack_c = &DAT_00b41a03;
  iStack_10 = *unaff_FS_OFFSET;
  uVar1 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  *in_ECX = &UNK_00c6606c;
  in_ECX[1] = 0;
  uStack_8 = 0;
  *in_ECX = &UNK_00c07548;
  func_0x00a385d0(uVar1);
  in_ECX[4] = 0x42700000;
  in_ECX[5] = 0;
  in_ECX[6] = 0;
  uStack_8 = CONCAT31(uStack_8._1_3_,1);
  in_ECX[7] = 0;
  in_ECX[8] = 0;
  in_ECX[9] = 0;
  in_ECX[10] = 0;
  in_ECX[0xb] = 0;
  in_ECX[0xc] = 0;
  in_ECX[0xd] = 0;
  in_ECX[0xe] = 0;
  in_ECX[0xf] = 0;
  func_0x00a38590();
  in_ECX[0x11] = _DAT_00cfafcc;
  _DAT_00cfafcc = _DAT_00cfafcc + 1;
  *unaff_FS_OFFSET = iStack_10;
  return;
}

