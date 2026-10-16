// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.purchase
// Analyst label: 点券购买任务 93/4 或 93/131 参数分支
// VA: 0x00a4c0b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_6a768539251d88d7b65577d70684c859a0e9a4c1c03c09a163398ce9fc48051c
// BEGIN PSEUDOCODE

void FUN_00a4c0b0(undefined4 *param_1)

{
  char cVar1;
  int in_ECX;
  undefined4 in_stack_00000028;
  undefined4 in_stack_0000002c;
  undefined4 in_stack_00000030;
  undefined4 in_stack_00000034;
  undefined4 in_stack_00000038;
  undefined4 in_stack_0000003c;
  undefined4 in_stack_00000040;
  undefined4 in_stack_00000044;
  undefined4 in_stack_00000048;
  undefined4 *in_stack_0000004c;
  undefined4 in_stack_00000050;
  undefined1 auStack_e4 [32];
  undefined4 uStack_c4;
  undefined4 uStack_c0;
  undefined4 uStack_bc;
  undefined4 uStack_b8;
  undefined4 uStack_b4;
  undefined4 uStack_b0;
  undefined4 uStack_ac;
  undefined4 uStack_a8;
  uint uStack_a4;
  undefined4 *puStack_a0;
  undefined1 *puStack_9c;
  uint uStack_98;
  undefined1 local_88 [48];
  undefined4 *local_58;
  undefined4 local_54;
  undefined4 local_50;
  undefined4 local_4c;
  undefined4 local_48;
  undefined4 local_44;
  undefined4 local_40;
  undefined4 local_3c;
  undefined1 *local_38;
  uint local_14;
  void *local_10;
  undefined1 *puStack_c;
  int local_8;
  
  puStack_c = &LAB_00b42684;
  local_10 = ExceptionList;
  uStack_98 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_38 = (undefined1 *)in_stack_00000028;
  local_40 = in_stack_0000002c;
  local_3c = in_stack_00000038;
  local_48 = in_stack_0000003c;
  local_58 = param_1;
  local_54 = in_stack_00000044;
  local_50 = in_stack_00000048;
  local_44 = in_stack_00000050;
  local_4c = 0;
  local_8 = 1;
  puStack_9c = (undefined1 *)0xa4c123;
  local_14 = uStack_98;
  puStack_9c = (undefined1 *)FUN_00a456e0();
  local_8._0_1_ = 2;
  puStack_a0 = (undefined4 *)0xa4c130;
  cVar1 = FUN_00a45630();
  local_8._0_1_ = 1;
  puStack_9c = (undefined1 *)0xa4c13e;
  FUN_00a45620();
  *param_1 = 0;
  puStack_9c = (undefined1 *)0x80000;
  uStack_a4 = (uint)(byte)((-(cVar1 != '\0') & 0x7fU) + 4);
  puStack_a0 = (undefined4 *)0x400;
  uStack_a8 = 0x5d;
  local_4c = 1;
  uStack_ac = 0xa4c170;
  FUN_00a63f20();
  puStack_9c = (undefined1 *)local_44;
  puStack_a0 = in_stack_0000004c;
  uStack_a4 = local_50;
  uStack_a8 = local_54;
  uStack_ac = in_stack_00000040;
  uStack_b0 = local_48;
  uStack_b4 = local_3c;
  uStack_b8 = in_stack_00000034;
  uStack_bc = in_stack_00000030;
  uStack_c0 = local_40;
  uStack_c4 = local_38;
  local_38 = auStack_e4;
  local_8 = CONCAT31(local_8._1_3_,3);
  FUN_00a456f0(&stack0x00000008);
  cVar1 = FUN_00a64ca0(local_88,in_ECX + 4);
  if (cVar1 != '\0') {
    puStack_9c = local_88;
    puStack_a0 = param_1;
    uStack_a4 = 0xa4c1d7;
    puStack_9c = (undefined1 *)FUN_00a3c6f0();
    if (puStack_9c != (undefined1 *)0x0) {
      puStack_a0 = (undefined4 *)0xa4c1e1;
      FUN_00a53d80();
    }
  }
  local_8._0_1_ = 1;
  puStack_9c = (undefined1 *)0xa4c1f3;
  FUN_00a63d80();
  local_8 = (uint)local_8._1_3_ << 8;
  puStack_9c = (undefined1 *)0xa4c1ff;
  FUN_00a45620();
  ExceptionList = local_10;
  __security_check_cookie(local_14 ^ (uint)&stack0xfffffffc);
  return;
}

