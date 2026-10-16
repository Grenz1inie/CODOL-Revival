// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.catalog
// Analyst label: SKU 价格和期限读取
// VA: 0x007070b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_8cee2742af9e42fa32d9ec48864924683c55e58148a5b55dee7e3e79a979264c
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_007070b0(void)

{
  ushort in_AX;
  ushort uVar1;
  ushort uVar2;
  ushort *puVar3;
  ushort *puVar4;
  int iVar5;
  int iVar6;
  uint uVar7;
  uint uVar8;
  ushort uVar9;
  ushort uVar10;
  uint uVar11;
  uint *unaff_EDI;
  
  if (((in_AX == 0) ||
      ((((DAT_02dbb294 <= in_AX && (DAT_02dbb294 + 5000 <= (uint)in_AX)) ||
        (puVar3 = (ushort *)FUN_00584720(), puVar3 == (ushort *)0x0)) ||
       ((uVar2 = (ushort)puVar3, uVar1 = puVar3[2] ^ uVar2 + 4 ^ DAT_00cdd584,
        (uVar1 & 0xfff) == 0 && uVar1 >> 0xc == 0 ||
        (((puVar3[1] ^ uVar2 + 2 ^ DAT_00cdd580) & 0x1000) == 0)))))) ||
     (puVar4 = (ushort *)FUN_00584640(), puVar4 == (ushort *)0x0)) {
    return 0;
  }
  iVar5 = FUN_005845b0();
  iVar6 = FUN_005846e0();
  *unaff_EDI = (uint)*puVar4;
  if ((iVar5 == 0) || ((*(byte *)(iVar5 + 0x20) & 2) == 0)) {
    uVar7 = 0;
  }
  else {
    uVar7 = (uint)*(byte *)(*(int *)(puVar4 + 6) + 2);
  }
  uVar1 = puVar4[2];
  unaff_EDI[3] = uVar7;
  unaff_EDI[2] = (uint)uVar1;
  uVar7 = FUN_00584760();
  uVar9 = *puVar3 ^ _DAT_00cdd57c;
  unaff_EDI[1] = uVar7;
  uVar9 = uVar9 ^ uVar2;
  uVar1 = uVar2 + 6 ^ puVar3[3] ^ DAT_00cdd588;
  uVar10 = uVar2 + 8 ^ puVar3[4] ^ DAT_00cdd58c;
  unaff_EDI[4] = (uint)(ushort)(uVar9 << 4 | uVar9 >> 0xc);
  uVar7 = (uint)(ushort)(uVar1 << 4 | uVar1 >> 0xc);
  uVar8 = (uint)(ushort)(uVar10 << 4 | uVar10 >> 0xc);
  unaff_EDI[5] = uVar7;
  unaff_EDI[6] = uVar8;
  if (uVar7 == 0) {
    uVar7 = uVar8;
  }
  uVar8 = *(uint *)(puVar3 + 8);
  uVar1 = puVar3[5];
  unaff_EDI[7] = uVar7;
  uVar1 = uVar2 + 10 ^ uVar1 ^ _DAT_00cdd590;
  uVar11 = uVar8 ^ (uint)(puVar3 + 8) ^ _DAT_00cdd598;
  unaff_EDI[10] = (uint)(ushort)(uVar1 << 4 | uVar1 >> 0xc);
  uVar8 = *(uint *)(puVar3 + 10);
  unaff_EDI[8] = uVar11 << 8 | uVar11 >> 0x18;
  uVar8 = uVar8 ^ (uint)(puVar3 + 10) ^ _DAT_00cdd59c;
  uVar2 = (ushort)(puVar3[1] ^ uVar2 + 2 ^ DAT_00cdd580) >> 0xc;
  unaff_EDI[9] = uVar8 << 8 | uVar8 >> 0x18;
  *(bool *)(unaff_EDI + 0xb) = (uVar2 & 4) != 0;
  *(bool *)((int)unaff_EDI + 0x2d) = (uVar2 & 2) != 0;
  if (iVar6 == 0) {
    uVar8 = 0xffffffff;
  }
  else {
    uVar2 = FUN_005847b0();
    if (uVar2 == 0) {
      uVar2 = FUN_005847d0();
    }
    uVar8 = (uint)uVar2;
  }
  unaff_EDI[0xe] = uVar8;
  if (iVar6 == 0) {
    uVar7 = 0xffffffff;
  }
  unaff_EDI[0xc] = uVar7;
  if (iVar6 != 0) {
    uVar7 = FUN_00afd390();
    unaff_EDI[0xd] = uVar7;
    return 1;
  }
  unaff_EDI[0xd] = 0xffffffff;
  return 0xffffff01;
}

