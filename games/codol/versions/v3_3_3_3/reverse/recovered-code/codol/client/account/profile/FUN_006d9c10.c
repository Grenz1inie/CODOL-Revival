// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 公开和私有 dwProfile 对象初始化
// VA: 0x006d9c10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_49d61387299a094510d358d60a8f173492b6e5188b8505523cef1baedf72f0ca
// BEGIN PSEUDOCODE

void FUN_006d9c10(void)

{
  int *pbBuffer;
  BOOL BVar1;
  undefined4 *in_ECX;
  undefined4 *puVar2;
  int local_10;
  
  puVar2 = in_ECX + 4;
  local_10 = 1;
  do {
    puVar2[1] = &DAT_00c7e518;
    puVar2[3] = &DAT_00c7e520;
    puVar2[0x2448] = bdReferencable::vftable;
    puVar2[0x2449] = 0;
    FUN_00a5a240(0);
    *puVar2 = dwProfile::vftable;
    puVar2[2] = dwProfile::vftable;
    *(undefined ***)(*(int *)(puVar2[1] + 4) + 4 + (int)puVar2) = dwProfile::vftable;
    puVar2[0x2422] = 0;
    puVar2[0x2423] = 0;
    puVar2[0x16] = 0;
    puVar2[0x18] = 0;
    puVar2[0x19] = 0;
    *(undefined1 *)(puVar2 + 0x1a) = 0;
    puVar2[0x1b] = 0;
    puVar2[0x1c] = 0;
    puVar2[0x1d] = 0;
    puVar2[0x1e] = 0;
    puVar2[0x2447] = 0;
    puVar2[0x2425] = 0;
    puVar2[0x2426] = 0;
    puVar2[0x2443] = 0;
    puVar2[0x2444] = 0xffffffff;
    *(undefined2 *)(puVar2 + 0x2424) = 0x100;
    _memset(puVar2 + 0x1f,0,0x8000);
    if (DAT_07817b6c == '\0') {
      CryptAcquireContextA(&DAT_017c6f80,(LPCSTR)0x0,(LPCSTR)0x0,1,0xf0000000);
      DAT_07817b6c = '\x01';
    }
    pbBuffer = puVar2 + 0x2445;
    BVar1 = CryptGenRandom(DAT_017c6f80,4,(BYTE *)pbBuffer);
    if ((BVar1 == 0) || (*pbBuffer == 0)) {
      FUN_00a367e0();
      FUN_00a36790(pbBuffer,4);
      FUN_00a53d80();
    }
    *(undefined1 *)(puVar2 + 0x2446) = 0;
    _memset(puVar2 + 0x2021,0,0x1000);
    if (puVar2[0x2422] != 0) {
      FUN_00af6cad(puVar2[0x2422]);
      puVar2[0x2422] = 0;
      puVar2[0x2423] = 0;
    }
    puVar2[0x2020] = 0;
    puVar2[0x201f] = 0;
    *(undefined2 *)(puVar2 + 0x2421) = 0;
    *(undefined1 *)(puVar2 + 6) = 0;
    puVar2 = puVar2 + 0x244a;
    local_10 = local_10 + -1;
  } while (-1 < local_10);
  *in_ECX = 0;
  in_ECX[1] = 0;
  return;
}

