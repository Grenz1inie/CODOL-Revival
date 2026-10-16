// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 账号切换时重置公开和私有档案
// VA: 0x006d9da0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_4100af57eb5bef281c813784514b85b29aed35ff08066a379c9b5a9b5724874f
// BEGIN PSEUDOCODE

void FUN_006d9da0(undefined4 param_1,undefined4 *param_2)

{
  undefined4 uVar1;
  undefined4 uVar2;
  BOOL BVar3;
  int iVar4;
  char *pcVar5;
  undefined4 *in_ECX;
  char *pcVar6;
  undefined4 *puVar7;
  int iVar8;
  undefined4 local_5c;
  undefined4 local_58;
  char local_4c [68];
  uint local_8;
  
  local_8 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  uVar1 = param_2[1];
  *in_ECX = *param_2;
  in_ECX[1] = uVar1;
  iVar8 = 0;
  puVar7 = in_ECX + 0x22;
  do {
    puVar7[-8] = 0;
    puVar7[-6] = 0;
    puVar7[-5] = 0;
    *(undefined1 *)(puVar7 + -4) = 0;
    puVar7[-3] = 0;
    puVar7[-2] = 0;
    puVar7[-1] = 0;
    *puVar7 = 0;
    puVar7[0x2429] = 0;
    puVar7[0x2407] = 0;
    puVar7[0x2408] = 0;
    puVar7[0x2425] = 0;
    puVar7[0x2426] = 0xffffffff;
    *(undefined2 *)(puVar7 + 0x2406) = 0x100;
    _memset(puVar7 + 1,0,0x8000);
    if (DAT_07817b6c == '\0') {
      CryptAcquireContextA(&DAT_017c6f80,(LPCSTR)0x0,(LPCSTR)0x0,1,0xf0000000);
      DAT_07817b6c = '\x01';
    }
    BVar3 = CryptGenRandom(DAT_017c6f80,4,(BYTE *)(puVar7 + 0x2427));
    if ((BVar3 == 0) || (puVar7[0x2427] == 0)) {
      FUN_00a367e0();
      FUN_00a36790(puVar7 + 0x2427,4);
      FUN_00a53d80();
    }
    *(undefined1 *)(puVar7 + 0x2428) = 0;
    _memset(puVar7 + 0x2003,0,0x1000);
    if (puVar7[0x2404] != 0) {
      FUN_00af6cad(puVar7[0x2404]);
      puVar7[0x2404] = 0;
      puVar7[0x2405] = 0;
    }
    puVar7[-8] = param_1;
    iVar4 = DAT_078b08bc;
    uVar1 = *param_2;
    uVar2 = param_2[1];
    iVar8 = iVar8 + 1;
    puVar7[0x2002] = 0;
    puVar7[0x2001] = 0;
    *(undefined2 *)(puVar7 + 0x2403) = 0;
    *(undefined1 *)(puVar7 + -0x18) = 0;
    puVar7[-6] = uVar1;
    puVar7[-5] = uVar2;
    *(undefined1 *)(puVar7 + -4) = 0;
    puVar7[-3] = iVar8;
    puVar7[-2] = 1;
    local_4c[0] = '\0';
    if ((iVar4 != 0) || (DAT_078b08c8 != 0)) {
      iVar4 = FUN_00a59520();
      local_5c = *(undefined4 *)(iVar4 + 0x20);
      local_58 = *(undefined4 *)(iVar4 + 0x24);
    }
    __snprintf(&DAT_0ca10870,0x100,"[ 0|%24llu]CL",local_5c,local_58);
    DAT_0ca1096f = 0;
    _strncpy(local_4c,&DAT_0ca10870,0x40);
    iVar4 = puVar7[-3];
    if (iVar4 == 0) {
LAB_006d9f77:
      pcVar6 = "NONE";
    }
    else if (iVar4 == 1) {
      pcVar6 = "public";
    }
    else {
      if (iVar4 != 2) goto LAB_006d9f77;
      pcVar6 = "private";
    }
    iVar4 = puVar7[-2];
    if (iVar4 == 0) {
LAB_006d9f97:
      pcVar5 = "NONE";
    }
    else if (iVar4 == 1) {
      pcVar5 = "client";
    }
    else {
      if (iVar4 != 2) goto LAB_006d9f97;
      pcVar5 = "server";
    }
    FUN_00637be0(puVar7 + -0x18,0x40,"%s Profile %s|%8s",local_4c,pcVar5,pcVar6);
    puVar7 = puVar7 + 0x244a;
    if (1 < iVar8) {
      __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
      return;
    }
  } while( true );
}

