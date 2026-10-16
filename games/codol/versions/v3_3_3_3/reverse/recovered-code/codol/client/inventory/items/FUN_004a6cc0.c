// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.items
// Analyst label: 库存条目转移路径
// VA: 0x004a6cc0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_62b6c641a80115cc8af23d1b718afabc77d48612d9993ac6e356b27bcfd074a4
// BEGIN PSEUDOCODE

void FUN_004a6cc0(char param_1,undefined4 param_2)

{
  undefined4 uVar1;
  int iVar2;
  undefined4 uVar3;
  char local_90 [63];
  undefined1 local_51;
  undefined1 local_50 [68];
  uint local_c;
  
  local_c = DAT_00cc7c80 ^ (uint)local_90;
  DAT_07817df8 = DAT_07817df8 | 1;
  DAT_07817df1 = param_1;
  if (param_1 != '\0') {
    uVar3 = 0;
    uVar1 = 0;
    if ((DAT_078b08bc != 0) || (DAT_078b08c8 != 0)) {
      iVar2 = FUN_00a59520();
      uVar3 = *(undefined4 *)(iVar2 + 0x20);
      uVar1 = *(undefined4 *)(iVar2 + 0x24);
    }
    FUN_00637be0(local_50,0x40,&DAT_00c61270,uVar3,uVar1);
    if (DAT_07809d68 == 0) {
      local_90[0] = '\0';
    }
    else {
      _strncpy(local_90,*(char **)(DAT_07809d68 + 0xc),0x3f);
      local_51 = 0;
    }
    if (DAT_078b0880 == 1) {
      FUN_006fc940();
    }
    DAT_07817ddc = param_2;
    FUN_005e2a50();
  }
  __security_check_cookie(local_c ^ (uint)local_90);
  return;
}

