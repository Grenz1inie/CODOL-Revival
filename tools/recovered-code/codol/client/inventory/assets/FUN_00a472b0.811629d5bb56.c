// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 资产获取任务 80/230
// VA: 0x00a472b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 * FUN_00a472b0(undefined4 *param_1,int param_2)

{
  uint uVar1;
  int in_ECX;
  int *unaff_FS_OFFSET;
  undefined1 auStack_44 [12];
  undefined1 uStack_38;
  int iStack_24;
  int iStack_20;
  undefined4 uStack_1c;
  undefined4 uStack_14;
  int iStack_10;
  undefined *puStack_c;
  uint uStack_8;
  
  puStack_c = &DAT_00b42631;
  iStack_10 = *unaff_FS_OFFSET;
  uVar1 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  *param_1 = 0;
  uStack_8 = 0;
  uStack_14 = 1;
  if (param_2 != 0) {
    FUN_00a63f20(0x50,0xe6,0x400,0x80000,uVar1);
    uStack_8 = 1;
    FUN_00a63eb0(in_ECX + 4);
    if ((iStack_24 == 0) && (iStack_20 == 0)) {
      iStack_24 = param_2;
      uStack_1c = 1;
    }
    else {
      func_0x00a53d80();
      uStack_38 = 0;
    }
    FUN_00a46060(param_1,auStack_44);
    uStack_8 = uStack_8 & 0xffffff00;
    FUN_00a63d80();
  }
  *unaff_FS_OFFSET = iStack_10;
  return param_1;
}

