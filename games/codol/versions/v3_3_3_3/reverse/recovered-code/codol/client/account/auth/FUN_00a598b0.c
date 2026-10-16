// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.auth
// Analyst label: 认证响应与 client_ticket 解码入口
// VA: 0x00a598b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_806f8b8a073991ad1b8b2ed6e34540407266a15ab204346b21850a5fbc77728d
// BEGIN PSEUDOCODE

void FUN_00a598b0(undefined4 param_1,int param_2)

{
  bool bVar1;
  char cVar2;
  undefined1 uVar3;
  int iVar4;
  char *pcVar5;
  undefined4 uVar6;
  int *in_ECX;
  undefined4 local_2d0;
  undefined1 local_2cc [20];
  int local_2b8 [8];
  char local_298 [208];
  char local_1c8 [208];
  undefined1 local_f8;
  undefined1 local_f7 [203];
  undefined4 local_2c;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  uint local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_00b439cb;
  local_10 = ExceptionList;
  local_14 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  FUN_00a53d80(local_14);
  local_2b8[7] = 700;
  iVar4 = (**(code **)(*(int *)in_ECX[0x54] + 0x30))();
  if (iVar4 != 200) {
    FUN_00a53d80(iVar4);
    local_2b8[7] = FUN_00a680e0(in_ECX[0x54]);
    goto LAB_00a59da0;
  }
  local_2b8[0] = 0;
  local_2b8[1] = 0;
  local_2b8[5] = 0;
  local_2b8[6] = 0;
  local_2b8[3] = 0;
  local_2b8[4] = 0;
  local_f8 = 0;
  _memset(local_f7,0,0xcb);
  FUN_00a801f0();
  local_8 = 0;
  cVar2 = FUN_00a80510(in_ECX + 0x57);
  if ((cVar2 == '\0') || (cVar2 = FUN_00a80350(), cVar2 == '\0')) {
    local_2b8[7] = 0x2de;
    local_8 = 0xffffffff;
    FUN_00a80210();
    goto LAB_00a59da0;
  }
  cVar2 = FUN_00a80c70("auth_task",local_2b8 + 5);
  if ((cVar2 == '\0') ||
     (cVar2 = (**(code **)(*in_ECX + 0x14))(param_1,0,local_2b8[5],local_2b8[6]), cVar2 == '\0')) {
    FUN_00a53d80(local_2b8[5],local_2b8[6]);
    local_2b8[7] = 0x2df;
    local_8 = 0xffffffff;
    FUN_00a80210();
    goto LAB_00a59da0;
  }
  in_ECX[6] = local_2b8[5];
  cVar2 = FUN_00a80c70(&DAT_00c4f3f8,local_2b8 + 3);
  if (cVar2 != '\0') {
    if ((local_2b8[3] != 700) || (local_2b8[4] != 0)) {
      local_2b8[7] = local_2b8[3];
      uVar6 = FUN_00a3c8d0(local_2b8[3]);
      FUN_00a53d80(local_2b8[3],local_2b8[4],uVar6);
      local_8 = 0xffffffff;
      FUN_00a80210();
      goto LAB_00a59da0;
    }
    cVar2 = FUN_00a595c0();
    if (cVar2 == '\0') {
      FUN_00a53d80();
      local_8 = 0xffffffff;
      FUN_00a80210();
      goto LAB_00a59da0;
    }
    cVar2 = FUN_00a80c70("iv_seed",local_2b8);
    local_298[0] = '\0';
    _memset(local_298 + 1,0,0xcc);
    if ((cVar2 == '\0') || (cVar2 = FUN_00a80d00("client_ticket",local_298,0xcd), cVar2 == '\0')) {
LAB_00a59b02:
      bVar1 = false;
    }
    else {
      pcVar5 = local_298;
      bVar1 = true;
      do {
        cVar2 = *pcVar5;
        pcVar5 = pcVar5 + 1;
      } while (cVar2 != '\0');
      iVar4 = FUN_00a36e40(local_298,(int)pcVar5 - (int)(local_298 + 1),&local_f8,param_2);
      if (iVar4 != param_2) {
        FUN_00a53d80(iVar4);
        goto LAB_00a59b02;
      }
    }
    local_1c8[0] = '\0';
    _memset(local_1c8 + 1,0,0xcc);
    if ((bVar1) && (cVar2 = FUN_00a80d00("server_ticket",local_1c8,0xcd), cVar2 != '\0')) {
      pcVar5 = local_1c8;
      do {
        cVar2 = *pcVar5;
        pcVar5 = pcVar5 + 1;
      } while (cVar2 != '\0');
      iVar4 = FUN_00a36e40(local_1c8,(int)pcVar5 - (int)(local_1c8 + 1),in_ECX + 0xb,0x80);
      if (iVar4 != 0x80) {
        FUN_00a53d80(iVar4);
        goto LAB_00a59b82;
      }
      cVar2 = (**(code **)(*in_ECX + 0x1c))(local_2cc);
      if (cVar2 == '\0') goto LAB_00a59b82;
      bVar1 = true;
    }
    else {
LAB_00a59b82:
      bVar1 = false;
    }
    local_2b8[2] = 0;
    local_2d0 = 0;
    if ((bVar1) && (cVar2 = FUN_00a36ea0(&local_f8,4,0,&local_2d0,local_2b8 + 2), cVar2 != '\0')) {
      bVar1 = true;
    }
    else {
      bVar1 = false;
    }
    if (local_2b8[2] == -0x10425222) {
      if (bVar1) goto LAB_00a59c31;
    }
    else if ((bVar1) &&
            (cVar2 = (**(code **)(*in_ECX + 0x18))(local_2b8[0],&local_f8,param_2), cVar2 != '\0'))
    {
LAB_00a59c31:
      FUN_00a678c0(&local_f8);
      if (in_ECX[0x32] == -0x10425222) {
        FUN_00a676f0(&local_2c,0);
        FUN_00a678b0(&local_2c,1);
        in_ECX[9] = in_ECX[0x34];
        local_2c = 0;
        local_28 = 0;
        local_24 = 0;
        local_20 = 0;
        local_1c = 0;
        local_18 = 0;
        in_ECX[10] = local_2b8[0];
        uVar3 = FUN_00a808f0("identity");
        *(undefined1 *)(in_ECX + 0x31) = uVar3;
        FUN_00a53d80();
        local_8 = 0xffffffff;
        FUN_00a80210();
      }
      else {
        FUN_00a53d80();
        if (((local_2b8[5] == 0xb) && (local_2b8[6] == 0)) ||
           ((local_2b8[5] == 0xd && (local_2b8[6] == 0)))) {
          local_2b8[7] = 0x2cc;
          local_8 = 0xffffffff;
          FUN_00a80210();
        }
        else {
          local_2b8[7] = 0x2ec;
          local_8 = 0xffffffff;
          FUN_00a80210();
        }
      }
      goto LAB_00a59da0;
    }
  }
  FUN_00a53d80();
  local_2b8[7] = 0x2df;
  local_8 = 0xffffffff;
  FUN_00a80210();
LAB_00a59da0:
  ExceptionList = local_10;
  __security_check_cookie(local_14 ^ (uint)&stack0xfffffffc);
  return;
}

