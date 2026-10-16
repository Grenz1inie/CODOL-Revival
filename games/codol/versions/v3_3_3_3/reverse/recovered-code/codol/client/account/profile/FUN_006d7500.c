// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案序列化与扩展字段写入
// VA: 0x006d7500; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_49d61387299a094510d358d60a8f173492b6e5188b8505523cef1baedf72f0ca
// BEGIN PSEUDOCODE

/* WARNING: Function: __alloca_probe replaced with injection: alloca_probe */

void FUN_006d7500(undefined4 param_1)

{
  uint uVar1;
  char cVar2;
  int iVar3;
  int in_ECX;
  undefined4 *puVar4;
  char *pcVar5;
  uint uVar6;
  bool bVar7;
  undefined1 auStack_2f14 [4];
  undefined4 local_2f10;
  undefined *local_2f0c;
  undefined4 local_2f08;
  int local_2f04;
  int local_2f00 [21];
  undefined4 local_2eac [2984];
  uint local_c;
  
  local_c = DAT_00cc7c80 ^ (uint)auStack_2f14;
  local_2f10 = param_1;
  pcVar5 = "mp/playerdata.def";
  if (*(int *)(in_ECX + 100) != 1) {
    pcVar5 = "mp/playersecuredata.def";
  }
  iVar3 = FUN_0049e7d0(0x27,pcVar5,1);
  local_2f04 = *(int *)(iVar3 + 8);
  if (0x7ffc < *(uint *)(local_2f04 + 0x30)) {
    FUN_00597d20(2,"943 %s %d %d",pcVar5,*(uint *)(local_2f04 + 0x30),0x7ffc);
  }
  local_2f08 = FUN_006d7d80();
  iVar3 = FUN_006d7340(in_ECX + -8);
  bVar7 = iVar3 != 0;
  if (bVar7) {
    local_2f0c = &DAT_077f3148;
  }
  else {
    local_2f0c = (undefined *)(in_ECX + 0x74);
    iVar3 = 0x8000;
  }
  cVar2 = FUN_007d0550(local_2f10);
  if ((((cVar2 == '\0') || (cVar2 = FUN_00a38f30(bVar7), cVar2 == '\0')) ||
      (cVar2 = FUN_00a38f30(1), cVar2 == '\0')) ||
     ((cVar2 = FUN_00a38f30(local_2f08), cVar2 == '\0' ||
      (cVar2 = FUN_00a39020(local_2f0c,iVar3), cVar2 == '\0')))) {
    __security_check_cookie(local_c ^ (uint)auStack_2f14);
    return;
  }
  local_2f00[0] = in_ECX + 0x78;
  uVar6 = 0;
  local_2f00[1] = 0x7ffc;
  local_2f00[2] = 0;
  uVar1 = *(uint *)(local_2f04 + 0x28);
  bVar7 = true;
  if (uVar1 < 10) {
    FUN_00630750(local_2f04,(uint *)(local_2f04 + 0x28),0,0,local_2f00,local_2f00 + 2,uVar1);
  }
  puVar4 = local_2eac;
  do {
    if ((uint)local_2f00[2] <= uVar6) break;
    switch(puVar4[-2]) {
    case 0:
      if (bVar7) {
        cVar2 = FUN_00a38ee0(*(undefined4 *)*puVar4);
LAB_006d76e2:
        if (cVar2 != '\0') {
          bVar7 = true;
          goto switchD_006d7656_caseD_2;
        }
      }
      break;
    case 1:
      if (bVar7) {
        cVar2 = FUN_00a38ee0(*(undefined1 *)*puVar4);
        goto LAB_006d76e2;
      }
      break;
    default:
      goto switchD_006d7656_caseD_2;
    case 3:
      if (bVar7) {
        cVar2 = FUN_00a38f80(*puVar4,puVar4[1]);
        goto LAB_006d76e2;
      }
      break;
    case 8:
      if (bVar7) {
        cVar2 = FUN_00a38a00(*(undefined4 *)*puVar4);
        goto LAB_006d76e2;
      }
      break;
    case 9:
      if (bVar7) {
        cVar2 = FUN_00a38ee0((int)*(short *)*puVar4);
        goto LAB_006d76e2;
      }
    }
    bVar7 = false;
switchD_006d7656_caseD_2:
    uVar6 = uVar6 + 1;
    puVar4 = puVar4 + 0x14;
  } while (bVar7);
  __security_check_cookie(local_c ^ (uint)auStack_2f14);
  return;
}

