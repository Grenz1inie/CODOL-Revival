// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 当前账号档案上下文获取
// VA: 0x006da140; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined * FUN_006da140(void)

{
  int iVar1;
  int iStack_10;
  int iStack_c;
  
  if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
    if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
      iVar1 = func_0x00a59520();
      iStack_10 = *(int *)(iVar1 + 0x20);
      iStack_c = *(int *)(iVar1 + 0x24);
    }
    if ((_DAT_0c95bd80 != iStack_10) || (_DAT_0c95bd84 != iStack_c)) {
      FUN_006d9da0(0,&iStack_10);
    }
  }
  return &DAT_0c95bd80;
}

