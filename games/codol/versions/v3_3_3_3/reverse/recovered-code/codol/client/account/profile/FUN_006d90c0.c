// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 装备与名片缓存回写档案
// VA: 0x006d90c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_37c53beb71d86cc04bee93c325a1d545439eb29ace7d62de34f2fb6c251158e9
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006d90c0(char *param_1)

{
  undefined *puVar1;
  char *pcVar2;
  char cVar3;
  uint uVar4;
  char *pcVar5;
  ushort *puVar6;
  ushort uVar7;
  uint *puVar8;
  int iVar9;
  bool bVar10;
  undefined *local_9c;
  char *local_98;
  undefined1 *local_94;
  char *local_90;
  undefined1 *local_8c;
  char local_81;
  char *local_80;
  undefined1 *local_7c;
  char *local_74;
  undefined1 *local_70;
  char *local_6c;
  char *local_68;
  undefined1 *local_64;
  char *local_60;
  undefined1 *local_5c;
  char *local_58;
  undefined1 local_4c [32];
  undefined1 local_2c [32];
  uint local_c;
  
  local_c = DAT_00cc7c80 ^ (uint)&local_9c;
  local_68 = param_1;
  iVar9 = 0;
  do {
    FUN_00592b10();
    iVar9 = iVar9 + 1;
  } while (iVar9 < 0x78);
  local_90 = (char *)0x0;
  local_9c = &DAT_02e16e54;
  do {
    iVar9 = 0;
    do {
      pcVar5 = local_90;
      FUN_00593210(local_90,iVar9);
      puVar1 = local_9c;
      iVar9 = iVar9 + 1;
    } while (iVar9 < 9);
    FUN_00593500(pcVar5);
    local_9c = puVar1 + 0x4c;
    local_90 = pcVar5 + 1;
  } while ((int)local_9c < 0x2e171e4);
  local_9c = (undefined *)0x0;
  local_90 = &DAT_02e88f1c;
  do {
    iVar9 = 0;
    puVar8 = (uint *)(local_90 + 0x24);
    do {
      if (local_90[iVar9 + 0x10] == '\0') {
        uVar4 = 0;
      }
      else {
        uVar4 = (DAT_00cdd280 >> (0x10U - (char)iVar9 & 0x1f) |
                DAT_00cdd280 << ((char)iVar9 + 0x10U & 0x1f)) ^ *puVar8;
        uVar4 = uVar4 << 8 | uVar4 >> 0x18;
      }
      FUN_00592f50(local_9c,uVar4);
      iVar9 = iVar9 + 1;
      puVar8 = puVar8 + 1;
    } while (iVar9 < 6);
    iVar9 = 0;
    puVar8 = (uint *)(local_90 + 0x48);
    do {
      if (local_90[iVar9 + 0x19] == '\0') {
        uVar4 = 0;
      }
      else {
        uVar4 = (DAT_00cdd280 >> (0x10U - (char)iVar9 & 0x1f) |
                DAT_00cdd280 << ((char)iVar9 + 0x10U & 0x1f)) ^ *puVar8;
        uVar4 = uVar4 << 8 | uVar4 >> 0x18;
      }
      FUN_00592f50(local_9c,uVar4);
      iVar9 = iVar9 + 1;
      puVar8 = puVar8 + 1;
    } while (iVar9 < 3);
    iVar9 = 0;
    puVar8 = (uint *)(local_90 + 0x54);
    do {
      if (local_90[iVar9 + 0x1c] == '\0') {
        uVar4 = 0;
      }
      else {
        uVar4 = (DAT_00cdd280 >> (0x10U - (char)iVar9 & 0x1f) |
                DAT_00cdd280 << ((char)iVar9 + 0x10U & 0x1f)) ^ *puVar8;
        uVar4 = uVar4 << 8 | uVar4 >> 0x18;
      }
      FUN_00592f50(local_9c,uVar4);
      iVar9 = iVar9 + 1;
      puVar8 = puVar8 + 1;
    } while (iVar9 < 3);
    iVar9 = 0;
    puVar8 = (uint *)(local_90 + 0x3c);
    do {
      if (local_90[iVar9 + 0x16] == '\0') {
        uVar4 = 0;
      }
      else {
        uVar4 = (DAT_00cdd280 >> (0x10U - (char)iVar9 & 0x1f) |
                DAT_00cdd280 << ((char)iVar9 + 0x10U & 0x1f)) ^ *puVar8;
        uVar4 = uVar4 << 8 | uVar4 >> 0x18;
      }
      FUN_00592f50(local_9c,uVar4);
      pcVar5 = local_90;
      iVar9 = iVar9 + 1;
      puVar8 = puVar8 + 1;
    } while (iVar9 < 3);
    if (local_90[0x1f] == '\0') {
      uVar4 = 0;
    }
    else {
      uVar4 = (*(uint *)(local_90 + 0x60) ^ DAT_00cdd280) << 8 |
              (*(uint *)(local_90 + 0x60) ^ DAT_00cdd280) >> 0x18;
    }
    iVar9 = FUN_006da140();
    local_98 = (char *)(iVar9 + 0x90);
    if (local_98 == (char *)0x0) {
      local_98 = (char *)0x0;
      local_94 = (undefined1 *)0x0;
    }
    else {
      local_94 = (undefined1 *)0x7ffc;
      local_74 = "weaponClasses";
      FUN_00637be0(local_2c,0x20,&DAT_00c5dde0,local_9c);
      local_70 = local_2c;
      local_6c = "lethalDoubleAmmo";
      FUN_00637be0(local_4c,0x20,&DAT_00c5dde0,uVar4 != 0);
      FUN_005926d0(&local_74,local_4c,&local_98,0,0);
    }
    if (pcVar5[0x20] == '\0') {
      uVar4 = 0;
    }
    else {
      uVar4 = (*(uint *)(pcVar5 + 100) ^ DAT_00cdd280) << 8 |
              (*(uint *)(pcVar5 + 100) ^ DAT_00cdd280) >> 0x18;
    }
    iVar9 = FUN_006da140();
    local_80 = (char *)(iVar9 + 0x90);
    if (local_80 == (char *)0x0) {
      local_80 = (char *)0x0;
      local_7c = (undefined1 *)0x0;
    }
    else {
      local_7c = (undefined1 *)0x7ffc;
      local_60 = "weaponClasses";
      FUN_00637be0(local_4c,0x20,&DAT_00c5dde0,local_9c);
      local_5c = local_4c;
      local_58 = "tacticalDoubleAmmo";
      FUN_00637be0(local_2c,0x20,&DAT_00c5dde0,uVar4 != 0);
      FUN_005926d0(&local_60,local_2c,&local_80,0,0);
    }
    pcVar2 = local_68;
    local_9c = local_9c + 1;
    local_90 = pcVar5 + 0x70;
  } while ((int)local_90 < 0x2e8a95c);
  local_81 = local_68[0x9118];
  local_68[0x9118] = local_81 == '\0';
  local_60 = (char *)FUN_00590940();
  local_80 = (char *)FUN_00590a80();
  iVar9 = FUN_006da140();
  local_9c = (undefined *)FUN_005957b0("cardNameplate",0);
  if (*(char *)(iVar9 + 0x9128) != '\0') {
    uVar4 = *(uint *)(iVar9 + 0x9124) ^ (uint)local_9c;
    local_9c = (undefined *)(uVar4 << 8 | uVar4 >> 0x18);
  }
  if ((DAT_07817df1 != '\0') && (cVar3 = FUN_005908f0(local_9c), cVar3 == '\0')) {
    local_9c = (undefined *)0x0;
  }
  local_98 = (char *)FUN_00590bc0();
  local_68 = "badge";
  if ((DAT_00cd7000 == 4) || (DAT_00cd7000 == 6)) {
    if ((DAT_078b08bc != 0) || (DAT_078b08c8 != 0)) {
      iVar9 = FUN_00a59520();
      local_90 = *(char **)(iVar9 + 0x20);
      local_8c = *(undefined1 **)(iVar9 + 0x24);
    }
    if ((DAT_0c95bd80 != local_90) || (DAT_0c95bd84 != local_8c)) {
      FUN_006d9da0(0,&local_90);
    }
  }
  local_90 = &DAT_0c95be10;
  local_8c = (undefined1 *)0x7ffc;
  pcVar5 = (char *)FUN_00592930(&local_68);
  if ((DAT_00cd7000 == 4) || (DAT_00cd7000 == 6)) {
    if ((DAT_078b08bc != 0) || (DAT_078b08c8 != 0)) {
      iVar9 = FUN_00a59520();
      local_68 = *(char **)(iVar9 + 0x20);
      local_64 = *(undefined1 **)(iVar9 + 0x24);
    }
    if ((DAT_0c95bd80 != local_68) || (DAT_0c95bd84 != local_64)) {
      FUN_006d9da0(0,&local_68);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    pcVar5 = (char *)((DAT_0c964ea4 ^ (uint)pcVar5) << 8 | (DAT_0c964ea4 ^ (uint)pcVar5) >> 0x18);
  }
  local_90 = pcVar5;
  if ((DAT_07817df1 != '\0') && (cVar3 = FUN_005908f0(pcVar5), cVar3 == '\0')) {
    local_90 = (char *)0x0;
  }
  local_68 = (char *)FUN_00590e30(0);
  pcVar5 = local_60;
  bVar10 = DAT_07817df1 != '\0';
  pcVar2[0x9118] = local_81;
  if ((bVar10) && (cVar3 = FUN_005908f0(local_60), cVar3 == '\0')) {
    puVar6 = (ushort *)FUN_00584470();
    if (puVar6 == (ushort *)0x0) {
      pcVar5 = (char *)0x0;
    }
    else {
      uVar7 = *puVar6 ^ (ushort)puVar6 ^ DAT_00cdd5a0;
      pcVar5 = (char *)(uint)(ushort)(uVar7 << 4 | uVar7 >> 0xc);
    }
  }
  if ((DAT_00cd7000 == 4) || (DAT_00cd7000 == 6)) {
    if ((DAT_078b08bc != 0) || (DAT_078b08c8 != 0)) {
      iVar9 = FUN_00a59520();
      local_60 = *(char **)(iVar9 + 0x20);
      local_5c = *(undefined1 **)(iVar9 + 0x24);
    }
    if ((DAT_0c95bd80 != local_60) || (DAT_0c95bd84 != local_5c)) {
      FUN_006d9da0(0,&local_60);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    pcVar5 = (char *)(((int)pcVar5 << 0x18 | (int)pcVar5 >> 8) ^ DAT_0c964ea4);
  }
  local_60 = "cardIcon";
  iVar9 = FUN_006da140();
  if ((char *)(iVar9 + 0x90) == (char *)0x0) {
    FUN_00597d20(2,"701 %s %i","cardIcon",pcVar5);
  }
  else {
    local_70 = (undefined1 *)0x7ffc;
    local_74 = (char *)(iVar9 + 0x90);
    FUN_00637be0(local_4c,0x20,&DAT_00c5dde0,pcVar5);
    FUN_005926d0(&local_60,local_4c,&local_74,0,0);
  }
  pcVar5 = local_80;
  if ((DAT_07817df1 != '\0') && (cVar3 = FUN_005908f0(local_80), cVar3 == '\0')) {
    puVar6 = (ushort *)FUN_00584470();
    if (puVar6 == (ushort *)0x0) {
      pcVar5 = (char *)0x0;
    }
    else {
      uVar7 = (ushort)puVar6 ^ (ushort)_DAT_00cdd5a0 ^ *puVar6;
      pcVar5 = (char *)(uint)(ushort)(uVar7 << 4 | uVar7 >> 0xc);
    }
  }
  if ((DAT_00cd7000 == 4) || (DAT_00cd7000 == 6)) {
    if ((DAT_078b08bc != 0) || (DAT_078b08c8 != 0)) {
      iVar9 = FUN_00a59520();
      local_80 = *(char **)(iVar9 + 0x20);
      local_7c = *(undefined1 **)(iVar9 + 0x24);
    }
    if ((DAT_0c95bd80 != local_80) || (DAT_0c95bd84 != local_7c)) {
      FUN_006d9da0(0,&local_80);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    pcVar5 = (char *)(((int)pcVar5 << 0x18 | (int)pcVar5 >> 8) ^ DAT_0c964ea4);
  }
  local_80 = "cardTitle";
  iVar9 = FUN_006da140();
  if ((char *)(iVar9 + 0x90) == (char *)0x0) {
    FUN_00597d20(2,"701 %s %i","cardTitle",pcVar5);
  }
  else {
    local_70 = (undefined1 *)0x7ffc;
    local_74 = (char *)(iVar9 + 0x90);
    FUN_00637be0(local_4c,0x20,&DAT_00c5dde0,pcVar5);
    FUN_005926d0(&local_80,local_4c,&local_74,0,0);
  }
  if (DAT_07817df1 != '\0') {
    FUN_005908f0(local_9c);
  }
  FUN_006da140();
  FUN_005927e0();
  pcVar5 = local_98;
  if ((DAT_07817df1 != '\0') && (cVar3 = FUN_005908f0(local_98), cVar3 == '\0')) {
    puVar6 = (ushort *)FUN_00584470();
    if (puVar6 == (ushort *)0x0) {
      pcVar5 = (char *)0x0;
    }
    else {
      uVar7 = *puVar6 ^ (ushort)puVar6 ^ DAT_00cdd5a0;
      pcVar5 = (char *)(uint)(ushort)(uVar7 << 4 | uVar7 >> 0xc);
    }
  }
  if ((DAT_00cd7000 == 4) || (DAT_00cd7000 == 6)) {
    if ((DAT_078b08bc != 0) || (DAT_078b08c8 != 0)) {
      iVar9 = FUN_00a59520();
      local_98 = *(char **)(iVar9 + 0x20);
      local_94 = *(undefined1 **)(iVar9 + 0x24);
    }
    if ((DAT_0c95bd80 != local_98) || (DAT_0c95bd84 != local_94)) {
      FUN_006d9da0(0,&local_98);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    pcVar5 = (char *)(((int)pcVar5 << 0x18 | (int)pcVar5 >> 8) ^ DAT_0c964ea4);
  }
  local_98 = "cardBackground";
  iVar9 = FUN_006da140();
  if ((char *)(iVar9 + 0x90) == (char *)0x0) {
    FUN_00597d20(2,"701 %s %i","cardBackground",pcVar5);
  }
  else {
    local_70 = (undefined1 *)0x7ffc;
    local_74 = (char *)(iVar9 + 0x90);
    FUN_00637be0(local_4c,0x20,&DAT_00c5dde0,pcVar5);
    FUN_005926d0(&local_98,local_4c,&local_74,0,0);
  }
  pcVar5 = local_90;
  if ((DAT_07817df1 != '\0') && (cVar3 = FUN_005908f0(local_90), cVar3 == '\0')) {
    pcVar5 = (char *)0x0;
  }
  if ((DAT_00cd7000 == 4) || (DAT_00cd7000 == 6)) {
    if ((DAT_078b08bc != 0) || (DAT_078b08c8 != 0)) {
      iVar9 = FUN_00a59520();
      local_98 = *(char **)(iVar9 + 0x20);
      local_94 = *(undefined1 **)(iVar9 + 0x24);
    }
    if ((DAT_0c95bd80 != local_98) || (DAT_0c95bd84 != local_94)) {
      FUN_006d9da0(0,&local_98);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    pcVar5 = (char *)(((int)pcVar5 << 0x18 | (int)pcVar5 >> 8) ^ DAT_0c964ea4);
  }
  local_98 = "badge";
  iVar9 = FUN_006da140();
  if ((char *)(iVar9 + 0x90) == (char *)0x0) {
    FUN_00597d20(2,"701 %s %i","badge",pcVar5);
  }
  else {
    local_70 = (undefined1 *)0x7ffc;
    local_74 = (char *)(iVar9 + 0x90);
    FUN_00637be0(local_4c,0x20,&DAT_00c5dde0,pcVar5);
    FUN_005926d0(&local_98,local_4c,&local_74,0,0);
  }
  pcVar5 = local_68;
  if ((DAT_07817df1 != '\0') && (cVar3 = FUN_005908f0(local_68), cVar3 == '\0')) {
    pcVar5 = (char *)0x0;
  }
  if ((DAT_00cd7000 == 4) || (DAT_00cd7000 == 6)) {
    if ((DAT_078b08bc != 0) || (DAT_078b08c8 != 0)) {
      iVar9 = FUN_00a59520();
      local_98 = *(char **)(iVar9 + 0x20);
      local_94 = *(undefined1 **)(iVar9 + 0x24);
    }
    if ((DAT_0c95bd80 != local_98) || (DAT_0c95bd84 != local_94)) {
      FUN_006d9da0(0,&local_98);
    }
  }
  if (DAT_0c964ea8 != '\0') {
    pcVar5 = (char *)(((int)pcVar5 << 0x18 | (int)pcVar5 >> 8) ^ DAT_0c964ea4);
  }
  local_98 = "acestreak";
  iVar9 = FUN_006da140();
  if ((char *)(iVar9 + 0x90) == (char *)0x0) {
    FUN_00597d20(2,"701 %s %i","acestreak",pcVar5);
    __security_check_cookie(local_c ^ (uint)&local_9c);
    return;
  }
  local_70 = (undefined1 *)0x7ffc;
  local_74 = (char *)(iVar9 + 0x90);
  FUN_00637be0(local_4c,0x20,&DAT_00c5dde0,pcVar5);
  FUN_005926d0(&local_98,local_4c,&local_74,0,0);
  __security_check_cookie(local_c ^ (uint)&local_9c);
  return;
}

