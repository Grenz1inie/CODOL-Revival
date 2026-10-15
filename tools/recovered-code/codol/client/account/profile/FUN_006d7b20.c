// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 按档案类型选择 DDL 定义
// VA: 0x006d7b20; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_49d61387299a094510d358d60a8f173492b6e5188b8505523cef1baedf72f0ca
// BEGIN PSEUDOCODE

/* WARNING: Function: __alloca_probe replaced with injection: alloca_probe */

void FUN_006d7b20(void)

{
  uint uVar1;
  int iVar2;
  int in_ECX;
  undefined1 *puVar3;
  char *pcVar4;
  undefined1 auStack_2f04 [4];
  int local_2f00 [22];
  undefined1 local_2ea8 [11932];
  uint local_c;
  
  local_c = DAT_00cc7c80 ^ (uint)auStack_2f04;
  pcVar4 = "mp/playerdata.def";
  if (*(int *)(in_ECX + 0x6c) != 1) {
    pcVar4 = "mp/playersecuredata.def";
  }
  iVar2 = FUN_0049e7d0(0x27,pcVar4,1);
  iVar2 = *(int *)(iVar2 + 8);
  if (0x7ffc < *(uint *)(iVar2 + 0x30)) {
    FUN_00597d20(2,"943 %s %d %d",pcVar4,*(uint *)(iVar2 + 0x30),0x7ffc);
  }
  local_2f00[0] = in_ECX + 0x80;
  local_2f00[1] = 0x7ffc;
  local_2f00[2] = 0;
  uVar1 = *(uint *)(iVar2 + 0x28);
  if (uVar1 < 10) {
    FUN_00630750(iVar2,(uint *)(iVar2 + 0x28),0,0,local_2f00,local_2f00 + 2,uVar1);
  }
  if (local_2f00[2] != 0) {
    puVar3 = local_2ea8;
    iVar2 = local_2f00[2];
    do {
      switch(*(undefined4 *)(puVar3 + -0xc)) {
      case 0:
      case 1:
      case 8:
      case 9:
        break;
      case 3:
      }
      puVar3 = puVar3 + 0x50;
      iVar2 = iVar2 + -1;
    } while (iVar2 != 0);
  }
  __security_check_cookie(local_c ^ (uint)auStack_2f04);
  return;
}

