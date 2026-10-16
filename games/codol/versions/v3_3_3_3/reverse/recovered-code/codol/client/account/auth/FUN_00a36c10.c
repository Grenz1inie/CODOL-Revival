// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.auth
// Analyst label: 认证票据 Base64 字符解码和长度边界
// VA: 0x00a36c10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby-tail.json
// BEGIN PSEUDOCODE

uint FUN_00a36c10(char *param_1,uint param_2,int param_3,uint param_4,int param_5)

{
  char cVar1;
  byte bVar2;
  char *pcVar3;
  byte bVar4;
  uint uVar5;
  uint uVar6;
  char cStack_c;
  char cStack_8;
  
  uVar5 = 0;
  pcVar3 = param_1;
  if (param_1 != (char *)0x0) {
    for (; ((cVar1 = *pcVar3, '\b' < cVar1 && (cVar1 < '\x0e')) || (cVar1 == ' '));
        pcVar3 = pcVar3 + 1) {
    }
  }
  uVar6 = uVar5;
  if (pcVar3 != param_1 + param_2) {
    while (cStack_c = *pcVar3, uVar6 = uVar5, cStack_c != '=') {
      if ((byte)(cStack_c + 0xbfU) < 0x1a) {
        cStack_c = cStack_c + -0x41;
      }
      else if ((byte)(cStack_c + 0x9fU) < 0x1a) {
        cStack_c = cStack_c + -0x47;
      }
      else if ((byte)(cStack_c - 0x30U) < 10) {
        cStack_c = cStack_c + '\x04';
      }
      else if (cStack_c == *(char *)(param_5 + 0x3e)) {
        cStack_c = '>';
      }
      else if (cStack_c == *(char *)(param_5 + 0x3f)) {
        cStack_c = '?';
      }
      else {
        func_0x00a53d80((int)cStack_c);
        cStack_c = '\0';
      }
      pcVar3 = pcVar3 + 1;
      if (pcVar3 != (char *)0x0) {
        for (; ((cVar1 = *pcVar3, '\b' < cVar1 && (cVar1 < '\x0e')) || (cVar1 == ' '));
            pcVar3 = pcVar3 + 1) {
        }
      }
      cStack_8 = *pcVar3;
      if ((byte)(cStack_8 + 0xbfU) < 0x1a) {
        cStack_8 = cStack_8 + -0x41;
      }
      else if ((byte)(cStack_8 + 0x9fU) < 0x1a) {
        cStack_8 = cStack_8 + -0x47;
      }
      else if ((byte)(cStack_8 - 0x30U) < 10) {
        cStack_8 = cStack_8 + '\x04';
      }
      else if (cStack_8 == *(char *)(param_5 + 0x3e)) {
        cStack_8 = '>';
      }
      else if (cStack_8 == *(char *)(param_5 + 0x3f)) {
        cStack_8 = '?';
      }
      else {
        func_0x00a53d80((int)cStack_8);
        cStack_8 = '\0';
      }
      bVar4 = cStack_8 >> 4 & 3U | cStack_c * '\x04';
      if (param_4 <= uVar5) break;
      *(byte *)(uVar5 + param_3) = bVar4;
      uVar6 = uVar5 + 1;
      pcVar3 = pcVar3 + 1;
      if (pcVar3 != (char *)0x0) {
        for (; ((cVar1 = *pcVar3, '\b' < cVar1 && (cVar1 < '\x0e')) || (cVar1 == ' '));
            pcVar3 = pcVar3 + 1) {
        }
      }
      if ((uint)((int)pcVar3 - (int)param_1) < param_2) {
        if ((*pcVar3 == '=') || (bVar4 = func_0x00a36b80(), param_4 <= uVar6)) break;
        *(byte *)(uVar6 + param_3) = (char)bVar4 >> 2 & 0xfU | cStack_8 << 4;
        uVar6 = uVar5 + 2;
      }
      uVar5 = uVar6;
      pcVar3 = pcVar3 + 1;
      if (pcVar3 != (char *)0x0) {
        for (; ((cVar1 = *pcVar3, '\b' < cVar1 && (cVar1 < '\x0e')) || (cVar1 == ' '));
            pcVar3 = pcVar3 + 1) {
        }
      }
      if ((uint)((int)pcVar3 - (int)param_1) < param_2) {
        uVar6 = uVar5;
        if ((*pcVar3 == '=') || (bVar2 = func_0x00a36b80(), param_4 <= uVar5)) break;
        *(byte *)(uVar5 + param_3) = bVar4 << 6 | bVar2;
        uVar5 = uVar5 + 1;
      }
      pcVar3 = pcVar3 + 1;
      if (pcVar3 != (char *)0x0) {
        for (; ((cVar1 = *pcVar3, '\b' < cVar1 && (cVar1 < '\x0e')) || (cVar1 == ' '));
            pcVar3 = pcVar3 + 1) {
        }
      }
      uVar6 = uVar5;
      if (pcVar3 == param_1 + param_2) break;
    }
    if (param_4 < uVar6) {
      func_0x00a53d80(param_4,uVar6);
    }
  }
  return uVar6;
}

