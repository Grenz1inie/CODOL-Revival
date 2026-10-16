// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.onboarding
// Analyst label: UI 通知状态访问
// VA: 0x005953a0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_6bc47e9711bca44a0b74c03346ff294d057cc900ef70ed75f0fc0c942c4a1cd8
// BEGIN PSEUDOCODE

void FUN_005953a0(undefined4 param_1)

{
  int local_24 [2];
  undefined1 local_14 [8];
  uint local_c;
  
  local_c = DAT_00cc7c80 ^ (uint)local_24;
  local_24[0] = FUN_006da140();
  local_24[0] = local_24[0] + 0x90;
  if (local_24[0] != 0) {
    local_24[1] = 0x7ffc;
    FUN_00637be0(local_14,8,&DAT_00c5dde0,param_1);
    FUN_00592930(&stack0xffffffe4);
    __security_check_cookie(local_c ^ (uint)local_24);
    return;
  }
  __security_check_cookie(local_c ^ (uint)local_24);
  return;
}

