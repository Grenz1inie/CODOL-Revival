// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 当前账号档案上下文获取
// VA: 0x006da140; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_acb437244ce9b91d58897d892f452ec7bb8fdad6d6206c506d9742096d843c77
// BEGIN PSEUDOCODE

undefined4 * FUN_006da140(void)

{
  int iVar1;
  int local_10;
  int local_c;
  
  if ((DAT_00cd7000 == 4) || (DAT_00cd7000 == 6)) {
    if ((DAT_078b08bc != 0) || (DAT_078b08c8 != 0)) {
      iVar1 = FUN_00a59520();
      local_10 = *(int *)(iVar1 + 0x20);
      local_c = *(int *)(iVar1 + 0x24);
    }
    if ((DAT_0c95bd80 != local_10) || (DAT_0c95bd84 != local_c)) {
      FUN_006d9da0(0,&local_10);
    }
  }
  return &DAT_0c95bd80;
}

