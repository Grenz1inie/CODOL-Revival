// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.connection
// Analyst label: 协议 210 握手 transcript 与密钥派生
// VA: 0x00a61980; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a61980(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  bool bVar1;
  char cVar2;
  uint uVar3;
  undefined4 *puVar4;
  int *piVar5;
  undefined4 *puVar6;
  undefined4 uVar7;
  int iVar8;
  int in_ECX;
  int *unaff_FS_OFFSET;
  undefined4 uStack_194;
  int iStack_190;
  undefined4 uStack_18c;
  undefined4 uStack_188;
  undefined4 *puStack_184;
  undefined4 *puStack_180;
  undefined4 uStack_17c;
  char acStack_176 [202];
  undefined1 auStack_ac [20];
  undefined1 auStack_98 [20];
  undefined1 auStack_84 [16];
  undefined1 auStack_74 [16];
  undefined1 auStack_64 [20];
  undefined1 auStack_50 [20];
  undefined1 auStack_3c [8];
  undefined4 uStack_34;
  undefined4 uStack_30;
  undefined4 uStack_2c;
  undefined4 uStack_28;
  undefined4 uStack_24;
  undefined4 uStack_20;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  uint uStack_14;
  int iStack_10;
  undefined *puStack_c;
  uint uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &DAT_00b445b9;
  iStack_10 = *unaff_FS_OFFSET;
  uVar3 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  uStack_18c = param_2;
  uStack_14 = uVar3;
  cVar2 = func_0x00a3a9d0(param_1,param_3,param_2,&uStack_18c,&puStack_180,4,uVar3);
  if ((cVar2 != '\0') &&
     (cVar2 = func_0x00a3a9d0(param_1,param_3,uStack_18c,&uStack_18c,&uStack_194,8,uVar3),
     cVar2 != '\0')) {
    *(undefined4 *)(in_ECX + 0x630) = uStack_194;
    *(int *)(in_ECX + 0x634) = iStack_190;
    cVar2 = func_0x00a3a9d0(param_1,param_3,uStack_18c,&uStack_18c,in_ECX + 0x5ec,8,uVar3);
    puVar4 = puStack_180;
    if (cVar2 != '\0') {
      if (puStack_180 != (undefined4 *)0xd2) {
        func_0x00a53d80();
        func_0x00a53d80(puVar4,0xd2);
        func_0x00a53d80();
        func_0x00596bf0(7);
        FUN_00a613c0();
        goto LAB_00a621f7;
      }
      uStack_8 = 0;
      acStack_176[0] = '\a';
      iStack_190 = func_0x00a38020(0x24);
      uStack_8._0_1_ = 1;
      if (iStack_190 == 0) {
        puVar4 = (undefined4 *)0x0;
      }
      else {
        puVar4 = (undefined4 *)func_0x00a3a130(acStack_176,8,1);
      }
      uStack_8 = (uint)uStack_8._1_3_ << 8;
      if (puVar4 != (undefined4 *)0x0) {
        InterlockedIncrement(puVar4 + 1);
      }
      func_0x00a39a50(0);
      func_0x00a3a2a0(1);
      acStack_176[1] = 0xff;
      func_0x00a39f50(acStack_176 + 1,1);
      func_0x00a39a50(1);
      puVar6 = *(undefined4 **)(in_ECX + 0x534);
      func_0x00a3a2a0(8);
      puStack_180 = puVar6;
      func_0x00a39f50(&puStack_180,0x20);
      puVar6 = *(undefined4 **)(in_ECX + 0x538);
      func_0x00a3a2a0(8);
      puStack_180 = puVar6;
      func_0x00a39f50(&puStack_180,0x20);
      func_0x00a39f50(in_ECX + 0x53c,0x400);
      puStack_180 = (undefined4 *)(puVar4[4] + 10);
      uStack_17c = 0;
      puStack_184 = (undefined4 *)0xd2;
      cVar2 = func_0x00a3a960(acStack_176 + 2,200,0,&uStack_17c,&puStack_184,4);
      if (cVar2 == '\0') {
LAB_00a61e88:
        bVar1 = false;
      }
      else {
        puStack_184 = (undefined4 *)0xd2;
        cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,&puStack_184,4);
        if (cVar2 == '\0') goto LAB_00a61e88;
        puStack_184 = (undefined4 *)func_0x007276b0();
        cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,&puStack_184,4);
        if ((cVar2 == '\0') ||
           (cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,in_ECX + 0x5e4,8),
           cVar2 == '\0')) goto LAB_00a61e88;
        puStack_184 = *(undefined4 **)(in_ECX + 0xac);
        cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,&puStack_184,4);
        if (cVar2 == '\0') goto LAB_00a61e88;
        acStack_176[1] = 0xab;
        cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,acStack_176 + 1,1);
        if (cVar2 == '\0') goto LAB_00a61e88;
        acStack_176[1] = 0x81;
        cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,acStack_176 + 1,1);
        if (cVar2 == '\0') goto LAB_00a61e88;
        puStack_184 = (undefined4 *)0xd2;
        cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,&puStack_184,4);
        if (cVar2 == '\0') goto LAB_00a61e88;
        uStack_188 = *(undefined4 *)(in_ECX + 0x630);
        puStack_184 = *(undefined4 **)(in_ECX + 0x634);
        cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,&uStack_188,8);
        if ((cVar2 == '\0') ||
           (cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,in_ECX + 0x5ec,8),
           cVar2 == '\0')) goto LAB_00a61e88;
        puStack_184 = puStack_180;
        cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,&puStack_184,4);
        if (cVar2 == '\0') goto LAB_00a61e88;
        acStack_176[1] = 0xab;
        cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,acStack_176 + 1,1);
        if (cVar2 == '\0') goto LAB_00a61e88;
        acStack_176[1] = 0x82;
        cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,acStack_176 + 1,1);
        if ((cVar2 == '\0') ||
           (cVar2 = func_0x00a3a960(acStack_176 + 2,200,uStack_17c,&uStack_17c,puVar4[2],puVar4[4]),
           cVar2 == '\0')) goto LAB_00a61e88;
        bVar1 = true;
      }
      func_0x00b2ced0();
      uStack_8 = CONCAT31(uStack_8._1_3_,2);
      iStack_190 = 0x14;
      if ((bVar1) &&
         (cVar2 = func_0x00b2cf50(acStack_176 + 2,uStack_17c,auStack_64,&iStack_190), cVar2 != '\0')
         ) {
        bVar1 = true;
      }
      else {
        bVar1 = false;
      }
      func_0x00a5f5f0(&uStack_2c,0);
      if ((bVar1) && (cVar2 = FUN_00a5fb90(auStack_64,&uStack_2c,0x18,auStack_50), cVar2 != '\0')) {
        bVar1 = true;
      }
      else {
        bVar1 = false;
      }
      uStack_2c = 0;
      uStack_28 = 0;
      uStack_24 = 0;
      uStack_20 = 0;
      uStack_1c = 0;
      uStack_18 = 0;
      uStack_8 = uStack_8 & 0xffffff00;
      func_0x00b2cf40();
      if ((bVar1) &&
         (cVar2 = FUN_00a60120(auStack_50,0x14,&UNK_00c08030,10,auStack_3c,0x10), cVar2 != '\0')) {
        bVar1 = true;
      }
      else {
        bVar1 = false;
      }
      *(undefined4 *)(in_ECX + 0x5f4) = uStack_34;
      *(undefined4 *)(in_ECX + 0x5f8) = uStack_30;
      if ((bVar1) &&
         (cVar2 = FUN_00a60120(auStack_50,0x14,&UNK_00c08028,6,auStack_ac,0x48), cVar2 != '\0')) {
        func_0x00a5f2c0(auStack_ac,1);
        func_0x00a5f140(auStack_98,1);
        if (*(undefined4 **)(in_ECX + 0x5fc) != (undefined4 *)0x0) {
          (**(code **)**(undefined4 **)(in_ECX + 0x5fc))(1);
          *(undefined4 *)(in_ECX + 0x5fc) = 0;
        }
        iStack_190 = func_0x00a38020(0x394);
        uStack_8._0_1_ = 3;
        if (iStack_190 == 0) {
          piVar5 = (int *)0x0;
        }
        else {
          piVar5 = (int *)func_0x00b2cc90();
        }
        *(int **)(in_ECX + 0x5fc) = piVar5;
        uStack_8 = (uint)uStack_8._1_3_ << 8;
        cVar2 = (**(code **)(*piVar5 + 4))(auStack_84,0x10);
        if (*(undefined4 **)(in_ECX + 0x600) != (undefined4 *)0x0) {
          (**(code **)**(undefined4 **)(in_ECX + 0x600))(1);
          *(undefined4 *)(in_ECX + 0x600) = 0;
        }
        iStack_190 = func_0x00a38020(0x394);
        uStack_8._0_1_ = 4;
        if (iStack_190 == 0) {
          piVar5 = (int *)0x0;
        }
        else {
          piVar5 = (int *)func_0x00b2cc90();
        }
        uStack_8 = (uint)uStack_8._1_3_ << 8;
        *(int **)(in_ECX + 0x600) = piVar5;
        if ((cVar2 == '\0') || (cVar2 = (**(code **)(*piVar5 + 4))(auStack_74,0x10), cVar2 == '\0'))
        goto LAB_00a62078;
        bVar1 = true;
      }
      else {
LAB_00a62078:
        bVar1 = false;
      }
      func_0x00afd440(auStack_ac,0,0x48);
      if (bVar1) {
        iStack_190 = func_0x00a38020(0x1c);
        uStack_8 = CONCAT31(uStack_8._1_3_,5);
        if (iStack_190 == 0) {
          puVar6 = (undefined4 *)0x0;
        }
        else {
          puVar6 = (undefined4 *)func_0x004a80d0((int)puStack_180 + 6,0);
        }
        puStack_184 = puVar6;
        if (puVar6 != (undefined4 *)0x0) {
          InterlockedIncrement(puVar6 + 1);
        }
        uStack_8 = CONCAT31(uStack_8._1_3_,6);
        cVar2 = func_0x00a38f30(puStack_180);
        if ((((cVar2 == '\0') || (cVar2 = func_0x00a38ea0(0xab), cVar2 == '\0')) ||
            (cVar2 = func_0x00a38ea0(0x82), cVar2 == '\0')) ||
           (cVar2 = func_0x00a38680(puVar4[2],puVar4[4]), cVar2 == '\0')) {
LAB_00a6213b:
          acStack_176[0] = '\0';
        }
        else {
          cVar2 = func_0x00a38680(auStack_3c,8);
          acStack_176[0] = '\x01';
          if (cVar2 == '\0') goto LAB_00a6213b;
        }
        func_0x00a38660();
        if (acStack_176[0] == '\0') {
          func_0x00a53d80();
          func_0x00596bf0(5);
          FUN_00a613c0();
        }
        else {
          iStack_190 = puVar6[3];
          uVar7 = func_0x00a38660();
          FUN_00a60fd0(iStack_190,uVar7);
          *(undefined4 *)(in_ECX + 0x5d8) = 2;
        }
        uStack_8 = uStack_8 & 0xffffff00;
        if ((puVar6 != (undefined4 *)0x0) && (iVar8 = InterlockedDecrement(puVar6 + 1), iVar8 == 0))
        {
          (**(code **)*puVar6)(1);
        }
      }
      else {
        func_0x00a53d80();
        func_0x00596bf0(6);
        acStack_176[0] = '\0';
        FUN_00a613c0();
      }
      uStack_8 = 0xffffffff;
      iVar8 = InterlockedDecrement(puVar4 + 1);
      if (iVar8 == 0) {
        (**(code **)*puVar4)(1);
      }
      goto LAB_00a621f7;
    }
  }
  func_0x00a53d80();
  func_0x00596bf0(0x1f);
  FUN_00a613c0();
LAB_00a621f7:
  *unaff_FS_OFFSET = iStack_10;
  func_0x00af6b2f();
  return;
}

