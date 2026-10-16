// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: 防暴盾例外与六槽位装备检查
// VA: 0x006c1190; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_8073bc16d246c34cdae1a051a07169cfd5984a7dff0ac264a5a11d0bae7f52dd
// BEGIN PSEUDOCODE

undefined4 FUN_006c1190(void)

{
  byte bVar1;
  char cVar2;
  int in_EAX;
  int iVar3;
  byte *pbVar4;
  char *pcVar5;
  bool bVar6;
  
  if (in_EAX != 0) {
    iVar3 = FUN_005845b0();
    if (iVar3 == 0) {
      pbVar4 = &DAT_00c4e869;
    }
    else {
      pbVar4 = *(byte **)(iVar3 + 0xc);
    }
    pcVar5 = "riotshield_mp";
    do {
      bVar1 = *pbVar4;
      bVar6 = bVar1 < (byte)*pcVar5;
      if (bVar1 != *pcVar5) {
LAB_006c11d3:
        iVar3 = (1 - (uint)bVar6) - (uint)(bVar6 != 0);
        goto LAB_006c11d8;
      }
      if (bVar1 == 0) break;
      bVar1 = pbVar4[1];
      bVar6 = bVar1 < (byte)pcVar5[1];
      if (bVar1 != pcVar5[1]) goto LAB_006c11d3;
      pbVar4 = pbVar4 + 2;
      pcVar5 = pcVar5 + 2;
    } while (bVar1 != 0);
    iVar3 = 0;
LAB_006c11d8:
    if (iVar3 != 0) {
      iVar3 = 0;
      do {
        cVar2 = FUN_00709570();
        if (cVar2 != '\0') {
          return 1;
        }
        iVar3 = iVar3 + 1;
      } while (iVar3 < 6);
      return 0;
    }
  }
  return 0;
}

