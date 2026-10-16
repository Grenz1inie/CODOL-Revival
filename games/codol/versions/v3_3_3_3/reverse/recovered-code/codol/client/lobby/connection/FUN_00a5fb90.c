// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.connection
// Analyst label: 握手摘要和密钥材料组合
// VA: 0x00a5fb90; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a5fb90(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  char cVar1;
  int *unaff_FS_OFFSET;
  undefined4 auStack_1d0 [111];
  uint uStack_14;
  int iStack_10;
  undefined *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &DAT_00b4428b;
  iStack_10 = *unaff_FS_OFFSET;
  uStack_14 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  func_0x00b2ca30(param_1,0x14,uStack_14);
  uStack_8 = 0;
  cVar1 = func_0x00b2c990(param_2,param_3);
  auStack_1d0[0] = 0x14;
  if (cVar1 != '\0') {
    func_0x00b2c9d0(param_4,auStack_1d0);
  }
  uStack_8 = 0xffffffff;
  func_0x00b2c980();
  *unaff_FS_OFFSET = iStack_10;
  func_0x00af6b2f();
  return;
}

