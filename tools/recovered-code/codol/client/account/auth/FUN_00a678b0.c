// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.auth
// Analyst label: 认证会话字段双向掩码转换
// VA: 0x00a678b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a678b0(int param_1,char param_2)

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
  pbVar2 = (byte *)(param_1 + 1);
  abStack_20[0] = 0x56;
  abStack_20[1] = 0x38;
  abStack_20[2] = 0xea;
  abStack_20[3] = 0xcd;
  abStack_20[4] = 0xfe;
  abStack_20[5] = 0x43;
  abStack_20[6] = 0x87;
  abStack_20[7] = 0x48;
  abStack_20[8] = 9;
  abStack_20[9] = 0xaa;
  abStack_20[10] = 0x36;
  abStack_20[0xb] = 0x21;
  abStack_20[0xc] = 0x75;
  abStack_20[0xd] = 0x8e;
  abStack_20[0xe] = 0xd2;
  abStack_20[0xf] = 0xc9;
  abStack_20[0x10] = 0xf0;
  abStack_20[0x11] = 0x42;
  abStack_20[0x12] = 0x80;
  abStack_20[0x13] = 0xf4;
  abStack_20[0x14] = 0xb1;
  abStack_20[0x15] = 1;
  abStack_20[0x16] = 0x5d;
  abStack_20[0x17] = 0x3f;
  aiStack_7c[0] = 3;
  aiStack_7c[1] = 0;
  aiStack_7c[2] = 0x11;
  aiStack_7c[3] = 0x12;
  aiStack_7c[4] = 0xb;
  aiStack_7c[5] = 2;
  aiStack_7c[6] = 0xe;
  aiStack_7c[7] = 10;
  aiStack_7c[8] = 5;
  aiStack_7c[9] = 0xf;
  aiStack_7c[10] = 7;
  aiStack_7c[0xb] = 0x15;
  aiStack_7c[0xc] = 0x13;
  aiStack_7c[0xd] = 8;
  aiStack_7c[0xe] = 0x16;
  aiStack_7c[0xf] = 9;
  aiStack_7c[0x10] = 4;
  aiStack_7c[0x11] = 1;
  aiStack_7c[0x12] = 0xc;
  aiStack_7c[0x13] = 0x10;
  aiStack_7c[0x14] = 6;
  aiStack_7c[0x15] = 0x14;
  aiStack_7c[0x16] = 0x17;
  pbVar1 = (byte *)(in_ECX + 0x89);
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
  func_0x00af6b2f(0xd);
  return;
}

