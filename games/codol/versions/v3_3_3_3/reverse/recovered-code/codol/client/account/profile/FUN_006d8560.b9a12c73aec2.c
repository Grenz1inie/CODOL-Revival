// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案下载状态处理
// VA: 0x006d8560; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_006d8560(void)

{
  undefined4 *puVar1;
  int iVar2;
  undefined4 uVar3;
  int unaff_EDI;
  code *pcVar4;
  int iStack_1c;
  int aiStack_18 [2];
  int iStack_10;
  int iStack_c;
  char cStack_5;
  
  iVar2 = func_0x006fed10();
  if (((iVar2 == 0) || (iVar2 = func_0x00a3c920(), iVar2 != 2)) ||
     (iStack_10 = func_0x00a3c990(), iStack_10 == 0)) {
    if (*(int *)(unaff_EDI + 0x74) != 0) {
      FUN_006d82f0(0);
    }
    return 0;
  }
  if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
    if (*(int *)(unaff_EDI + 0x6c) == 0) {
      return 0;
    }
    if (*(int *)(unaff_EDI + 0x60) == 0 && *(int *)(unaff_EDI + 100) == 0) {
      if (*(char *)(unaff_EDI + 0x68) != '\0') {
        return 0;
      }
      return 0;
    }
  }
  if (*(char *)(unaff_EDI + 0x68) != '\0') {
    return 0;
  }
  if (*(int *)(unaff_EDI + 0x74) == 1) {
    if (5 < *(int *)(unaff_EDI + 0x910c)) {
      return 0;
    }
    iVar2 = *(int *)(unaff_EDI + 0x910c) + 1;
    *(int *)(unaff_EDI + 0x910c) = iVar2;
    if (iVar2 == 6) {
      func_0x006d8940(0xc);
      uVar3 = func_0x006d82b0();
      func_0x00597d20(0,&UNK_00c7e4ac,uVar3);
      return 0;
    }
  }
  else if (*(int *)(unaff_EDI + 0x74) != 2) {
    return 0;
  }
  func_0x006fcc50();
  puVar1 = (undefined4 *)(unaff_EDI + 0x60);
  if ((iStack_1c != *(int *)(unaff_EDI + 0x60)) ||
     (cStack_5 = '\x01', aiStack_18[0] != *(int *)(unaff_EDI + 100))) {
    cStack_5 = '\0';
  }
  uVar3 = 0;
  iStack_c = 0;
  if (*(int *)(unaff_EDI + 0x6c) == 1) {
    if (*(int *)(unaff_EDI + 0x74) == 1) {
      uVar3 = FUN_00a5a890(aiStack_18,puVar1);
      FUN_006d7290(uVar3);
      func_0x00b24750();
      uVar3 = 0x18;
    }
    if (((*(int *)(unaff_EDI + 0x6c) == 1) && (*(int *)(unaff_EDI + 0x74) == 2)) &&
       ((~*(uint *)(unaff_EDI + 0x807c) & 0x7ffffff) == 0)) {
      FUN_006d8a70();
      if (cStack_5 == '\0') {
        uVar3 = FUN_00a5a650(aiStack_18,*puVar1,*(undefined4 *)(unaff_EDI + 100));
      }
      else {
        uVar3 = FUN_00a5a420(aiStack_18);
      }
      FUN_006d7290(uVar3);
      func_0x00b24750();
      uVar3 = 0x1a;
    }
  }
  if ((*(int *)(unaff_EDI + 0x6c) == 2) && (*(int *)(unaff_EDI + 0x74) == 1)) {
    if (cStack_5 == '\0') {
      uVar3 = FUN_00a5a770(aiStack_18,*puVar1,*(undefined4 *)(unaff_EDI + 100));
    }
    else {
      uVar3 = FUN_00a5a9d0(aiStack_18);
    }
    FUN_006d7290(uVar3);
    func_0x00b24750();
    uVar3 = 0x19;
  }
  if (((*(int *)(unaff_EDI + 0x6c) == 2) && (*(int *)(unaff_EDI + 0x74) == 2)) &&
     ((~*(uint *)(unaff_EDI + 0x807c) & 0x7ffffff) == 0)) {
    uVar3 = FUN_00a5a530(aiStack_18,*puVar1,*(undefined4 *)(unaff_EDI + 100));
    FUN_006d7290(uVar3);
    func_0x00b24750();
    uVar3 = 0x1b;
  }
  if (iStack_c != 0) {
    pcVar4 = FUN_006d83e0;
    iVar2 = iStack_c;
    InterlockedIncrement(iStack_c + 4);
    FUN_006f5fb0(uVar3,iVar2,pcVar4);
    func_0x00b24750();
    return 1;
  }
  func_0x00b24750();
  return 0;
}

