// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.purchase
// Analyst label: 点券购买任务 93/4 或 93/131 参数分支
// VA: 0x00a4c0b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a4c0b0(undefined4 *param_1)

{
  char cVar1;
  int in_ECX;
  int *unaff_FS_OFFSET;
  undefined4 in_stack_00000028;
  undefined4 in_stack_0000002c;
  undefined4 in_stack_00000030;
  undefined4 in_stack_00000034;
  undefined4 in_stack_00000038;
  undefined4 in_stack_0000003c;
  undefined4 in_stack_00000040;
  undefined4 in_stack_00000044;
  undefined4 *in_stack_00000048;
  undefined4 in_stack_0000004c;
  undefined4 in_stack_00000050;
  undefined1 auStack_f8 [32];
  undefined4 uStack_d8;
  undefined4 uStack_d4;
  undefined4 uStack_d0;
  undefined4 uStack_cc;
  undefined4 uStack_c8;
  undefined4 uStack_c4;
  undefined4 uStack_c0;
  undefined4 uStack_bc;
  undefined4 *puStack_b8;
  undefined1 *puStack_b4;
  undefined4 uStack_b0;
  undefined4 uStack_ac;
  uint uStack_a8;
  undefined4 uStack_a4;
  undefined4 uStack_a0;
  undefined4 uStack_9c;
  uint uStack_98;
  undefined1 auStack_88 [48];
  undefined4 *puStack_58;
  undefined4 uStack_54;
  undefined4 *puStack_50;
  undefined4 uStack_4c;
  undefined4 uStack_48;
  undefined4 uStack_44;
  undefined4 uStack_40;
  undefined4 uStack_3c;
  undefined1 *puStack_38;
  uint uStack_14;
  int iStack_10;
  undefined *puStack_c;
  int iStack_8;
  
  puStack_c = &DAT_00b42684;
  iStack_10 = *unaff_FS_OFFSET;
  uStack_98 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  puStack_38 = (undefined1 *)in_stack_00000028;
  uStack_40 = in_stack_0000002c;
  uStack_3c = in_stack_00000038;
  uStack_48 = in_stack_0000003c;
  puStack_58 = param_1;
  uStack_54 = in_stack_00000044;
  puStack_50 = in_stack_00000048;
  uStack_44 = in_stack_00000050;
  uStack_4c = 0;
  iStack_8 = 1;
  uStack_9c = 0xa4c123;
  uStack_14 = uStack_98;
  uStack_9c = func_0x00a456e0();
  iStack_8._0_1_ = 2;
  uStack_a0 = 0xa4c130;
  cVar1 = func_0x00a45630();
  iStack_8._0_1_ = 1;
  uStack_a0 = 0xa4c13e;
  func_0x00a45620();
  *param_1 = 0;
  uStack_a0 = 0x80000;
  uStack_a8 = (uint)(byte)((-(cVar1 != '\0') & 0x7fU) + 4);
  uStack_a4 = 0x400;
  uStack_ac = 0x5d;
  uStack_4c = 1;
  uStack_b0 = 0xa4c170;
  FUN_00a63f20();
  uStack_b0 = uStack_44;
  puStack_b4 = (undefined1 *)in_stack_0000004c;
  puStack_b8 = puStack_50;
  uStack_bc = uStack_54;
  uStack_c0 = in_stack_00000040;
  uStack_c4 = uStack_48;
  uStack_c8 = uStack_3c;
  uStack_cc = in_stack_00000034;
  uStack_d0 = in_stack_00000030;
  uStack_d4 = uStack_40;
  uStack_d8 = puStack_38;
  puStack_38 = auStack_f8;
  iStack_8 = CONCAT31(iStack_8._1_3_,3);
  func_0x00a456f0(&stack0x00000008);
  cVar1 = func_0x00a64ca0(auStack_88,in_ECX + 4);
  if (cVar1 != '\0') {
    puStack_b4 = auStack_88;
    puStack_b8 = param_1;
    uStack_bc = 0xa4c1d7;
    puStack_b4 = (undefined1 *)func_0x00a3c6f0();
    if (puStack_b4 != (undefined1 *)0x0) {
      puStack_b8 = (undefined4 *)0xa4c1e1;
      func_0x00a53d80();
    }
  }
  iStack_8._0_1_ = 1;
  puStack_b4 = (undefined1 *)0xa4c1f3;
  FUN_00a63d80();
  iStack_8 = (uint)iStack_8._1_3_ << 8;
  puStack_b4 = (undefined1 *)0xa4c1ff;
  func_0x00a45620();
  *unaff_FS_OFFSET = iStack_10;
  uStack_a4 = 0xa4c219;
  func_0x00af6b2f();
  return;
}

