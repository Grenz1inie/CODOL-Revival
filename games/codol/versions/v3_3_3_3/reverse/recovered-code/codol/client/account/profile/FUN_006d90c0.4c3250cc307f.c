// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 装备与名片缓存回写档案
// VA: 0x006d90c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006d90c0(undefined *param_1)

{
  undefined *puVar1;
  char cVar2;
  uint uVar3;
  undefined *puVar4;
  ushort *puVar5;
  ushort uVar6;
  uint *puVar7;
  int iVar8;
  bool bVar9;
  uint uStack_9c;
  undefined *puStack_98;
  undefined1 *puStack_94;
  undefined *puStack_90;
  undefined1 *puStack_8c;
  char cStack_81;
  undefined *puStack_80;
  undefined1 *puStack_7c;
  undefined *puStack_74;
  undefined1 *puStack_70;
  undefined *puStack_6c;
  undefined *puStack_68;
  undefined1 *puStack_64;
  undefined *puStack_60;
  undefined1 *puStack_5c;
  undefined *puStack_58;
  undefined1 auStack_4c [32];
  undefined1 auStack_2c [32];
  uint uStack_c;
  
  uStack_c = _DAT_00cc7c80 ^ (uint)&uStack_9c;
  puStack_68 = param_1;
  iVar8 = 0;
  do {
    func_0x00592b10();
    iVar8 = iVar8 + 1;
  } while (iVar8 < 0x78);
  puStack_90 = (undefined *)0x0;
  uStack_9c = 0x2e16e54;
  do {
    iVar8 = 0;
    do {
      puVar4 = puStack_90;
      func_0x00593210(puStack_90,iVar8);
      uVar3 = uStack_9c;
      iVar8 = iVar8 + 1;
    } while (iVar8 < 9);
    func_0x00593500(puVar4);
    uStack_9c = uVar3 + 0x4c;
    puStack_90 = puVar4 + 1;
  } while ((int)uStack_9c < 0x2e171e4);
  uStack_9c = 0;
  puStack_90 = (undefined *)0x2e88f1c;
  do {
    iVar8 = 0;
    puVar7 = (uint *)(puStack_90 + 0x24);
    do {
      if (puStack_90[iVar8 + 0x10] == '\0') {
        uVar3 = 0;
      }
      else {
        uVar3 = (_DAT_00cdd280 >> (0x10U - (char)iVar8 & 0x1f) |
                _DAT_00cdd280 << ((char)iVar8 + 0x10U & 0x1f)) ^ *puVar7;
        uVar3 = uVar3 << 8 | uVar3 >> 0x18;
      }
      func_0x00592f50(uStack_9c,uVar3);
      iVar8 = iVar8 + 1;
      puVar7 = puVar7 + 1;
    } while (iVar8 < 6);
    iVar8 = 0;
    puVar7 = (uint *)(puStack_90 + 0x48);
    do {
      if (puStack_90[iVar8 + 0x19] == '\0') {
        uVar3 = 0;
      }
      else {
        uVar3 = (_DAT_00cdd280 >> (0x10U - (char)iVar8 & 0x1f) |
                _DAT_00cdd280 << ((char)iVar8 + 0x10U & 0x1f)) ^ *puVar7;
        uVar3 = uVar3 << 8 | uVar3 >> 0x18;
      }
      func_0x00592f50(uStack_9c,uVar3);
      iVar8 = iVar8 + 1;
      puVar7 = puVar7 + 1;
    } while (iVar8 < 3);
    iVar8 = 0;
    puVar7 = (uint *)(puStack_90 + 0x54);
    do {
      if (puStack_90[iVar8 + 0x1c] == '\0') {
        uVar3 = 0;
      }
      else {
        uVar3 = (_DAT_00cdd280 >> (0x10U - (char)iVar8 & 0x1f) |
                _DAT_00cdd280 << ((char)iVar8 + 0x10U & 0x1f)) ^ *puVar7;
        uVar3 = uVar3 << 8 | uVar3 >> 0x18;
      }
      func_0x00592f50(uStack_9c,uVar3);
      iVar8 = iVar8 + 1;
      puVar7 = puVar7 + 1;
    } while (iVar8 < 3);
    iVar8 = 0;
    puVar7 = (uint *)(puStack_90 + 0x3c);
    do {
      if (puStack_90[iVar8 + 0x16] == '\0') {
        uVar3 = 0;
      }
      else {
        uVar3 = (_DAT_00cdd280 >> (0x10U - (char)iVar8 & 0x1f) |
                _DAT_00cdd280 << ((char)iVar8 + 0x10U & 0x1f)) ^ *puVar7;
        uVar3 = uVar3 << 8 | uVar3 >> 0x18;
      }
      func_0x00592f50(uStack_9c,uVar3);
      puVar4 = puStack_90;
      iVar8 = iVar8 + 1;
      puVar7 = puVar7 + 1;
    } while (iVar8 < 3);
    if (puStack_90[0x1f] == '\0') {
      uVar3 = 0;
    }
    else {
      uVar3 = (*(uint *)(puStack_90 + 0x60) ^ _DAT_00cdd280) << 8 |
              (*(uint *)(puStack_90 + 0x60) ^ _DAT_00cdd280) >> 0x18;
    }
    iVar8 = FUN_006da140();
    puStack_98 = (undefined *)(iVar8 + 0x90);
    if (puStack_98 == (undefined *)0x0) {
      puStack_98 = (undefined *)0x0;
      puStack_94 = (undefined1 *)0x0;
    }
    else {
      puStack_94 = (undefined1 *)0x7ffc;
      puStack_74 = &UNK_00c6c218;
      func_0x00637be0(auStack_2c,0x20,&UNK_00c5dde0,uStack_9c);
      puStack_70 = auStack_2c;
      puStack_6c = &UNK_00c6c23c;
      func_0x00637be0(auStack_4c,0x20,&UNK_00c5dde0,uVar3 != 0);
      func_0x005926d0(&puStack_74,auStack_4c,&puStack_98,0,0);
    }
    if (puVar4[0x20] == '\0') {
      uVar3 = 0;
    }
    else {
      uVar3 = (*(uint *)(puVar4 + 100) ^ _DAT_00cdd280) << 8 |
              (*(uint *)(puVar4 + 100) ^ _DAT_00cdd280) >> 0x18;
    }
    iVar8 = FUN_006da140();
    puStack_80 = (undefined *)(iVar8 + 0x90);
    if (puStack_80 == (undefined *)0x0) {
      puStack_80 = (undefined *)0x0;
      puStack_7c = (undefined1 *)0x0;
    }
    else {
      puStack_7c = (undefined1 *)0x7ffc;
      puStack_60 = &UNK_00c6c218;
      func_0x00637be0(auStack_4c,0x20,&UNK_00c5dde0,uStack_9c);
      puStack_5c = auStack_4c;
      puStack_58 = &UNK_00c6c250;
      func_0x00637be0(auStack_2c,0x20,&UNK_00c5dde0,uVar3 != 0);
      func_0x005926d0(&puStack_60,auStack_2c,&puStack_80,0,0);
    }
    puVar1 = puStack_68;
    uStack_9c = uStack_9c + 1;
    puStack_90 = puVar4 + 0x70;
  } while ((int)puStack_90 < 0x2e8a95c);
  cStack_81 = puStack_68[0x9118];
  puStack_68[0x9118] = cStack_81 == '\0';
  puStack_60 = (undefined *)func_0x00590940();
  puStack_80 = (undefined *)func_0x00590a80();
  iVar8 = FUN_006da140();
  uStack_9c = func_0x005957b0(&UNK_00c67e7c,0);
  if (*(char *)(iVar8 + 0x9128) != '\0') {
    uStack_9c = *(uint *)(iVar8 + 0x9124) ^ uStack_9c;
    uStack_9c = uStack_9c << 8 | uStack_9c >> 0x18;
  }
  if ((DAT_07817df1 != '\0') && (cVar2 = func_0x005908f0(uStack_9c), cVar2 == '\0')) {
    uStack_9c = 0;
  }
  puStack_98 = (undefined *)func_0x00590bc0();
  puStack_68 = &UNK_00c67598;
  if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
    if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
      iVar8 = func_0x00a59520();
      puStack_90 = *(undefined **)(iVar8 + 0x20);
      puStack_8c = *(undefined1 **)(iVar8 + 0x24);
    }
    if ((_DAT_0c95bd80 != puStack_90) || (_DAT_0c95bd84 != puStack_8c)) {
      FUN_006d9da0(0,&puStack_90);
    }
  }
  puStack_90 = (undefined *)0xc95be10;
  puStack_8c = (undefined1 *)0x7ffc;
  puVar4 = (undefined *)func_0x00592930(&puStack_68);
  if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
    if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
      iVar8 = func_0x00a59520();
      puStack_68 = *(undefined **)(iVar8 + 0x20);
      puStack_64 = *(undefined1 **)(iVar8 + 0x24);
    }
    if ((_DAT_0c95bd80 != puStack_68) || (_DAT_0c95bd84 != puStack_64)) {
      FUN_006d9da0(0,&puStack_68);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    puVar4 = (undefined *)
             ((_DAT_0c964ea4 ^ (uint)puVar4) << 8 | (_DAT_0c964ea4 ^ (uint)puVar4) >> 0x18);
  }
  puStack_90 = puVar4;
  if ((DAT_07817df1 != '\0') && (cVar2 = func_0x005908f0(puVar4), cVar2 == '\0')) {
    puStack_90 = (undefined *)0x0;
  }
  puStack_68 = (undefined *)func_0x00590e30(0);
  puVar4 = puStack_60;
  bVar9 = DAT_07817df1 != '\0';
  puVar1[0x9118] = cStack_81;
  if ((bVar9) && (cVar2 = func_0x005908f0(puStack_60), cVar2 == '\0')) {
    puVar5 = (ushort *)func_0x00584470();
    if (puVar5 == (ushort *)0x0) {
      puVar4 = (undefined *)0x0;
    }
    else {
      uVar6 = *puVar5 ^ (ushort)puVar5 ^ _DAT_00cdd5a0;
      puVar4 = (undefined *)(uint)(ushort)(uVar6 << 4 | uVar6 >> 0xc);
    }
  }
  if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
    if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
      iVar8 = func_0x00a59520();
      puStack_60 = *(undefined **)(iVar8 + 0x20);
      puStack_5c = *(undefined1 **)(iVar8 + 0x24);
    }
    if ((_DAT_0c95bd80 != puStack_60) || (_DAT_0c95bd84 != puStack_5c)) {
      FUN_006d9da0(0,&puStack_60);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    puVar4 = (undefined *)(((int)puVar4 << 0x18 | (int)puVar4 >> 8) ^ _DAT_0c964ea4);
  }
  puStack_60 = &UNK_00c67e54;
  iVar8 = FUN_006da140();
  if ((undefined *)(iVar8 + 0x90) == (undefined *)0x0) {
    func_0x00597d20(2,&UNK_00c6c1e4,&UNK_00c67e54,puVar4);
  }
  else {
    puStack_70 = (undefined1 *)0x7ffc;
    puStack_74 = (undefined *)(iVar8 + 0x90);
    func_0x00637be0(auStack_4c,0x20,&UNK_00c5dde0,puVar4);
    func_0x005926d0(&puStack_60,auStack_4c,&puStack_74,0,0);
  }
  puVar4 = puStack_80;
  if ((DAT_07817df1 != '\0') && (cVar2 = func_0x005908f0(puStack_80), cVar2 == '\0')) {
    puVar5 = (ushort *)func_0x00584470();
    if (puVar5 == (ushort *)0x0) {
      puVar4 = (undefined *)0x0;
    }
    else {
      uVar6 = (ushort)puVar5 ^ (ushort)_DAT_00cdd5a0 ^ *puVar5;
      puVar4 = (undefined *)(uint)(ushort)(uVar6 << 4 | uVar6 >> 0xc);
    }
  }
  if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
    if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
      iVar8 = func_0x00a59520();
      puStack_80 = *(undefined **)(iVar8 + 0x20);
      puStack_7c = *(undefined1 **)(iVar8 + 0x24);
    }
    if ((_DAT_0c95bd80 != puStack_80) || (_DAT_0c95bd84 != puStack_7c)) {
      FUN_006d9da0(0,&puStack_80);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    puVar4 = (undefined *)(((int)puVar4 << 0x18 | (int)puVar4 >> 8) ^ _DAT_0c964ea4);
  }
  puStack_80 = &UNK_00c67e60;
  iVar8 = FUN_006da140();
  if ((undefined *)(iVar8 + 0x90) == (undefined *)0x0) {
    func_0x00597d20(2,&UNK_00c6c1e4,&UNK_00c67e60,puVar4);
  }
  else {
    puStack_70 = (undefined1 *)0x7ffc;
    puStack_74 = (undefined *)(iVar8 + 0x90);
    func_0x00637be0(auStack_4c,0x20,&UNK_00c5dde0,puVar4);
    func_0x005926d0(&puStack_80,auStack_4c,&puStack_74,0,0);
  }
  if (DAT_07817df1 != '\0') {
    func_0x005908f0(uStack_9c);
  }
  FUN_006da140();
  func_0x005927e0();
  puVar4 = puStack_98;
  if ((DAT_07817df1 != '\0') && (cVar2 = func_0x005908f0(puStack_98), cVar2 == '\0')) {
    puVar5 = (ushort *)func_0x00584470();
    if (puVar5 == (ushort *)0x0) {
      puVar4 = (undefined *)0x0;
    }
    else {
      uVar6 = *puVar5 ^ (ushort)puVar5 ^ _DAT_00cdd5a0;
      puVar4 = (undefined *)(uint)(ushort)(uVar6 << 4 | uVar6 >> 0xc);
    }
  }
  if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
    if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
      iVar8 = func_0x00a59520();
      puStack_98 = *(undefined **)(iVar8 + 0x20);
      puStack_94 = *(undefined1 **)(iVar8 + 0x24);
    }
    if ((_DAT_0c95bd80 != puStack_98) || (_DAT_0c95bd84 != puStack_94)) {
      FUN_006d9da0(0,&puStack_98);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    puVar4 = (undefined *)(((int)puVar4 << 0x18 | (int)puVar4 >> 8) ^ _DAT_0c964ea4);
  }
  puStack_98 = &UNK_00c67e6c;
  iVar8 = FUN_006da140();
  if ((undefined *)(iVar8 + 0x90) == (undefined *)0x0) {
    func_0x00597d20(2,&UNK_00c6c1e4,&UNK_00c67e6c,puVar4);
  }
  else {
    puStack_70 = (undefined1 *)0x7ffc;
    puStack_74 = (undefined *)(iVar8 + 0x90);
    func_0x00637be0(auStack_4c,0x20,&UNK_00c5dde0,puVar4);
    func_0x005926d0(&puStack_98,auStack_4c,&puStack_74,0,0);
  }
  puVar4 = puStack_90;
  if ((DAT_07817df1 != '\0') && (cVar2 = func_0x005908f0(puStack_90), cVar2 == '\0')) {
    puVar4 = (undefined *)0x0;
  }
  if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
    if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
      iVar8 = func_0x00a59520();
      puStack_98 = *(undefined **)(iVar8 + 0x20);
      puStack_94 = *(undefined1 **)(iVar8 + 0x24);
    }
    if ((_DAT_0c95bd80 != puStack_98) || (_DAT_0c95bd84 != puStack_94)) {
      FUN_006d9da0(0,&puStack_98);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    puVar4 = (undefined *)(((int)puVar4 << 0x18 | (int)puVar4 >> 8) ^ _DAT_0c964ea4);
  }
  puStack_98 = &UNK_00c67598;
  iVar8 = FUN_006da140();
  if ((undefined *)(iVar8 + 0x90) == (undefined *)0x0) {
    func_0x00597d20(2,&UNK_00c6c1e4,&UNK_00c67598,puVar4);
  }
  else {
    puStack_70 = (undefined1 *)0x7ffc;
    puStack_74 = (undefined *)(iVar8 + 0x90);
    func_0x00637be0(auStack_4c,0x20,&UNK_00c5dde0,puVar4);
    func_0x005926d0(&puStack_98,auStack_4c,&puStack_74,0,0);
  }
  puVar4 = puStack_68;
  if ((DAT_07817df1 != '\0') && (cVar2 = func_0x005908f0(puStack_68), cVar2 == '\0')) {
    puVar4 = (undefined *)0x0;
  }
  if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
    if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
      iVar8 = func_0x00a59520();
      puStack_98 = *(undefined **)(iVar8 + 0x20);
      puStack_94 = *(undefined1 **)(iVar8 + 0x24);
    }
    if ((_DAT_0c95bd80 != puStack_98) || (_DAT_0c95bd84 != puStack_94)) {
      FUN_006d9da0(0,&puStack_98);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    puVar4 = (undefined *)(((int)puVar4 << 0x18 | (int)puVar4 >> 8) ^ _DAT_0c964ea4);
  }
  puStack_98 = &UNK_00c6af5c;
  iVar8 = FUN_006da140();
  if ((undefined *)(iVar8 + 0x90) == (undefined *)0x0) {
    func_0x00597d20(2,&UNK_00c6c1e4,&UNK_00c6af5c,puVar4);
    func_0x00af6b2f();
    return;
  }
  puStack_70 = (undefined1 *)0x7ffc;
  puStack_74 = (undefined *)(iVar8 + 0x90);
  func_0x00637be0(auStack_4c,0x20,&UNK_00c5dde0,puVar4);
  func_0x005926d0(&puStack_98,auStack_4c,&puStack_74,0,0);
  func_0x00af6b2f();
  return;
}

