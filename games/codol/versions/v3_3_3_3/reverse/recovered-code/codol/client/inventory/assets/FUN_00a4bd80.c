// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 权益条目读取（需结合汇编）
// VA: 0x00a4bd80; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_69dfaff037b33415d2d413f6a23d78d4875dd2c3f7c952589ff443d871f132b7
// BEGIN PSEUDOCODE

/* WARNING: Removing unreachable block (ram,0x00a4be5a) */
/* WARNING: Removing unreachable block (ram,0x00a4be60) */
/* WARNING: Removing unreachable block (ram,0x00a4be64) */
/* WARNING: Removing unreachable block (ram,0x00a4be71) */
/* WARNING: Removing unreachable block (ram,0x00a4be73) */
/* WARNING: Removing unreachable block (ram,0x00a4be84) */
/* WARNING: Removing unreachable block (ram,0x00a4be91) */
/* WARNING: Removing unreachable block (ram,0x00a4be93) */
/* WARNING: Removing unreachable block (ram,0x00a4beab) */
/* WARNING: Removing unreachable block (ram,0x00a4bea7) */
/* WARNING: Removing unreachable block (ram,0x00a4bead) */

void FUN_00a4bd80(undefined4 *param_1)

{
  char cVar1;
  uint uVar2;
  LONG LVar3;
  int in_ECX;
  bool bVar4;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puStack_c = &LAB_00b425a8;
  local_10 = ExceptionList;
  uVar2 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_8 = 1;
  bVar4 = true;
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
    bVar4 = cVar1 != '\0';
  }
  if (bVar4) {
    FUN_00a38a60();
  }
  *(undefined2 *)(in_ECX + 0x30) = 0;
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

