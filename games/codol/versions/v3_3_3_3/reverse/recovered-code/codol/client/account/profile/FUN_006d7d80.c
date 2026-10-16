// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案 CRC 计算路径
// VA: 0x006d7d80; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_7d8cc19d471049d1a3ff1531d2d7ad1c114afe76de7bce5db1ab31474a9e3db0
// BEGIN PSEUDOCODE

void FUN_006d7d80(void)

{
  byte *pbVar1;
  uint uVar2;
  uint extraout_EDX;
  int iVar3;
  int unaff_EDI;
  
  uVar2 = 0xffffffff;
  if (DAT_0788c798 == 0) {
    FUN_006819e0();
    uVar2 = extraout_EDX;
  }
  iVar3 = 0x1fff;
  pbVar1 = (byte *)(unaff_EDI + 0x81);
  do {
    uVar2 = uVar2 >> 8 ^ (&DAT_0379d420)[(pbVar1[-1] ^ uVar2) & 0xff];
    uVar2 = uVar2 >> 8 ^ (&DAT_0379d420)[(*pbVar1 ^ uVar2) & 0xff];
    uVar2 = uVar2 >> 8 ^ (&DAT_0379d420)[(pbVar1[1] ^ uVar2) & 0xff];
    uVar2 = uVar2 >> 8 ^ (&DAT_0379d420)[(pbVar1[2] ^ uVar2) & 0xff];
    iVar3 = iVar3 + -1;
    pbVar1 = pbVar1 + 4;
  } while (iVar3 != 0);
  *(uint *)(unaff_EDI + 0x7c) = ~uVar2;
  return;
}

