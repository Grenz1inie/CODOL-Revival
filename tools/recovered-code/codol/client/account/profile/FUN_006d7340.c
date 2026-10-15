// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案压缩辅助
// VA: 0x006d7340; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/profile-write.json
// BEGIN PSEUDOCODE

uint FUN_006d7340(void)

{
  int iVar1;
  uint uVar2;
  uint uStack_24;
  
  uVar2 = 0x10000;
  iVar1 = func_0x00654400();
  if (iVar1 == 0) {
    iVar1 = func_0x00654630(4);
    if (iVar1 == 1) {
      iVar1 = func_0x00654860();
      uVar2 = uStack_24;
    }
    else {
      func_0x00654860();
      if (iVar1 == 0) goto LAB_006d741a;
    }
  }
  if (iVar1 == 0) {
    if (uVar2 < 0x8001) {
      return uVar2;
    }
    func_0x006d8940(0);
    return 0;
  }
  if (iVar1 != -5) {
    if (iVar1 == -4) {
      func_0x006d8940(1);
      return 0;
    }
    if (iVar1 == -2) {
      func_0x006d8940(3);
      return 0;
    }
    func_0x006d8940(4);
    return 0;
  }
LAB_006d741a:
  func_0x006d8940(2);
  return 0;
}

