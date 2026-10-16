// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 继承所有者的余额条目读取
// VA: 0x00a64ad0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_69dfaff037b33415d2d413f6a23d78d4875dd2c3f7c952589ff443d871f132b7
// BEGIN PSEUDOCODE

void FUN_00a64ad0(undefined4 *param_1)

{
  char cVar1;
  uint uVar2;
  LONG LVar3;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puStack_c = &LAB_00b449f8;
  local_10 = ExceptionList;
  uVar2 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_8 = 1;
  FUN_00a455f0();
  local_8._0_1_ = 2;
  cVar1 = FUN_00a45630();
  local_8 = CONCAT31(local_8._1_3_,1);
  FUN_00a45620();
  if (cVar1 == '\0') {
    FUN_00a45750();
  }
  else {
    if (param_1 != (undefined4 *)0x0) {
      InterlockedIncrement(param_1 + 1);
    }
    cVar1 = FUN_00a45950();
    if (cVar1 == '\0') goto LAB_00a64b71;
  }
  cVar1 = FUN_00a390b0();
  if (cVar1 != '\0') {
    FUN_00a38a60();
  }
LAB_00a64b71:
  local_8 = local_8 & 0xffffff00;
  if (((param_1 != (undefined4 *)0x0) && (LVar3 = InterlockedDecrement(param_1 + 1), LVar3 == 0)) &&
     (param_1 != (undefined4 *)0x0)) {
    (**(code **)*param_1)();
  }
  local_8 = 0xffffffff;
  FUN_00a45620();
  ExceptionList = local_10;
  __security_check_cookie(uVar2 ^ (uint)&stack0xfffffffc);
  return;
}

