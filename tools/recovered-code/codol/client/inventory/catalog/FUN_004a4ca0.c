// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.catalog
// Analyst label: unlockFlagsNew 条件比较
// VA: 0x004a4ca0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_5b3a12cdceb6147f41adbe1258bb1a40b72237d32583ac434b31debabe49fbec
// BEGIN PSEUDOCODE

bool FUN_004a4ca0(uint param_1)

{
  int in_EAX;
  uint uVar1;
  char *local_18;
  undefined4 local_14;
  int local_10;
  undefined4 local_c;
  
  if (in_EAX == 0) {
    return true;
  }
  local_18 = "unlockFlagsNew";
  local_14 = FUN_00637c60(&DAT_00c5dde0);
  local_10 = FUN_006da140();
  local_10 = local_10 + 0x91b8;
  local_c = 0x7ffc;
  uVar1 = FUN_00592930(&local_18);
  return param_1 <= uVar1;
}

