// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案随机掩码初始化
// VA: 0x006d8a00; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_809054723794266787c51e70d0cb7f793b1ca3b0828acef7bccc38088d67e3b8
// BEGIN PSEUDOCODE

void FUN_006d8a00(void)

{
  int *pbBuffer;
  BOOL BVar1;
  int unaff_EDI;
  
  pbBuffer = (int *)(unaff_EDI + 0x9114);
  if (DAT_07817b6c == '\0') {
    CryptAcquireContextA(&DAT_017c6f80,(LPCSTR)0x0,(LPCSTR)0x0,1,0xf0000000);
    DAT_07817b6c = '\x01';
  }
  BVar1 = CryptGenRandom(DAT_017c6f80,4,(BYTE *)pbBuffer);
  if ((BVar1 == 0) || (*pbBuffer == 0)) {
    FUN_00a367e0();
    FUN_00a36790(pbBuffer,4);
    FUN_00a53d80();
  }
  *(undefined1 *)(unaff_EDI + 0x9118) = 0;
  return;
}

