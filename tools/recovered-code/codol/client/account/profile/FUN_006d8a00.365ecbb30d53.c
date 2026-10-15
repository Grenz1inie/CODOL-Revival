// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案随机掩码初始化
// VA: 0x006d8a00; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006d8a00(void)

{
  int *piVar1;
  int iVar2;
  int unaff_EDI;
  
  piVar1 = (int *)(unaff_EDI + 0x9114);
  if (DAT_07817b6c == '\0') {
    CryptAcquireContextA(&DAT_017c6f80,0,0,1,0xf0000000);
    DAT_07817b6c = '\x01';
  }
  iVar2 = CryptGenRandom(_DAT_017c6f80,4,piVar1);
  if ((iVar2 == 0) || (*piVar1 == 0)) {
    func_0x00a367e0();
    func_0x00a36790(piVar1,4);
    func_0x00a53d80();
  }
  *(undefined1 *)(unaff_EDI + 0x9118) = 0;
  return;
}

