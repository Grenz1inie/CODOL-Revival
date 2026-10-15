// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案异步任务完成处理
// VA: 0x006d83e0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_37adaed9d139608621986c84f87a7f3b3b4792d3bdcd6ccefebec572c8a67d02
// BEGIN PSEUDOCODE

void FUN_006d83e0(int param_1,undefined4 param_2)

{
  int iVar1;
  int iVar2;
  char cVar3;
  undefined1 local_9;
  
  iVar1 = *(int *)(param_1 + 0x38);
  iVar2 = FUN_00a44cf0();
  if (iVar1 != 0) {
    cVar3 = (char)param_2;
    if ((cVar3 != '\0') || (local_9 = cVar3, iVar2 == 800)) {
      local_9 = '\x01';
    }
    if (*(int *)(iVar1 + 0x58) == 0) {
      if (iVar2 == 800) {
        FUN_006d7d80();
      }
      if ((cVar3 == '\0') && (DAT_0788c798 == 0)) {
        FUN_006819e0();
      }
    }
    else if ((cVar3 != '\0') || (local_9 = cVar3, iVar2 == 0)) {
      local_9 = '\x01';
    }
    if (((*(int *)(iVar1 + 0x74) == 2) || (*(int *)(iVar1 + 0x74) == 4)) &&
       (*(int *)(iVar1 + 0x6c) == 1)) {
      *(undefined1 *)(iVar1 + 0x9118) = 1;
      FUN_006d90c0(iVar1);
    }
    if ((*(int *)(iVar1 + 0x74) == 2) && (*(int *)(iVar1 + 0x6c) == 2)) {
      FUN_004e6d60(*(undefined4 *)(iVar1 + 0x60),*(undefined4 *)(iVar1 + 100),param_2);
    }
    iVar2 = *(int *)(iVar1 + 0x74);
    FUN_006d82f0(local_9 != '\0');
    if (((iVar2 == 1) && (local_9 == '\0')) && (*(int *)(iVar1 + 0x58) == 0)) {
      FUN_006d87d0();
    }
  }
  return;
}

