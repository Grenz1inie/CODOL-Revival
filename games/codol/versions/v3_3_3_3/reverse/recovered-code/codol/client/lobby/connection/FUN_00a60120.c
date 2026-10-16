// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.connection
// Analyst label: 握手带标签的分块密钥扩展
// VA: 0x00a60120; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a60120(undefined4 param_1,uint param_2,undefined4 param_3,int param_4,undefined4 param_5,
                 uint param_6)

{
  bool bVar1;
  char cVar2;
  uint uVar3;
  int *unaff_FS_OFFSET;
  int iStack_540;
  int iStack_53c;
  uint uStack_538;
  undefined1 uStack_532;
  char cStack_531;
  undefined4 uStack_530;
  char cStack_529;
  undefined1 auStack_1b8 [400];
  undefined1 auStack_28 [20];
  uint uStack_14;
  int iStack_10;
  undefined *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &DAT_00b44346;
  iStack_10 = *unaff_FS_OFFSET;
  uStack_14 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  uStack_538 = 0;
  if (((param_2 < 9) || (1999 < param_6)) || (399 < param_4 + 0x15U)) {
    bVar1 = false;
  }
  else {
    bVar1 = true;
  }
  cStack_529 = '\x01';
  uStack_530 = 0;
  if ((bVar1) &&
     (cVar2 = func_0x00a3a960(auStack_1b8,400,0,&uStack_530,param_3,param_4,uStack_14),
     cVar2 != '\0')) {
    uStack_532 = 1;
    cVar2 = func_0x00a3a960(auStack_1b8,400,uStack_530,&uStack_530,&uStack_532,1);
    if (cVar2 == '\0') goto LAB_00a6020d;
    bVar1 = true;
  }
  else {
LAB_00a6020d:
    bVar1 = false;
  }
  func_0x00b2ca30(param_1,param_2);
  uStack_8 = 0;
  if ((bVar1) && (cVar2 = func_0x00b2c990(auStack_1b8,uStack_530), cVar2 != '\0')) {
    bVar1 = true;
  }
  else {
    bVar1 = false;
  }
  iStack_540 = 0x14;
  if (((bVar1) && (cVar2 = func_0x00b2c9d0(auStack_28,&iStack_540), cVar2 != '\0')) &&
     (iStack_540 == 0x14)) {
    uVar3 = param_6 - uStack_538;
    if (0x14 < uVar3) {
      uVar3 = 0x14;
    }
    cVar2 = func_0x00a3a960(param_5,param_6,uStack_538,&uStack_538,auStack_28,uVar3);
    if (cVar2 != '\0') {
      bVar1 = true;
      goto LAB_00a602b8;
    }
  }
  bVar1 = false;
LAB_00a602b8:
  uStack_8 = 0xffffffff;
  func_0x00b2c980();
  if (bVar1) {
    do {
      if (param_6 <= uStack_538) break;
      cStack_529 = cStack_529 + '\x01';
      uStack_530 = 0;
      cVar2 = func_0x00a3a960(auStack_1b8,400,0,&uStack_530,auStack_28,0x14);
      if ((cVar2 == '\0') ||
         (cVar2 = func_0x00a3a960(auStack_1b8,400,uStack_530,&uStack_530,param_3,param_4),
         cVar2 == '\0')) {
LAB_00a6038c:
        bVar1 = false;
      }
      else {
        cStack_531 = cStack_529;
        cVar2 = func_0x00a3a960(auStack_1b8,400,uStack_530,&uStack_530,&cStack_531,1);
        if (cVar2 == '\0') goto LAB_00a6038c;
        bVar1 = true;
      }
      func_0x00b2ca30(param_1,param_2);
      uStack_8 = 1;
      if ((bVar1) && (cVar2 = func_0x00b2c990(auStack_1b8,uStack_530), cVar2 != '\0')) {
        bVar1 = true;
      }
      else {
        bVar1 = false;
      }
      iStack_53c = 0x14;
      if (((bVar1) && (cVar2 = func_0x00b2c9d0(auStack_28,&iStack_53c), cVar2 != '\0')) &&
         (iStack_53c == 0x14)) {
        uVar3 = param_6 - uStack_538;
        if (0x14 < uVar3) {
          uVar3 = 0x14;
        }
        cVar2 = func_0x00a3a960(param_5,param_6,uStack_538,&uStack_538,auStack_28,uVar3);
        if (cVar2 == '\0') goto LAB_00a60436;
        bVar1 = true;
      }
      else {
LAB_00a60436:
        bVar1 = false;
      }
      uStack_8 = 0xffffffff;
      func_0x00b2c980();
    } while (bVar1);
  }
  *unaff_FS_OFFSET = iStack_10;
  func_0x00af6b2f();
  return;
}

