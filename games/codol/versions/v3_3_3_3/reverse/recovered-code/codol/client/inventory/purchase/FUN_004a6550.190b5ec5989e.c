// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.purchase
// Analyst label: 购买任务分派
// VA: 0x004a6550; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_004a6550(int param_1,int param_2)

{
  uint uVar1;
  char cVar2;
  int iVar3;
  int *piVar4;
  uint uVar5;
  int iVar6;
  byte bVar7;
  uint uVar8;
  undefined4 *puVar9;
  ushort uVar10;
  undefined4 *puVar11;
  undefined1 *puVar12;
  undefined4 uVar13;
  undefined4 uVar14;
  undefined4 *puVar15;
  undefined4 uVar16;
  code *pcVar17;
  undefined4 uVar18;
  int iStack_19c;
  uint uStack_198;
  undefined4 *puStack_194;
  undefined4 *puStack_190;
  char cStack_189;
  undefined4 auStack_188 [32];
  uint auStack_108 [32];
  undefined4 auStack_88 [32];
  uint uStack_8;
  
  uStack_8 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  puStack_190 = (undefined4 *)0x0;
  iVar3 = func_0x006fed10();
  if ((iVar3 != 0) && (iVar3 = func_0x00a3c920(), iVar3 == 2)) {
    puStack_190 = (undefined4 *)func_0x00a421e0(&UNK_00c4e869);
  }
  puStack_194 = (undefined4 *)0x0;
  iVar3 = func_0x006fed10();
  if ((iVar3 != 0) && (iVar3 = func_0x00a3c920(), iVar3 == 2)) {
    puStack_194 = (undefined4 *)func_0x00a42310(&UNK_00c4e869);
  }
  if ((puStack_190 == (undefined4 *)0x0) || (puStack_194 == (undefined4 *)0x0)) {
    func_0x00af6b2f();
    return;
  }
  uVar8 = 0;
  iVar3 = 0;
  cStack_189 = '\0';
  uStack_198 = uStack_198 & 0xffffff00;
  if (0 < param_2) {
    do {
      uVar1 = *(uint *)(param_1 + iVar3 * 4);
      cVar2 = func_0x00707480();
      if (cVar2 == '\0') {
        auStack_108[uVar8] = uVar1;
        auStack_188[uVar8] = 0;
        auStack_88[uVar8] = 1;
        uVar8 = (uint)(byte)((char)uVar8 + 1);
      }
      iVar3 = iVar3 + 1;
    } while (iVar3 < param_2);
    uStack_198 = CONCAT31(uStack_198._1_3_,(char)uVar8);
    if ((char)uVar8 != '\0') {
      puVar9 = (undefined4 *)0x0;
      piVar4 = (int *)FUN_00a47370(&puStack_190,auStack_108,auStack_88,uStack_198,0);
      if ((piVar4 != &iStack_19c) && (puVar9 = (undefined4 *)*piVar4, puVar9 != (undefined4 *)0x0))
      {
        InterlockedIncrement(puVar9 + 1);
      }
      if (((puStack_190 != (undefined4 *)0x0) &&
          (iVar3 = InterlockedDecrement(puStack_190 + 1), iVar3 == 0)) &&
         (puStack_190 != (undefined4 *)0x0)) {
        (**(code **)*puStack_190)(1);
      }
      if (puVar9 == (undefined4 *)0x0) {
        cStack_189 = '\0';
      }
      else {
        pcVar17 = FUN_004a6940;
        puVar15 = puVar9;
        InterlockedIncrement(puVar9 + 1);
        func_0x006f5fb0(0x59,puVar15,pcVar17);
        cStack_189 = '\x01';
        iVar3 = InterlockedDecrement(puVar9 + 1);
        if (iVar3 == 0) {
          (**(code **)*puVar9)(1);
        }
      }
    }
  }
  uVar8 = uStack_198;
  bVar7 = 0;
  iVar3 = 0;
  uStack_198 = uStack_198 & 0xffffff00;
  if (0 < param_2) {
    do {
      uVar1 = *(uint *)(param_1 + iVar3 * 4);
      if ((short)uVar1 != 0) {
        uVar5 = uVar1 & 0xffff;
        if (uVar5 < _DAT_02dbb294) {
          uVar10 = *(ushort *)(_DAT_02dbb290 + uVar5 * 2);
        }
        else {
          if (_DAT_02dbb294 + 5000 <= uVar5) goto LAB_004a67e1;
          uVar10 = *(ushort *)((uVar5 - _DAT_02dbb294) * 2 + 0x7838120);
        }
        uVar5 = (uint)uVar10;
        if (uVar10 == 0) {
          iVar6 = 0;
        }
        else if (uVar5 < _DAT_02dbb28c) {
          iVar6 = _DAT_02dbb288 + uVar5 * 0x18;
        }
        else if (uVar5 < _DAT_07838118 + _DAT_02dbb28c) {
          iVar6 = (uVar5 - _DAT_02dbb28c) * 0x18 + 0x2dbba58;
        }
        else {
          iVar6 = 0;
        }
        if ((iVar6 != 0) &&
           (uVar10 = (ushort)(ushort *)(iVar6 + 6) ^ (ushort)_DAT_00cdd588 ^ *(ushort *)(iVar6 + 6),
           (uVar10 & 0xfff) != 0 || uVar10 >> 0xc != 0)) {
          auStack_108[bVar7] = uVar1;
          auStack_188[bVar7] = 0;
          auStack_88[bVar7] = 1;
          bVar7 = bVar7 + 1;
        }
      }
LAB_004a67e1:
      iVar3 = iVar3 + 1;
    } while (iVar3 < param_2);
    uStack_198._1_3_ = SUB43(uVar8,1);
    uStack_198 = CONCAT31(uStack_198._1_3_,bVar7);
    if (bVar7 != 0) {
      puVar9 = (undefined4 *)0x0;
      piVar4 = (int *)FUN_00a4c280(&puStack_194,auStack_108,auStack_88,uStack_198,0);
      if ((piVar4 != &iStack_19c) && (puVar9 = (undefined4 *)*piVar4, puVar9 != (undefined4 *)0x0))
      {
        InterlockedIncrement(puVar9 + 1);
      }
      if ((puStack_194 != (undefined4 *)0x0) &&
         (iVar3 = InterlockedDecrement(puStack_194 + 1), iVar3 == 0)) {
        if (puStack_194 != (undefined4 *)0x0) {
          (**(code **)*puStack_194)(1);
        }
        puStack_194 = (undefined4 *)0x0;
      }
      if (puVar9 != (undefined4 *)0x0) {
        puVar15 = puVar9 + 1;
        InterlockedIncrement(puVar15);
        uVar18 = 0;
        uVar16 = 0;
        uVar14 = 0;
        uVar13 = 0;
        puVar12 = &SUB_00a53d80;
        pcVar17 = FUN_004a6940;
        puVar11 = puVar9;
        InterlockedIncrement(puVar15);
        func_0x006f5d20(0x59,puVar11,pcVar17,puVar12,uVar13,uVar14,uVar16,uVar18);
        iVar3 = InterlockedDecrement(puVar15);
        if (iVar3 == 0) {
          (**(code **)*puVar9)(1);
        }
      }
      if ((cStack_189 == '\0') && (puVar9 == (undefined4 *)0x0)) {
        cStack_189 = 0;
        func_0x00af6b2f();
        return;
      }
      cStack_189 = '\x01';
      if ((puVar9 != (undefined4 *)0x0) && (iVar3 = InterlockedDecrement(puVar9 + 1), iVar3 == 0)) {
        (**(code **)*puVar9)(1);
      }
    }
  }
  func_0x00af6b2f();
  return;
}

