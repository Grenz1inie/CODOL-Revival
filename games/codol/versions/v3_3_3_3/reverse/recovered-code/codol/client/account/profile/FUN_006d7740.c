// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案反序列化与 DDL 扩展字段读取
// VA: 0x006d7740; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_baa82e2fe72c64409aaee8ece035896f1ab4fc53ad9912d87c1020f0bfee5c89
// BEGIN PSEUDOCODE

/* WARNING: Function: __alloca_probe replaced with injection: alloca_probe */
/* WARNING: Removing unreachable block (ram,0x006d7987) */

void FUN_006d7740(undefined4 *param_1)

{
  bool bVar1;
  char cVar2;
  int iVar3;
  LONG LVar4;
  int in_ECX;
  int iVar5;
  char *pcVar6;
  uint uVar7;
  undefined4 *puVar8;
  undefined1 auStack_2f5c [7];
  char local_2f55;
  rsize_t local_2f54;
  undefined4 local_2f50;
  int local_2f4c;
  int local_2f48;
  int local_2f44;
  int local_2f40 [21];
  undefined4 local_2eec [2983];
  char local_50 [68];
  uint local_c;
  
  local_c = DAT_00cc7c80 ^ (uint)auStack_2f5c;
  local_2f50 = 0;
  pcVar6 = "mp/playerdata.def";
  if (*(int *)(in_ECX + 0x6c) != 1) {
    pcVar6 = "mp/playersecuredata.def";
  }
  iVar3 = FUN_0049e7d0(0x27,pcVar6,1);
  iVar3 = *(int *)(iVar3 + 8);
  if (0x7ffc < *(uint *)(iVar3 + 0x30)) {
    FUN_00597d20(2,"943 %s %d %d",pcVar6,*(uint *)(iVar3 + 0x30),0x7ffc);
  }
  puVar8 = param_1;
  if (param_1 != (undefined4 *)0x0) {
    InterlockedIncrement(param_1 + 1);
  }
  cVar2 = FUN_00a5a370(puVar8);
  local_2f48 = 0;
  local_2f4c = 0;
  local_2f44 = 0;
  if ((cVar2 == '\0') || (cVar2 = FUN_00a38a60(&local_2f48), cVar2 == '\0')) {
    bVar1 = false;
  }
  else {
    bVar1 = true;
  }
  local_2f55 = local_2f48 != 0;
  if (((bVar1) && (cVar2 = FUN_00a38a60(&local_2f4c), cVar2 != '\0')) &&
     (cVar2 = FUN_00a38a60(&local_2f44), cVar2 != '\0')) {
    bVar1 = true;
  }
  else {
    bVar1 = false;
  }
  local_2f54 = 0x8000;
  if ((bVar1) && (cVar2 = FUN_00a392b0(&DAT_077f3148,&local_2f54), cVar2 != '\0')) {
    bVar1 = true;
    if (local_2f54 == 0) {
      bVar1 = false;
      _strncpy(local_50,(char *)(in_ECX + 0x18),0x40);
      pcVar6 = local_50;
      do {
        cVar2 = *pcVar6;
        pcVar6 = pcVar6 + 1;
      } while (cVar2 != '\0');
      iVar5 = 0;
      if (0 < (int)pcVar6 - (int)(local_50 + 1)) {
        do {
          if (local_50[iVar5] == '|') {
            local_50[iVar5] = '-';
          }
          iVar5 = iVar5 + 1;
        } while (iVar5 < (int)pcVar6 - (int)(local_50 + 1));
      }
      FUN_00597d20(0,"1125 %s",local_50);
    }
  }
  else {
    bVar1 = false;
  }
  if (local_2f55 == '\0') {
    _memcpy_s((void *)(in_ECX + 0x7c),0x8000,&DAT_077f3148,local_2f54);
    if (bVar1) goto LAB_006d7900;
  }
  else if ((bVar1) && (cVar2 = FUN_006d7430(local_2f54), cVar2 != '\0')) {
LAB_006d7900:
    iVar5 = FUN_006d7d80();
    if (local_2f4c != 1) goto LAB_006d7aad;
    if (local_2f44 == iVar5) {
      local_2f40[0] = in_ECX + 0x80;
      local_2f40[1] = 0x7ffc;
      local_2f40[2] = 0;
      uVar7 = *(uint *)(iVar3 + 0x28);
      if (uVar7 < 10) {
        FUN_00630750(iVar3,(uint *)(iVar3 + 0x28),0,0,local_2f40,local_2f40 + 2,uVar7);
      }
      uVar7 = 0;
      puVar8 = local_2eec;
      bVar1 = true;
      do {
        if ((uint)local_2f40[2] <= uVar7) break;
        switch(puVar8[-2]) {
        case 0:
          if (bVar1) {
            cVar2 = FUN_00a39130(*puVar8);
LAB_006d7a97:
            if (cVar2 != '\0') {
              bVar1 = true;
              break;
            }
          }
          goto LAB_006d7a9f;
        case 1:
          if ((bVar1) && (cVar2 = FUN_00a39130(&local_2f50), cVar2 != '\0')) {
            bVar1 = true;
            *(undefined1 *)*puVar8 = (undefined1)local_2f50;
          }
          else {
            bVar1 = false;
            *(undefined1 *)*puVar8 = (undefined1)local_2f50;
          }
          break;
        case 3:
          if (bVar1) {
            cVar2 = FUN_00a39250(*puVar8,puVar8[1]);
            goto LAB_006d7a97;
          }
          goto LAB_006d7a9f;
        case 8:
          if (bVar1) {
            cVar2 = FUN_00a39210(*puVar8);
            goto LAB_006d7a97;
          }
LAB_006d7a9f:
          bVar1 = false;
          break;
        case 9:
          if ((bVar1) && (cVar2 = FUN_00a39130(&local_2f50), cVar2 != '\0')) {
            bVar1 = true;
            *(undefined2 *)*puVar8 = (undefined2)local_2f50;
          }
          else {
            bVar1 = false;
            *(undefined2 *)*puVar8 = (undefined2)local_2f50;
          }
        }
        uVar7 = uVar7 + 1;
        puVar8 = puVar8 + 0x14;
      } while (bVar1);
      goto LAB_006d7aad;
    }
  }
  if (*(int *)(in_ECX + 0x6c) == 1) {
    *(undefined1 *)(in_ECX + 0x9090) = 1;
    FUN_006d7c70();
    FUN_006d7ce0();
    *(undefined4 *)(in_ECX + 0x807c) = 0x7ffffff;
    if (((param_1 != (undefined4 *)0x0) && (LVar4 = InterlockedDecrement(param_1 + 1), LVar4 == 0))
       && (param_1 != (undefined4 *)0x0)) {
      (**(code **)*param_1)(1);
    }
    __security_check_cookie(local_c ^ (uint)auStack_2f5c);
    return;
  }
LAB_006d7aad:
  if (((param_1 != (undefined4 *)0x0) && (LVar4 = InterlockedDecrement(param_1 + 1), LVar4 == 0)) &&
     (param_1 != (undefined4 *)0x0)) {
    (**(code **)*param_1)(1);
  }
  __security_check_cookie(local_c ^ (uint)auStack_2f5c);
  return;
}

