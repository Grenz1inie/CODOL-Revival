// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 资产获取任务 80/230
// VA: 0x00a472b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_b2e7a53bc8c2ed2f4621c8db197bebaaf5f952565b2a1dc169b2a5f2da25a881
// BEGIN PSEUDOCODE

undefined4 * FUN_00a472b0(undefined4 *param_1,int param_2)

{
  uint uVar1;
  int in_ECX;
  undefined1 local_44 [12];
  undefined1 local_38;
  int local_24;
  int local_20;
  undefined4 local_1c;
  undefined4 local_14;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puStack_c = &LAB_00b42631;
  local_10 = ExceptionList;
  uVar1 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  *param_1 = 0;
  local_8 = 0;
  local_14 = 1;
  if (param_2 != 0) {
    FUN_00a63f20(0x50,0xe6,0x400,0x80000);
    local_8 = 1;
    FUN_00a63eb0(in_ECX + 4);
    if ((local_24 == 0) && (local_20 == 0)) {
      local_24 = param_2;
      local_1c = 1;
    }
    else {
      FUN_00a53d80(uVar1);
      local_38 = 0;
    }
    FUN_00a46060(param_1,local_44);
    local_8 = local_8 & 0xffffff00;
    FUN_00a63d80();
  }
  ExceptionList = local_10;
  return param_1;
}

