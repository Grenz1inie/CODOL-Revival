// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 账号 ID 与账号类型读取
// VA: 0x00a45950; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_843b7d460f215fcaa37cea103b937dc06164cd073609b4c60ff575136facc2d0
// BEGIN PSEUDOCODE

undefined1 FUN_00a45950(undefined4 *param_1,int param_2)

{
  char cVar1;
  uint uVar2;
  LONG LVar3;
  undefined1 uVar4;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  puStack_c = &LAB_00b44f88;
  local_10 = ExceptionList;
  uVar2 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_8 = 0;
  cVar1 = FUN_00a391c0(param_2 + 0x18);
  if (cVar1 != '\0') {
    cVar1 = FUN_00a39250(param_2 + 8,10);
    if (cVar1 != '\0') {
      uVar4 = 1;
      goto LAB_00a459a6;
    }
  }
  uVar4 = 0;
LAB_00a459a6:
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

