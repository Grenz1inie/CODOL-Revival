// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.purchase
// Analyst label: 购买任务分派
// VA: 0x004a6550; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_11f85cb05c3c92cc49459f59c8c6d10e124509c45e6829a9206c1d2dff36a485
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_004a6550(int param_1,int param_2)

{
  LONG *lpAddend;
  uint uVar1;
  char cVar2;
  int iVar3;
  int *piVar4;
  LONG LVar5;
  uint uVar6;
  undefined *puVar7;
  byte bVar8;
  uint uVar9;
  undefined4 *puVar10;
  ushort uVar11;
  undefined4 *puVar12;
  code *pcVar13;
  undefined4 uVar14;
  undefined4 uVar15;
  undefined4 uVar16;
  code *pcVar17;
  undefined4 uVar18;
  int local_19c;
  uint local_198;
  undefined4 *local_194;
  undefined4 *local_190;
  char local_189;
  undefined4 auStack_188 [32];
  uint local_108 [32];
  undefined4 local_88 [32];
  uint local_8;
  
  local_8 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  local_190 = (undefined4 *)0x0;
  iVar3 = FUN_006fed10();
  if ((iVar3 != 0) && (iVar3 = FUN_00a3c920(), iVar3 == 2)) {
    local_190 = (undefined4 *)FUN_00a421e0(&DAT_00c4e869);
  }
  local_194 = (undefined4 *)0x0;
  iVar3 = FUN_006fed10();
  if ((iVar3 != 0) && (iVar3 = FUN_00a3c920(), iVar3 == 2)) {
    local_194 = (undefined4 *)FUN_00a42310(&DAT_00c4e869);
  }
  if ((local_190 == (undefined4 *)0x0) || (local_194 == (undefined4 *)0x0)) {
    __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
    return;
  }
  uVar9 = 0;
  iVar3 = 0;
  local_189 = '\0';
  local_198 = local_198 & 0xffffff00;
  if (0 < param_2) {
    do {
      uVar1 = *(uint *)(param_1 + iVar3 * 4);
      cVar2 = FUN_00707480();
      if (cVar2 == '\0') {
        local_108[uVar9] = uVar1;
        auStack_188[uVar9] = 0;
        local_88[uVar9] = 1;
        uVar9 = (uint)(byte)((char)uVar9 + 1);
      }
      iVar3 = iVar3 + 1;
    } while (iVar3 < param_2);
    local_198 = CONCAT31(local_198._1_3_,(char)uVar9);
    if ((char)uVar9 != '\0') {
      puVar10 = (undefined4 *)0x0;
      piVar4 = (int *)FUN_00a47370(&local_190,local_108,local_88,local_198,0);
      if ((piVar4 != &local_19c) && (puVar10 = (undefined4 *)*piVar4, puVar10 != (undefined4 *)0x0))
      {
        InterlockedIncrement(puVar10 + 1);
      }
      if (((local_190 != (undefined4 *)0x0) &&
          (LVar5 = InterlockedDecrement(local_190 + 1), LVar5 == 0)) &&
         (local_190 != (undefined4 *)0x0)) {
        (**(code **)*local_190)(1);
      }
      if (puVar10 == (undefined4 *)0x0) {
        local_189 = '\0';
      }
      else {
        pcVar17 = FUN_004a6940;
        puVar12 = puVar10;
        InterlockedIncrement(puVar10 + 1);
        FUN_006f5fb0(0x59,puVar12,pcVar17);
        local_189 = '\x01';
        LVar5 = InterlockedDecrement(puVar10 + 1);
        if (LVar5 == 0) {
          (**(code **)*puVar10)(1);
        }
      }
    }
  }
  uVar9 = local_198;
  bVar8 = 0;
  iVar3 = 0;
  local_198 = local_198 & 0xffffff00;
  if (0 < param_2) {
    do {
      uVar1 = *(uint *)(param_1 + iVar3 * 4);
      if ((short)uVar1 != 0) {
        uVar6 = uVar1 & 0xffff;
        if (uVar6 < DAT_02dbb294) {
          uVar11 = *(ushort *)(DAT_02dbb290 + uVar6 * 2);
        }
        else {
          if (DAT_02dbb294 + 5000 <= uVar6) goto LAB_004a67e1;
          uVar11 = *(ushort *)(&DAT_07838120 + (uVar6 - DAT_02dbb294) * 2);
        }
        uVar6 = (uint)uVar11;
        if (uVar11 == 0) {
          puVar7 = (undefined *)0x0;
        }
        else if (uVar6 < DAT_02dbb28c) {
          puVar7 = (undefined *)(DAT_02dbb288 + uVar6 * 0x18);
        }
        else if (uVar6 < DAT_07838118 + DAT_02dbb28c) {
          puVar7 = &DAT_02dbba58 + (uVar6 - DAT_02dbb28c) * 0x18;
        }
        else {
          puVar7 = (undefined *)0x0;
        }
        if ((puVar7 != (undefined *)0x0) &&
           (uVar11 = (ushort)(puVar7 + 6) ^ (ushort)_DAT_00cdd588 ^ *(ushort *)(puVar7 + 6),
           (uVar11 & 0xfff) != 0 || uVar11 >> 0xc != 0)) {
          local_108[bVar8] = uVar1;
          auStack_188[bVar8] = 0;
          local_88[bVar8] = 1;
          bVar8 = bVar8 + 1;
        }
      }
LAB_004a67e1:
      iVar3 = iVar3 + 1;
    } while (iVar3 < param_2);
    local_198._1_3_ = SUB43(uVar9,1);
    local_198 = CONCAT31(local_198._1_3_,bVar8);
    if (bVar8 != 0) {
      puVar10 = (undefined4 *)0x0;
      piVar4 = (int *)FUN_00a4c280(&local_194,local_108,local_88,local_198,0);
      if ((piVar4 != &local_19c) && (puVar10 = (undefined4 *)*piVar4, puVar10 != (undefined4 *)0x0))
      {
        InterlockedIncrement(puVar10 + 1);
      }
      if ((local_194 != (undefined4 *)0x0) &&
         (LVar5 = InterlockedDecrement(local_194 + 1), LVar5 == 0)) {
        if (local_194 != (undefined4 *)0x0) {
          (**(code **)*local_194)(1);
        }
        local_194 = (undefined4 *)0x0;
      }
      if (puVar10 != (undefined4 *)0x0) {
        lpAddend = puVar10 + 1;
        InterlockedIncrement(lpAddend);
        uVar18 = 0;
        uVar16 = 0;
        uVar15 = 0;
        uVar14 = 0;
        pcVar13 = FUN_00a53d80;
        pcVar17 = FUN_004a6940;
        puVar12 = puVar10;
        InterlockedIncrement(lpAddend);
        FUN_006f5d20(0x59,puVar12,pcVar17,pcVar13,uVar14,uVar15,uVar16,uVar18);
        LVar5 = InterlockedDecrement(lpAddend);
        if (LVar5 == 0) {
          (**(code **)*puVar10)(1);
        }
      }
      if ((local_189 == '\0') && (puVar10 == (undefined4 *)0x0)) {
        local_189 = 0;
        __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
        return;
      }
      local_189 = '\x01';
      if ((puVar10 != (undefined4 *)0x0) && (LVar5 = InterlockedDecrement(puVar10 + 1), LVar5 == 0))
      {
        (**(code **)*puVar10)(1);
      }
    }
  }
  __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
  return;
}

