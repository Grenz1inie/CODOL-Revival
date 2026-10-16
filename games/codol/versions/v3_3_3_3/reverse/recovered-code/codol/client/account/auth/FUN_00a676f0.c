// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.auth
// Analyst label: 认证对象 24 字节字段双向掩码转换
// VA: 0x00a676f0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a676f0(int param_1,char param_2)

{
  byte *pbVar1;
  byte *pbVar2;
  int in_ECX;
  int *piVar3;
  int iVar4;
  int aiStack_7c [23];
  byte abStack_20 [24];
  uint uStack_8;
  
  uStack_8 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  iVar4 = 4;
  aiStack_7c[0xc] = 9;
  pbVar2 = (byte *)(param_1 + 1);
  abStack_20[0] = 0x34;
  abStack_20[1] = 0x88;
  abStack_20[2] = 0x3f;
  abStack_20[3] = 0xea;
  abStack_20[4] = 0x30;
  abStack_20[5] = 0x99;
  abStack_20[6] = 0xed;
  abStack_20[7] = 0xdc;
  abStack_20[8] = 0xca;
  abStack_20[9] = 0xff;
  abStack_20[10] = 3;
  abStack_20[0xb] = 0x76;
  abStack_20[0xc] = 0x34;
  abStack_20[0xd] = 0x3b;
  abStack_20[0xe] = 0xc3;
  abStack_20[0xf] = 0x21;
  abStack_20[0x10] = 9;
  abStack_20[0x11] = 0x89;
  abStack_20[0x12] = 0x61;
  abStack_20[0x13] = 0x43;
  abStack_20[0x14] = 0xfd;
  abStack_20[0x15] = 0x58;
  abStack_20[0x16] = 0x18;
  abStack_20[0x17] = 0xd3;
  aiStack_7c[0] = 0xe;
  aiStack_7c[1] = 0x12;
  aiStack_7c[2] = 3;
  aiStack_7c[3] = 0xb;
  aiStack_7c[4] = 0x14;
  aiStack_7c[5] = 2;
  aiStack_7c[6] = 6;
  aiStack_7c[7] = 0xf;
  aiStack_7c[8] = 10;
  aiStack_7c[9] = 0x11;
  aiStack_7c[10] = 0x17;
  aiStack_7c[0xb] = 1;
  aiStack_7c[0xd] = 7;
  aiStack_7c[0xe] = 0xd;
  aiStack_7c[0xf] = 0x13;
  aiStack_7c[0x10] = 0x10;
  aiStack_7c[0x11] = 0;
  aiStack_7c[0x12] = 5;
  aiStack_7c[0x13] = 0x16;
  aiStack_7c[0x14] = 0x15;
  aiStack_7c[0x15] = 4;
  aiStack_7c[0x16] = 8;
  pbVar1 = (byte *)(in_ECX + 0x69);
  piVar3 = aiStack_7c;
  do {
    if (param_2 == '\0') {
      pbVar2[-1] = abStack_20[piVar3[-1]] ^ pbVar1[-1];
      *pbVar2 = abStack_20[*piVar3] ^ *pbVar1;
      pbVar2[1] = abStack_20[piVar3[1]] ^ pbVar1[1];
      pbVar2[2] = abStack_20[piVar3[2]] ^ pbVar1[2];
      pbVar2[3] = abStack_20[piVar3[3]] ^ pbVar1[3];
      pbVar2[4] = abStack_20[piVar3[4]] ^ pbVar1[4];
    }
    else {
      pbVar1[-1] = abStack_20[piVar3[-1]] ^ pbVar2[-1];
      *pbVar1 = abStack_20[*piVar3] ^ *pbVar2;
      pbVar1[1] = abStack_20[piVar3[1]] ^ pbVar2[1];
      pbVar1[2] = abStack_20[piVar3[2]] ^ pbVar2[2];
      pbVar1[3] = abStack_20[piVar3[3]] ^ pbVar2[3];
      pbVar1[4] = abStack_20[piVar3[4]] ^ pbVar2[4];
    }
    pbVar1 = pbVar1 + 6;
    pbVar2 = pbVar2 + 6;
    piVar3 = piVar3 + 6;
    iVar4 = iVar4 + -1;
  } while (iVar4 != 0);
  func_0x00af6b2f(0xc);
  return;
}

