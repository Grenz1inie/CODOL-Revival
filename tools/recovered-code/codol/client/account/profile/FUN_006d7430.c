// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案解压与数据检查
// VA: 0x006d7430; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_baa82e2fe72c64409aaee8ece035896f1ab4fc53ad9912d87c1020f0bfee5c89
// BEGIN PSEUDOCODE

bool FUN_006d7430(uint param_1)

{
  int in_EAX;
  int iVar1;
  bool bVar2;
  
  iVar1 = param_1;
  param_1 = 0x8000;
  _memset((void *)(in_EAX + 0x7c),0,0x8000);
  if (iVar1 == 0) {
    return false;
  }
  iVar1 = FUN_00659040((void *)(in_EAX + 0x7c),&param_1,&DAT_077f3148,iVar1);
  bVar2 = iVar1 == 0;
  if (bVar2) {
    if (param_1 != 0x8000) {
      FUN_006d8940(6 - (uint)(0x8000 < param_1));
      return false;
    }
  }
  else {
    if (iVar1 != -5) {
      if (iVar1 == -4) {
        FUN_006d8940(7);
        return false;
      }
      if (iVar1 != -3) {
        FUN_006d8940(10);
        return bVar2;
      }
      FUN_006d8940(9);
      return false;
    }
    FUN_006d8940(8);
  }
  return bVar2;
}

