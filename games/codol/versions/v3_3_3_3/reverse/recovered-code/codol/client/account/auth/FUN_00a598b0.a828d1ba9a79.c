// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.auth
// Analyst label: 认证响应与 client_ticket 解码入口
// VA: 0x00a598b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a598b0(undefined4 param_1,int param_2)

{
  bool bVar1;
  char cVar2;
  undefined1 uVar3;
  int iVar4;
  char *pcVar5;
  undefined4 uVar6;
  int *in_ECX;
  int *unaff_FS_OFFSET;
  undefined4 uStack_2d0;
  undefined1 auStack_2cc [20];
  int aiStack_2b8 [8];
  char acStack_298 [208];
  char acStack_1c8 [208];
  undefined1 uStack_f8;
  undefined1 auStack_f7 [203];
  undefined4 uStack_2c;
  undefined4 uStack_28;
  undefined4 uStack_24;
  undefined4 uStack_20;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  uint uStack_14;
  int iStack_10;
  undefined *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &DAT_00b439cb;
  iStack_10 = *unaff_FS_OFFSET;
  uStack_14 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  func_0x00a53d80(uStack_14);
  aiStack_2b8[7] = 700;
  iVar4 = (**(code **)(*(int *)in_ECX[0x54] + 0x30))();
  if (iVar4 != 200) {
    func_0x00a53d80(iVar4);
    aiStack_2b8[7] = func_0x00a680e0(in_ECX[0x54]);
    goto LAB_00a59da0;
  }
  aiStack_2b8[0] = 0;
  aiStack_2b8[1] = 0;
  aiStack_2b8[5] = 0;
  aiStack_2b8[6] = 0;
  aiStack_2b8[3] = 0;
  aiStack_2b8[4] = 0;
  uStack_f8 = 0;
  func_0x00afd440(auStack_f7,0,0xcb);
  func_0x00a801f0();
  uStack_8 = 0;
  cVar2 = func_0x00a80510(in_ECX + 0x57);
  if ((cVar2 == '\0') || (cVar2 = func_0x00a80350(), cVar2 == '\0')) {
    aiStack_2b8[7] = 0x2de;
    uStack_8 = 0xffffffff;
    func_0x00a80210();
    goto LAB_00a59da0;
  }
  cVar2 = func_0x00a80c70(&UNK_00c07d60,aiStack_2b8 + 5);
  if ((cVar2 == '\0') ||
     (cVar2 = (**(code **)(*in_ECX + 0x14))(param_1,0,aiStack_2b8[5],aiStack_2b8[6]), cVar2 == '\0')
     ) {
    func_0x00a53d80(aiStack_2b8[5],aiStack_2b8[6]);
    aiStack_2b8[7] = 0x2df;
    uStack_8 = 0xffffffff;
    func_0x00a80210();
    goto LAB_00a59da0;
  }
  in_ECX[6] = aiStack_2b8[5];
  cVar2 = func_0x00a80c70(&UNK_00c4f3f8,aiStack_2b8 + 3);
  if (cVar2 != '\0') {
    if ((aiStack_2b8[3] != 700) || (aiStack_2b8[4] != 0)) {
      aiStack_2b8[7] = aiStack_2b8[3];
      uVar6 = func_0x00a3c8d0(aiStack_2b8[3]);
      func_0x00a53d80(aiStack_2b8[3],aiStack_2b8[4],uVar6);
      uStack_8 = 0xffffffff;
      func_0x00a80210();
      goto LAB_00a59da0;
    }
    cVar2 = func_0x00a595c0();
    if (cVar2 == '\0') {
      func_0x00a53d80();
      uStack_8 = 0xffffffff;
      func_0x00a80210();
      goto LAB_00a59da0;
    }
    cVar2 = func_0x00a80c70(&UNK_00c07c44,aiStack_2b8);
    acStack_298[0] = '\0';
    func_0x00afd440(acStack_298 + 1,0,0xcc);
    if ((cVar2 == '\0') || (cVar2 = func_0x00a80d00(&UNK_00c07e4c,acStack_298,0xcd), cVar2 == '\0'))
    {
LAB_00a59b02:
      bVar1 = false;
    }
    else {
      pcVar5 = acStack_298;
      bVar1 = true;
      do {
        cVar2 = *pcVar5;
        pcVar5 = pcVar5 + 1;
      } while (cVar2 != '\0');
      iVar4 = FUN_00a36e40(acStack_298,(int)pcVar5 - (int)(acStack_298 + 1),&uStack_f8,param_2);
      if (iVar4 != param_2) {
        func_0x00a53d80(iVar4);
        goto LAB_00a59b02;
      }
    }
    acStack_1c8[0] = '\0';
    func_0x00afd440(acStack_1c8 + 1,0,0xcc);
    if ((bVar1) && (cVar2 = func_0x00a80d00(&UNK_00c07e3c,acStack_1c8,0xcd), cVar2 != '\0')) {
      pcVar5 = acStack_1c8;
      do {
        cVar2 = *pcVar5;
        pcVar5 = pcVar5 + 1;
      } while (cVar2 != '\0');
      iVar4 = FUN_00a36e40(acStack_1c8,(int)pcVar5 - (int)(acStack_1c8 + 1),in_ECX + 0xb,0x80);
      if (iVar4 != 0x80) {
        func_0x00a53d80(iVar4);
        goto LAB_00a59b82;
      }
      cVar2 = (**(code **)(*in_ECX + 0x1c))(auStack_2cc);
      if (cVar2 == '\0') goto LAB_00a59b82;
      bVar1 = true;
    }
    else {
LAB_00a59b82:
      bVar1 = false;
    }
    aiStack_2b8[2] = 0;
    uStack_2d0 = 0;
    if ((bVar1) &&
       (cVar2 = func_0x00a36ea0(&uStack_f8,4,0,&uStack_2d0,aiStack_2b8 + 2), cVar2 != '\0')) {
      bVar1 = true;
    }
    else {
      bVar1 = false;
    }
    if (aiStack_2b8[2] == -0x10425222) {
      if (bVar1) goto LAB_00a59c31;
    }
    else if ((bVar1) &&
            (cVar2 = (**(code **)(*in_ECX + 0x18))(aiStack_2b8[0],&uStack_f8,param_2), cVar2 != '\0'
            )) {
LAB_00a59c31:
      FUN_00a678c0(&uStack_f8);
      if (in_ECX[0x32] == -0x10425222) {
        FUN_00a676f0(&uStack_2c,0);
        FUN_00a678b0(&uStack_2c,1);
        in_ECX[9] = in_ECX[0x34];
        uStack_2c = 0;
        uStack_28 = 0;
        uStack_24 = 0;
        uStack_20 = 0;
        uStack_1c = 0;
        uStack_18 = 0;
        in_ECX[10] = aiStack_2b8[0];
        uVar3 = func_0x00a808f0(&UNK_00b74708);
        *(undefined1 *)(in_ECX + 0x31) = uVar3;
        func_0x00a53d80();
        uStack_8 = 0xffffffff;
        func_0x00a80210();
      }
      else {
        func_0x00a53d80();
        if (((aiStack_2b8[5] == 0xb) && (aiStack_2b8[6] == 0)) ||
           ((aiStack_2b8[5] == 0xd && (aiStack_2b8[6] == 0)))) {
          aiStack_2b8[7] = 0x2cc;
          uStack_8 = 0xffffffff;
          func_0x00a80210();
        }
        else {
          aiStack_2b8[7] = 0x2ec;
          uStack_8 = 0xffffffff;
          func_0x00a80210();
        }
      }
      goto LAB_00a59da0;
    }
  }
  func_0x00a53d80();
  aiStack_2b8[7] = 0x2df;
  uStack_8 = 0xffffffff;
  func_0x00a80210();
LAB_00a59da0:
  *unaff_FS_OFFSET = iStack_10;
  func_0x00af6b2f();
  return;
}

