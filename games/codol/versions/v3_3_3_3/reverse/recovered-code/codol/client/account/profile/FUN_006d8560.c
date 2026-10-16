// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案下载状态处理
// VA: 0x006d8560; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_7333536d816d3bf0cc6f0061ae585c658391fe6ef64f2392feaf765d7d27dcee
// BEGIN PSEUDOCODE

undefined4 FUN_006d8560(void)

{
  undefined4 *puVar1;
  int iVar2;
  undefined4 uVar3;
  int unaff_EDI;
  code *pcVar4;
  int local_1c;
  int local_18 [2];
  int local_10;
  int local_c;
  char local_5;
  
  iVar2 = FUN_006fed10();
  if (((iVar2 == 0) || (iVar2 = FUN_00a3c920(), iVar2 != 2)) ||
     (local_10 = FUN_00a3c990(), local_10 == 0)) {
    if (*(int *)(unaff_EDI + 0x74) != 0) {
      FUN_006d82f0(0);
    }
    return 0;
  }
  if ((DAT_00cd7000 == 4) || (DAT_00cd7000 == 6)) {
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
      FUN_006d8940(0xc);
      uVar3 = FUN_006d82b0();
      FUN_00597d20(0,"WIN_PROFILE_DOWNLOAD_FAILURE",uVar3);
      return 0;
    }
  }
  else if (*(int *)(unaff_EDI + 0x74) != 2) {
    return 0;
  }
  FUN_006fcc50();
  puVar1 = (undefined4 *)(unaff_EDI + 0x60);
  if ((local_1c != *(int *)(unaff_EDI + 0x60)) ||
     (local_5 = '\x01', local_18[0] != *(int *)(unaff_EDI + 100))) {
    local_5 = '\0';
  }
  uVar3 = 0;
  local_c = 0;
  if (*(int *)(unaff_EDI + 0x6c) == 1) {
    if (*(int *)(unaff_EDI + 0x74) == 1) {
      uVar3 = FUN_00a5a890(local_18,puVar1,unaff_EDI,1);
      FUN_006d7290(uVar3);
      FUN_00b24750();
      uVar3 = 0x18;
    }
    if (((*(int *)(unaff_EDI + 0x6c) == 1) && (*(int *)(unaff_EDI + 0x74) == 2)) &&
       ((~*(uint *)(unaff_EDI + 0x807c) & 0x7ffffff) == 0)) {
      FUN_006d8a70(unaff_EDI);
      if (local_5 == '\0') {
        uVar3 = FUN_00a5a650(local_18,*puVar1,*(undefined4 *)(unaff_EDI + 100),unaff_EDI);
      }
      else {
        uVar3 = FUN_00a5a420(local_18,unaff_EDI);
      }
      FUN_006d7290(uVar3);
      FUN_00b24750();
      uVar3 = 0x1a;
    }
  }
  if ((*(int *)(unaff_EDI + 0x6c) == 2) && (*(int *)(unaff_EDI + 0x74) == 1)) {
    if (local_5 == '\0') {
      uVar3 = FUN_00a5a770(local_18,*puVar1,*(undefined4 *)(unaff_EDI + 100),unaff_EDI);
    }
    else {
      uVar3 = FUN_00a5a9d0(local_18,unaff_EDI);
    }
    FUN_006d7290(uVar3);
    FUN_00b24750();
    uVar3 = 0x19;
  }
  if (((*(int *)(unaff_EDI + 0x6c) == 2) && (*(int *)(unaff_EDI + 0x74) == 2)) &&
     ((~*(uint *)(unaff_EDI + 0x807c) & 0x7ffffff) == 0)) {
    uVar3 = FUN_00a5a530(local_18,*puVar1,*(undefined4 *)(unaff_EDI + 100),unaff_EDI);
    FUN_006d7290(uVar3);
    FUN_00b24750();
    uVar3 = 0x1b;
  }
  if (local_c != 0) {
    pcVar4 = FUN_006d83e0;
    iVar2 = local_c;
    InterlockedIncrement((LONG *)(local_c + 4));
    FUN_006f5fb0(uVar3,iVar2,pcVar4);
    FUN_00b24750();
    return 1;
  }
  FUN_00b24750();
  return 0;
}

