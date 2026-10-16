// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.items
// Analyst label: 库存条目反序列化
// VA: 0x00a4b850; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_8212de7a70f27467a15bdceb9451f821d3ebc4172c1465e7be9ef3d4d4af8f78
// BEGIN PSEUDOCODE

void FUN_00a4b850(undefined4 *param_1)

{
  bool bVar1;
  char cVar2;
  uint uVar3;
  LONG LVar4;
  int in_ECX;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puStack_c = &LAB_00b42498;
  local_10 = ExceptionList;
  uVar3 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_8 = 1;
  FUN_00a455f0();
  local_8._0_1_ = 2;
  cVar2 = FUN_00a45630();
  local_8 = CONCAT31(local_8._1_3_,1);
  FUN_00a45620();
  if (cVar2 == '\0') {
    FUN_00a45750();
LAB_00a4b91c:
    cVar2 = FUN_00a38a60();
    if (((cVar2 != '\0') && (cVar2 = FUN_00a38a60(), cVar2 != '\0')) &&
       (cVar2 = FUN_00a38a60(), cVar2 != '\0')) {
      bVar1 = true;
      goto LAB_00a4b8ed;
    }
  }
  else {
    if (param_1 != (undefined4 *)0x0) {
      InterlockedIncrement(param_1 + 1);
    }
    cVar2 = FUN_00a45950();
    if (cVar2 != '\0') goto LAB_00a4b91c;
  }
  bVar1 = false;
LAB_00a4b8ed:
  if ((bVar1) && (cVar2 = FUN_00a392b0(), cVar2 != '\0')) {
    bVar1 = true;
  }
  else {
    bVar1 = false;
  }
  *(undefined1 *)(in_ECX + 0x7c) = 0x40;
  if (((bVar1) && (cVar2 = FUN_00a38a60(), cVar2 != '\0')) &&
     ((cVar2 = FUN_00a39170(), cVar2 != '\0' &&
      ((cVar2 = FUN_00a390f0(), cVar2 != '\0' && (cVar2 = FUN_00a38a60(), cVar2 != '\0')))))) {
    FUN_00a390b0();
  }
  local_8 = local_8 & 0xffffff00;
  if (((param_1 != (undefined4 *)0x0) && (LVar4 = InterlockedDecrement(param_1 + 1), LVar4 == 0)) &&
     (param_1 != (undefined4 *)0x0)) {
    (**(code **)*param_1)();
  }
  local_8 = 0xffffffff;
  FUN_00a45620();
  ExceptionList = local_10;
  __security_check_cookie(uVar3 ^ (uint)&stack0xfffffffc);
  return;
}

