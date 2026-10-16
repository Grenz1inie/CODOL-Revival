// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.connection
// Analyst label: 协议 210 握手 transcript 与密钥派生
// VA: 0x00a61980; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_88a82b73182cc47932137af41a0471451f32e98cb986bebdcb5fa10822f80bb1
// BEGIN PSEUDOCODE

void FUN_00a61980(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  bool bVar1;
  char cVar2;
  uint uVar3;
  undefined4 *puVar4;
  int *piVar5;
  undefined4 *puVar6;
  undefined4 uVar7;
  LONG LVar8;
  int in_ECX;
  undefined4 local_194;
  int local_190;
  undefined4 local_18c;
  undefined4 local_188;
  undefined4 *local_184;
  undefined4 *local_180;
  undefined4 local_17c;
  char local_176 [202];
  undefined1 local_ac [20];
  undefined1 local_98 [20];
  undefined1 local_84 [16];
  undefined1 local_74 [16];
  undefined1 local_64 [20];
  undefined1 local_50 [20];
  undefined1 local_3c [8];
  undefined4 local_34;
  undefined4 local_30;
  undefined4 local_2c;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  uint local_14;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_00b445b9;
  local_10 = ExceptionList;
  uVar3 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_18c = param_2;
  local_14 = uVar3;
  cVar2 = FUN_00a3a9d0(param_1,param_3,param_2,&local_18c,&local_180,4,uVar3);
  if ((cVar2 != '\0') &&
     (cVar2 = FUN_00a3a9d0(param_1,param_3,local_18c,&local_18c,&local_194,8,uVar3), cVar2 != '\0'))
  {
    *(undefined4 *)(in_ECX + 0x630) = local_194;
    *(int *)(in_ECX + 0x634) = local_190;
    cVar2 = FUN_00a3a9d0(param_1,param_3,local_18c,&local_18c,in_ECX + 0x5ec,8,uVar3);
    puVar4 = local_180;
    if (cVar2 != '\0') {
      if (local_180 != (undefined4 *)0xd2) {
        FUN_00a53d80();
        FUN_00a53d80(puVar4,0xd2);
        FUN_00a53d80();
        FUN_00596bf0(7);
        FUN_00a613c0();
        goto LAB_00a621f7;
      }
      local_8 = 0;
      local_176[0] = '\a';
      local_190 = FUN_00a38020(0x24);
      local_8._0_1_ = 1;
      if (local_190 == 0) {
        puVar4 = (undefined4 *)0x0;
      }
      else {
        puVar4 = (undefined4 *)FUN_00a3a130(local_176,8,1);
      }
      local_8 = (uint)local_8._1_3_ << 8;
      if (puVar4 != (undefined4 *)0x0) {
        InterlockedIncrement(puVar4 + 1);
      }
      FUN_00a39a50(0);
      FUN_00a3a2a0(1);
      local_176[1] = 0xff;
      FUN_00a39f50(local_176 + 1,1);
      FUN_00a39a50(1);
      puVar6 = *(undefined4 **)(in_ECX + 0x534);
      FUN_00a3a2a0(8);
      local_180 = puVar6;
      FUN_00a39f50(&local_180,0x20);
      puVar6 = *(undefined4 **)(in_ECX + 0x538);
      FUN_00a3a2a0(8);
      local_180 = puVar6;
      FUN_00a39f50(&local_180,0x20);
      FUN_00a39f50(in_ECX + 0x53c,0x400);
      local_180 = (undefined4 *)(puVar4[4] + 10);
      local_17c = 0;
      local_184 = (undefined4 *)0xd2;
      cVar2 = FUN_00a3a960(local_176 + 2,200,0,&local_17c,&local_184,4);
      if (cVar2 == '\0') {
LAB_00a61e88:
        bVar1 = false;
      }
      else {
        local_184 = (undefined4 *)0xd2;
        cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,&local_184,4);
        if (cVar2 == '\0') goto LAB_00a61e88;
        local_184 = (undefined4 *)FUN_007276b0();
        cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,&local_184,4);
        if ((cVar2 == '\0') ||
           (cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,in_ECX + 0x5e4,8),
           cVar2 == '\0')) goto LAB_00a61e88;
        local_184 = *(undefined4 **)(in_ECX + 0xac);
        cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,&local_184,4);
        if (cVar2 == '\0') goto LAB_00a61e88;
        local_176[1] = 0xab;
        cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,local_176 + 1,1);
        if (cVar2 == '\0') goto LAB_00a61e88;
        local_176[1] = 0x81;
        cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,local_176 + 1,1);
        if (cVar2 == '\0') goto LAB_00a61e88;
        local_184 = (undefined4 *)0xd2;
        cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,&local_184,4);
        if (cVar2 == '\0') goto LAB_00a61e88;
        local_188 = *(undefined4 *)(in_ECX + 0x630);
        local_184 = *(undefined4 **)(in_ECX + 0x634);
        cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,&local_188,8);
        if ((cVar2 == '\0') ||
           (cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,in_ECX + 0x5ec,8),
           cVar2 == '\0')) goto LAB_00a61e88;
        local_184 = local_180;
        cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,&local_184,4);
        if (cVar2 == '\0') goto LAB_00a61e88;
        local_176[1] = 0xab;
        cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,local_176 + 1,1);
        if (cVar2 == '\0') goto LAB_00a61e88;
        local_176[1] = 0x82;
        cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,local_176 + 1,1);
        if ((cVar2 == '\0') ||
           (cVar2 = FUN_00a3a960(local_176 + 2,200,local_17c,&local_17c,puVar4[2],puVar4[4]),
           cVar2 == '\0')) goto LAB_00a61e88;
        bVar1 = true;
      }
      FUN_00b2ced0();
      local_8 = CONCAT31(local_8._1_3_,2);
      local_190 = 0x14;
      if ((bVar1) &&
         (cVar2 = FUN_00b2cf50(local_176 + 2,local_17c,local_64,&local_190), cVar2 != '\0')) {
        bVar1 = true;
      }
      else {
        bVar1 = false;
      }
      FUN_00a5f5f0(&local_2c,0);
      if ((bVar1) && (cVar2 = FUN_00a5fb90(local_64,&local_2c,0x18,local_50), cVar2 != '\0')) {
        bVar1 = true;
      }
      else {
        bVar1 = false;
      }
      local_2c = 0;
      local_28 = 0;
      local_24 = 0;
      local_20 = 0;
      local_1c = 0;
      local_18 = 0;
      local_8 = local_8 & 0xffffff00;
      FUN_00b2cf40();
      if ((bVar1) &&
         (cVar2 = FUN_00a60120(local_50,0x14,"CLIENTCHAL",10,local_3c,0x10), cVar2 != '\0')) {
        bVar1 = true;
      }
      else {
        bVar1 = false;
      }
      *(undefined4 *)(in_ECX + 0x5f4) = local_34;
      *(undefined4 *)(in_ECX + 0x5f8) = local_30;
      if ((bVar1) && (cVar2 = FUN_00a60120(local_50,0x14,"BDDATA",6,local_ac,0x48), cVar2 != '\0'))
      {
        FUN_00a5f2c0(local_ac,1);
        FUN_00a5f140(local_98,1);
        if (*(undefined4 **)(in_ECX + 0x5fc) != (undefined4 *)0x0) {
          (**(code **)**(undefined4 **)(in_ECX + 0x5fc))(1);
          *(undefined4 *)(in_ECX + 0x5fc) = 0;
        }
        local_190 = FUN_00a38020(0x394);
        local_8._0_1_ = 3;
        if (local_190 == 0) {
          piVar5 = (int *)0x0;
        }
        else {
          piVar5 = (int *)FUN_00b2cc90();
        }
        *(int **)(in_ECX + 0x5fc) = piVar5;
        local_8 = (uint)local_8._1_3_ << 8;
        cVar2 = (**(code **)(*piVar5 + 4))(local_84,0x10);
        if (*(undefined4 **)(in_ECX + 0x600) != (undefined4 *)0x0) {
          (**(code **)**(undefined4 **)(in_ECX + 0x600))(1);
          *(undefined4 *)(in_ECX + 0x600) = 0;
        }
        local_190 = FUN_00a38020(0x394);
        local_8._0_1_ = 4;
        if (local_190 == 0) {
          piVar5 = (int *)0x0;
        }
        else {
          piVar5 = (int *)FUN_00b2cc90();
        }
        local_8 = (uint)local_8._1_3_ << 8;
        *(int **)(in_ECX + 0x600) = piVar5;
        if ((cVar2 == '\0') || (cVar2 = (**(code **)(*piVar5 + 4))(local_74,0x10), cVar2 == '\0'))
        goto LAB_00a62078;
        bVar1 = true;
      }
      else {
LAB_00a62078:
        bVar1 = false;
      }
      _memset(local_ac,0,0x48);
      if (bVar1) {
        local_190 = FUN_00a38020(0x1c);
        local_8 = CONCAT31(local_8._1_3_,5);
        if (local_190 == 0) {
          puVar6 = (undefined4 *)0x0;
        }
        else {
          puVar6 = (undefined4 *)FUN_004a80d0((int)local_180 + 6,0);
        }
        local_184 = puVar6;
        if (puVar6 != (undefined4 *)0x0) {
          InterlockedIncrement(puVar6 + 1);
        }
        local_8 = CONCAT31(local_8._1_3_,6);
        cVar2 = FUN_00a38f30(local_180);
        if ((((cVar2 == '\0') || (cVar2 = FUN_00a38ea0(0xab), cVar2 == '\0')) ||
            (cVar2 = FUN_00a38ea0(0x82), cVar2 == '\0')) ||
           (cVar2 = FUN_00a38680(puVar4[2],puVar4[4]), cVar2 == '\0')) {
LAB_00a6213b:
          local_176[0] = '\0';
        }
        else {
          cVar2 = FUN_00a38680(local_3c,8);
          local_176[0] = '\x01';
          if (cVar2 == '\0') goto LAB_00a6213b;
        }
        FUN_00a38660();
        if (local_176[0] == '\0') {
          FUN_00a53d80();
          FUN_00596bf0(5);
          FUN_00a613c0();
        }
        else {
          local_190 = puVar6[3];
          uVar7 = FUN_00a38660();
          FUN_00a60fd0(local_190,uVar7);
          *(undefined4 *)(in_ECX + 0x5d8) = 2;
        }
        local_8 = local_8 & 0xffffff00;
        if ((puVar6 != (undefined4 *)0x0) && (LVar8 = InterlockedDecrement(puVar6 + 1), LVar8 == 0))
        {
          (**(code **)*puVar6)(1);
        }
      }
      else {
        FUN_00a53d80();
        FUN_00596bf0(6);
        local_176[0] = '\0';
        FUN_00a613c0();
      }
      local_8 = 0xffffffff;
      LVar8 = InterlockedDecrement(puVar4 + 1);
      if (LVar8 == 0) {
        (**(code **)*puVar4)(1);
      }
      goto LAB_00a621f7;
    }
  }
  FUN_00a53d80();
  FUN_00596bf0(0x1f);
  FUN_00a613c0();
LAB_00a621f7:
  ExceptionList = local_10;
  __security_check_cookie(local_14 ^ (uint)&stack0xfffffffc);
  return;
}

