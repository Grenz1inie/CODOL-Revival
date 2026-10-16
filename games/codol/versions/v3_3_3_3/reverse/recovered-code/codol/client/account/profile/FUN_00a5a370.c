// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案基类字段读取
// VA: 0x00a5a370; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_baa82e2fe72c64409aaee8ece035896f1ab4fc53ad9912d87c1020f0bfee5c89
// BEGIN PSEUDOCODE

char FUN_00a5a370(undefined4 *param_1)

{
  char cVar1;
  uint uVar2;
  LONG LVar3;
  int in_ECX;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  puStack_c = &LAB_00b43e48;
  local_10 = ExceptionList;
  uVar2 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_8 = 0;
  cVar1 = FUN_00a391c0(in_ECX + 0x10);
  if (cVar1 == '\0') {
    FUN_00a53d80(uVar2);
  }
  local_8 = 0xffffffff;
  if (param_1 != (undefined4 *)0x0) {
    LVar3 = InterlockedDecrement(param_1 + 1);
    if ((LVar3 == 0) && (param_1 != (undefined4 *)0x0)) {
      (**(code **)*param_1)(1);
    }
  }
  ExceptionList = local_10;
  return cVar1;
}

