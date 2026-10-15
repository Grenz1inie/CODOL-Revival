// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.currency
// Analyst label: 点券余额请求任务 93/1
// VA: 0x00a4bfc0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_7ad9c9ea3911405e75eb46fbce016bfbfb626c976948c5b9146a231598bd19b7
// BEGIN PSEUDOCODE

undefined4 * FUN_00a4bfc0(undefined4 *param_1,int param_2,undefined4 param_3)

{
  char cVar1;
  uint uVar2;
  int iVar3;
  int local_44 [3];
  char local_38;
  char local_30;
  int local_2c;
  int local_24;
  int local_20;
  undefined4 local_1c;
  undefined4 local_14;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puStack_c = &LAB_00b42631;
  local_10 = ExceptionList;
  uVar2 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  *param_1 = 0;
  local_8 = 0;
  local_14 = 1;
  FUN_00a63f20(0x5d,1,0x400,0x80000);
  local_8 = 1;
  cVar1 = (**(code **)(local_44[0] + 4))(4,1,uVar2);
  if (cVar1 != '\0') {
    if (local_30 != '\0') {
      local_2c = local_2c + -1;
    }
    if (local_38 != '\0') {
      cVar1 = FUN_00a38f30(param_3);
      local_38 = '\x01';
      if (cVar1 != '\0') goto LAB_00a4c04f;
    }
    local_38 = '\0';
  }
LAB_00a4c04f:
  if ((local_24 == 0) && (local_20 == 0)) {
    local_24 = param_2;
    local_1c = param_3;
  }
  else {
    FUN_00a53d80();
    local_38 = '\0';
  }
  iVar3 = FUN_00a3c6f0(param_1,local_44);
  if (iVar3 != 0) {
    FUN_00a53d80(iVar3);
  }
  local_8 = local_8 & 0xffffff00;
  FUN_00a63d80();
  ExceptionList = local_10;
  return param_1;
}

