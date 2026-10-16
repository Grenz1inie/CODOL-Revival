// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.currency
// Analyst label: 游戏币余额请求任务 80/130
// VA: 0x00a461d0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_7ad9c9ea3911405e75eb46fbce016bfbfb626c976948c5b9146a231598bd19b7
// BEGIN PSEUDOCODE

undefined4 * FUN_00a461d0(undefined4 *param_1,int param_2,int param_3)

{
  uint uVar1;
  undefined1 local_48 [12];
  undefined1 local_3c;
  int local_28;
  int local_24;
  int local_20;
  undefined4 local_14;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puStack_c = &LAB_00b41c51;
  local_10 = ExceptionList;
  uVar1 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  *param_1 = 0;
  local_8 = 0;
  local_14 = 1;
  if ((param_2 != 0) && (param_3 != 0)) {
    FUN_00a63f20(0x50,0x82,0x400,0x80000);
    local_8 = 1;
    FUN_00a45a90(&param_3);
    if ((local_28 == 0) && (local_24 == 0)) {
      local_28 = param_2;
      local_20 = param_3;
    }
    else {
      FUN_00a53d80(uVar1);
      local_3c = 0;
    }
    FUN_00a46060(param_1,local_48);
    local_8 = local_8 & 0xffffff00;
    FUN_00a63d80();
  }
  ExceptionList = local_10;
  return param_1;
}

