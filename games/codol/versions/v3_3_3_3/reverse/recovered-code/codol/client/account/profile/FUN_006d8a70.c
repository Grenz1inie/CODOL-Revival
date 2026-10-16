// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 保存前清理无效装备并同步档案
// VA: 0x006d8a70; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006d8a70(int param_1)

{
  char cVar1;
  int iVar2;
  int iVar3;
  undefined4 uVar4;
  uint uVar5;
  undefined4 *puVar6;
  int iVar7;
  undefined *puStack_e0;
  undefined1 *puStack_dc;
  undefined1 *puStack_d8;
  int iStack_d0;
  int iStack_cc;
  int iStack_c8;
  undefined4 uStack_c4;
  int iStack_c0;
  int iStack_bc;
  undefined4 *puStack_b8;
  char cStack_b3;
  char cStack_b2;
  char cStack_b1;
  undefined1 auStack_af [11];
  undefined4 auStack_a4 [7];
  int aiStack_88 [6];
  undefined1 auStack_70 [32];
  undefined1 auStack_50 [32];
  undefined1 auStack_30 [36];
  uint uStack_c;
  
  uStack_c = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  iStack_d0 = param_1;
  cStack_b2 = '\0';
  cStack_b3 = '\0';
  puStack_b8 = (undefined4 *)0x0;
  do {
    puVar6 = puStack_b8;
    func_0x00592d70(&iStack_bc);
    cStack_b1 = '\0';
    if ((iStack_bc != 0) && ((iStack_bc < 1 || (cVar1 = func_0x00695c90(iStack_bc), cVar1 == '\0')))
       ) {
      cStack_b1 = '\x01';
      iStack_bc = 0;
    }
    iVar7 = 0;
    do {
      iVar2 = aiStack_88[iVar7];
      if ((iVar2 != 0) && ((iVar2 < 1 || (cVar1 = func_0x00695c90(iVar2), cVar1 == '\0')))) {
        cStack_b1 = '\x01';
        aiStack_88[iVar7] = 0;
      }
      iVar7 = iVar7 + 1;
    } while (iVar7 < 6);
    if (cStack_b1 != '\0') {
      iVar7 = 0;
      iStack_c0 = 0x10 - (int)auStack_af;
      do {
        if (aiStack_88[iVar7] < 1) {
          auStack_a4[iVar7] = 0;
          auStack_af[iVar7] = 0;
        }
        else {
          auStack_af[iVar7] = 1;
          puVar6 = puStack_b8;
        }
        iVar7 = iVar7 + 1;
      } while (iVar7 < 6);
      func_0x00592b10();
      cStack_b2 = '\x01';
    }
    iStack_cc = (int)puVar6 * 2 + 1;
    func_0x00592d70(&iStack_bc);
    cStack_b1 = '\0';
    if ((iStack_bc != 0) && ((iStack_bc < 1 || (cVar1 = func_0x00695c90(iStack_bc), cVar1 == '\0')))
       ) {
      cStack_b1 = '\x01';
      iStack_bc = 0;
    }
    iVar7 = 0;
    do {
      iVar2 = aiStack_88[iVar7];
      if ((iVar2 != 0) && ((iVar2 < 1 || (cVar1 = func_0x00695c90(iVar2), cVar1 == '\0')))) {
        cStack_b1 = '\x01';
        aiStack_88[iVar7] = 0;
      }
      iVar7 = iVar7 + 1;
    } while (iVar7 < 6);
    if (cStack_b1 != '\0') {
      iVar7 = 0;
      do {
        if (aiStack_88[iVar7] < 1) {
          auStack_a4[iVar7] = 0;
          auStack_af[iVar7] = 0;
        }
        else {
          auStack_af[iVar7] = 1;
          puVar6 = puStack_b8;
        }
        iVar7 = iVar7 + 1;
      } while (iVar7 < 6);
      func_0x00592b10();
      cStack_b2 = '\x01';
    }
    iVar7 = 0;
    do {
      iVar2 = func_0x00593040(puVar6);
      if ((iVar2 != 0) && ((iVar2 < 1 || (cVar1 = func_0x00695c90(iVar2), cVar1 == '\0')))) {
        func_0x00592f50(puVar6,0);
        cStack_b2 = '\x01';
      }
      iVar7 = iVar7 + 1;
    } while (iVar7 < 6);
    iVar7 = 0;
    do {
      iVar2 = func_0x00593040(puVar6);
      if ((iVar2 != 0) && ((iVar2 < 1 || (cVar1 = func_0x00695c90(iVar2), cVar1 == '\0')))) {
        func_0x00592f50(puVar6,0);
        cStack_b2 = '\x01';
      }
      iVar7 = iVar7 + 1;
    } while (iVar7 < 3);
    puStack_b8 = (undefined4 *)0xcdd504;
    do {
      uVar4 = *puStack_b8;
      iStack_c8 = FUN_006da140();
      iStack_c8 = iStack_c8 + 0x90;
      if (iStack_c8 == 0) {
        uStack_c4 = 0;
      }
      else {
        uStack_c4 = 0x7ffc;
        puStack_e0 = &UNK_00c6c218;
        func_0x00637be0(auStack_70,5,&UNK_00c5dde0,puVar6);
        func_0x00637be0(auStack_30,5,&UNK_00c5dde0,0xffffffff);
        func_0x00af70f9(auStack_50,0x20,uVar4);
        puStack_dc = auStack_70;
        puStack_d8 = auStack_50;
        iVar7 = FUN_006da140();
        uVar5 = func_0x00592930(&puStack_e0);
        if (*(char *)(iVar7 + 0x9128) != '\0') {
          uVar5 = *(uint *)(iVar7 + 0x9124) ^ uVar5;
          uVar5 = uVar5 << 8 | uVar5 >> 0x18;
        }
        if (((0 < (int)uVar5) && (iVar7 = uVar5 - 1, iVar7 != 0)) &&
           ((iVar7 < 1 || (cVar1 = func_0x00695c90(iVar7), cVar1 == '\0')))) {
          func_0x00592f50(puVar6,0);
          cStack_b2 = '\x01';
        }
      }
      puStack_b8 = puStack_b8 + 1;
    } while ((int)puStack_b8 < 0xcdd510);
    iVar7 = 0;
    do {
      iVar2 = func_0x00593040(puVar6);
      if ((iVar2 != 0) && ((iVar2 < 1 || (cVar1 = func_0x00695c90(iVar2), cVar1 == '\0')))) {
        func_0x00592f50(puVar6,0);
        cStack_b2 = '\x01';
      }
      iVar7 = iVar7 + 1;
    } while (iVar7 < 3);
    puStack_b8 = (undefined4 *)((int)puVar6 + 1);
  } while ((int)puStack_b8 < 0x3c);
  iVar7 = 0;
  do {
    iVar2 = 0;
    do {
      iVar3 = func_0x00593370(iVar7,iVar2);
      if ((iVar3 != 0) && ((iVar3 < 1 || (cVar1 = func_0x00695c90(iVar3), cVar1 == '\0')))) {
        func_0x00593210(iVar7,iVar2);
        cStack_b3 = '\x01';
      }
      iVar2 = iVar2 + 1;
    } while (iVar2 < 9);
    iVar2 = func_0x00593450(iVar7);
    if ((iVar2 != 0) && ((iVar2 < 1 || (cVar1 = func_0x00695c90(iVar2), cVar1 == '\0')))) {
      func_0x00593500(iVar7);
      cStack_b3 = '\x01';
    }
    iVar7 = iVar7 + 1;
  } while (iVar7 < 0xc);
  uVar4 = func_0x00590940();
  cVar1 = func_0x005908f0(uVar4);
  if (cVar1 == '\0') {
    func_0x00584470();
    func_0x00590a00();
  }
  uVar4 = func_0x00590a80();
  cVar1 = func_0x005908f0(uVar4);
  if (cVar1 == '\0') {
    func_0x00584470();
    func_0x00590b40();
  }
  iVar7 = FUN_006da140();
  uVar5 = func_0x005957b0(&UNK_00c67e7c,0);
  if (*(char *)(iVar7 + 0x9128) != '\0') {
    uVar5 = *(uint *)(iVar7 + 0x9124) ^ uVar5;
    uVar5 = uVar5 << 8 | uVar5 >> 0x18;
  }
  if ((DAT_07817df1 != '\0') && (cVar1 = func_0x005908f0(uVar5), cVar1 == '\0')) {
    uVar5 = 0;
  }
  cVar1 = func_0x005908f0(uVar5);
  if (cVar1 == '\0') {
    if (DAT_07817df1 != '\0') {
      func_0x005908f0(0);
    }
    FUN_006da140();
    func_0x005927e0();
  }
  uVar4 = func_0x00590bc0();
  cVar1 = func_0x005908f0(uVar4);
  if (cVar1 == '\0') {
    func_0x00584470();
    func_0x00590c80();
  }
  uVar4 = func_0x00590d50();
  cVar1 = func_0x005908f0(uVar4);
  if (cVar1 == '\0') {
    func_0x00590de0();
  }
  uVar4 = func_0x00590e30(0);
  cVar1 = func_0x005908f0(uVar4);
  if (cVar1 == '\0') {
    func_0x00590ee0();
  }
  if (cStack_b2 != '\0') {
    func_0x00593b20();
  }
  if (cStack_b3 != '\0') {
    func_0x00593700();
  }
  *(undefined1 *)(iStack_d0 + 0x9118) = 0;
  FUN_006d90c0(iStack_d0);
  func_0x00af6b2f();
  return;
}

