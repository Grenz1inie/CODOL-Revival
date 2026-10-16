// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.currency
// Analyst label: 简单余额条目读取
// VA: 0x00a4c4a0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_d74eab6c044b240a14a78129cc507bf8de6c5d29089703199f9fc534eb28fccd
// BEGIN PSEUDOCODE

undefined1 FUN_00a4c4a0(undefined4 *param_1)

{
  char cVar1;
  uint uVar2;
  LONG LVar3;
  int in_ECX;
  undefined1 uVar4;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  puStack_c = &LAB_00b44f88;
  local_10 = ExceptionList;
  uVar2 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_8 = 0;
  cVar1 = FUN_00a390b0(in_ECX + 0x10);
  if (cVar1 != '\0') {
    cVar1 = FUN_00a38a60(in_ECX + 0x14);
    if (cVar1 != '\0') {
      uVar4 = 1;
      goto LAB_00a4c4f3;
    }
  }
  uVar4 = 0;
LAB_00a4c4f3:
  local_8 = 0xffffffff;
  if (param_1 != (undefined4 *)0x0) {
    LVar3 = InterlockedDecrement(param_1 + 1);
    if ((LVar3 == 0) && (param_1 != (undefined4 *)0x0)) {
      (**(code **)*param_1)(1,uVar2);
    }
  }
  ExceptionList = local_10;
  return uVar4;
}

