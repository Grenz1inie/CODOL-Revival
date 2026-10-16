// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.purchase
// Analyst label: 游戏币购买任务 80/154 参数构造
// VA: 0x00a467e0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 * FUN_00a467e0(undefined4 *param_1)

{
  char cVar1;
  int in_ECX;
  int *unaff_FS_OFFSET;
  undefined1 auStack_44 [48];
  undefined4 uStack_14;
  int iStack_10;
  undefined *puStack_c;
  uint uStack_8;
  
  puStack_c = &DAT_00b41c11;
  iStack_10 = *unaff_FS_OFFSET;
  *unaff_FS_OFFSET = (int)&iStack_10;
  *param_1 = 0;
  uStack_8 = 0;
  uStack_14 = 1;
  FUN_00a63f20();
  uStack_8 = 1;
  func_0x00a456e0();
  cVar1 = func_0x00a45b40(auStack_44,in_ECX + 4);
  if (cVar1 != '\0') {
    FUN_00a46060();
  }
  uStack_8 = uStack_8 & 0xffffff00;
  FUN_00a63d80();
  *unaff_FS_OFFSET = iStack_10;
  return param_1;
}

