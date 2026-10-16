// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 账号切换时重置公开和私有档案
// VA: 0x006d9da0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006d9da0(undefined4 param_1,undefined4 *param_2)

{
  undefined4 uVar1;
  undefined4 uVar2;
  int iVar3;
  undefined *puVar4;
  undefined4 *in_ECX;
  undefined *puVar5;
  undefined4 *puVar6;
  int iVar7;
  undefined4 uStack_5c;
  undefined4 uStack_58;
  undefined1 auStack_4c [68];
  uint uStack_8;
  
  uStack_8 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  uVar1 = param_2[1];
  *in_ECX = *param_2;
  in_ECX[1] = uVar1;
  iVar7 = 0;
  puVar6 = in_ECX + 0x22;
  do {
    puVar6[-8] = 0;
    puVar6[-6] = 0;
    puVar6[-5] = 0;
    *(undefined1 *)(puVar6 + -4) = 0;
    puVar6[-3] = 0;
    puVar6[-2] = 0;
    puVar6[-1] = 0;
    *puVar6 = 0;
    puVar6[0x2429] = 0;
    puVar6[0x2407] = 0;
    puVar6[0x2408] = 0;
    puVar6[0x2425] = 0;
    puVar6[0x2426] = 0xffffffff;
    *(undefined2 *)(puVar6 + 0x2406) = 0x100;
    func_0x00afd440(puVar6 + 1,0,0x8000);
    if (DAT_07817b6c == '\0') {
      CryptAcquireContextA(&DAT_017c6f80,0,0,1,0xf0000000);
      DAT_07817b6c = '\x01';
    }
    iVar3 = CryptGenRandom(_DAT_017c6f80,4,puVar6 + 0x2427);
    if ((iVar3 == 0) || (puVar6[0x2427] == 0)) {
      func_0x00a367e0();
      func_0x00a36790(puVar6 + 0x2427,4);
      func_0x00a53d80();
    }
    *(undefined1 *)(puVar6 + 0x2428) = 0;
    func_0x00afd440(puVar6 + 0x2003,0,0x1000);
    if (puVar6[0x2404] != 0) {
      func_0x00af6cad(puVar6[0x2404]);
      puVar6[0x2404] = 0;
      puVar6[0x2405] = 0;
    }
    puVar6[-8] = param_1;
    iVar3 = _DAT_078b08bc;
    uVar1 = *param_2;
    uVar2 = param_2[1];
    iVar7 = iVar7 + 1;
    puVar6[0x2002] = 0;
    puVar6[0x2001] = 0;
    *(undefined2 *)(puVar6 + 0x2403) = 0;
    *(undefined1 *)(puVar6 + -0x18) = 0;
    puVar6[-6] = uVar1;
    puVar6[-5] = uVar2;
    *(undefined1 *)(puVar6 + -4) = 0;
    puVar6[-3] = iVar7;
    puVar6[-2] = 1;
    auStack_4c[0] = 0;
    if ((iVar3 != 0) || (_DAT_078b08c8 != 0)) {
      iVar3 = func_0x00a59520();
      uStack_5c = *(undefined4 *)(iVar3 + 0x20);
      uStack_58 = *(undefined4 *)(iVar3 + 0x24);
    }
    func_0x00af99e3(0xca10870,0x100,&UNK_00c61498,uStack_5c,uStack_58);
    DAT_0ca1096f = 0;
    func_0x00af75c0(auStack_4c,0xca10870,0x40);
    iVar3 = puVar6[-3];
    if (iVar3 == 0) {
LAB_006d9f77:
      puVar5 = &UNK_00c4ed04;
    }
    else if (iVar3 == 1) {
      puVar5 = &UNK_00c60478;
    }
    else {
      if (iVar3 != 2) goto LAB_006d9f77;
      puVar5 = &UNK_00c60480;
    }
    iVar3 = puVar6[-2];
    if (iVar3 == 0) {
LAB_006d9f97:
      puVar4 = &UNK_00c4ed04;
    }
    else if (iVar3 == 1) {
      puVar4 = &UNK_00c62264;
    }
    else {
      if (iVar3 != 2) goto LAB_006d9f97;
      puVar4 = &UNK_00c6225c;
    }
    func_0x00637be0(puVar6 + -0x18,0x40,&UNK_00c7e488,auStack_4c,puVar4,puVar5);
    puVar6 = puVar6 + 0x244a;
    if (1 < iVar7) {
      func_0x00af6b2f();
      return;
    }
  } while( true );
}

