// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 远程任务缓冲对象初始化
// VA: 0x00a62db0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a62db0(undefined4 param_1,undefined1 param_2)

{
  uint uVar1;
  undefined4 *in_ECX;
  int *unaff_FS_OFFSET;
  int iStack_10;
  undefined *puStack_c;
  undefined4 uStack_8;
  
  puStack_c = &DAT_00b44670;
  iStack_10 = *unaff_FS_OFFSET;
  uVar1 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  *in_ECX = &UNK_00c6606c;
  in_ECX[1] = 0;
  in_ECX[2] = 0;
  in_ECX[3] = 0;
  *(undefined1 *)(in_ECX + 6) = param_2;
  *(undefined1 *)((int)in_ECX + 0x19) = param_2;
  *(undefined1 *)((int)in_ECX + 0x1a) = 0;
  in_ECX[5] = 0;
  in_ECX[4] = 0;
  in_ECX[7] = 0;
  in_ECX[8] = 0;
  in_ECX[9] = 0;
  in_ECX[10] = 0;
  uStack_8 = 1;
  *in_ECX = &UNK_00c08044;
  func_0x00a62c40(param_1,uVar1);
  *unaff_FS_OFFSET = iStack_10;
  return;
}

