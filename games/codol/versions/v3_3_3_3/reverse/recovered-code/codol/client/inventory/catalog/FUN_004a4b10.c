// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.catalog
// Analyst label: 解锁条件名称到索引
// VA: 0x004a4b10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_9dce6628889f74083e9b6053ff33d71dc4bc53d316e1b14e1b5e70ebda5f7b0b
// BEGIN PSEUDOCODE

undefined4 FUN_004a4b10(undefined4 param_1)

{
  char cVar1;
  int iVar2;
  int iVar3;
  char *pcVar4;
  undefined4 uVar5;
  char *pcVar6;
  
  iVar2 = FUN_0049e7d0(0x25,"mp/unlockFlags.csv",1);
  if (iVar2 == 0) {
    pcVar6 = "";
  }
  else {
    iVar3 = FUN_0062f6c0(iVar2,0,param_1);
    if ((((*(int *)(iVar2 + 4) < 2) || (*(int *)(iVar2 + 8) <= iVar3)) || (iVar3 < 0)) ||
       (pcVar6 = *(char **)(*(int *)(iVar2 + 0xc) + 8 + *(int *)(iVar2 + 4) * iVar3 * 8),
       pcVar6 == (char *)0x0)) {
      pcVar6 = "";
    }
  }
  pcVar4 = pcVar6;
  do {
    cVar1 = *pcVar4;
    pcVar4 = pcVar4 + 1;
  } while (cVar1 != '\0');
  if (pcVar4 == pcVar6 + 1) {
    return 0;
  }
  uVar5 = FUN_00af6e68(pcVar6);
  return uVar5;
}

