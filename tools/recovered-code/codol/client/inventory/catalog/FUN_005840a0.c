// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.catalog
// Analyst label: 目录编码值读取
// VA: 0x005840a0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_860fdb44634ad29d5b9f4076fbc37465564984da32578ddb353111cf14a85ad4
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_005840a0(void)

{
  uint *puVar1;
  ushort uVar2;
  BOOL BVar3;
  int *piVar4;
  ushort *puVar5;
  uint *puVar6;
  ushort *puVar7;
  int iVar8;
  uint uVar9;
  int local_48;
  ushort local_44;
  ushort local_40;
  ushort local_3c;
  ushort local_38;
  ushort local_34;
  ushort local_30;
  uint local_2c;
  uint local_28;
  ushort local_24;
  ushort local_20;
  ushort local_1c;
  ushort local_18;
  ushort local_14;
  ushort local_10;
  ushort local_c;
  uint local_8;
  
  local_8 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  if (DAT_07817b6c == '\0') {
    CryptAcquireContextA(&DAT_017c6f80,(LPCSTR)0x0,(LPCSTR)0x0,1,0xf0000000);
    DAT_07817b6c = '\x01';
  }
  BVar3 = CryptGenRandom(DAT_017c6f80,0x40,(BYTE *)&local_48);
  if ((BVar3 == 0) || (local_48 == 0)) {
    FUN_00a367e0();
    FUN_00a36790(&local_48,0x40);
    FUN_00a53d80();
  }
  DAT_00cdd580 = local_44;
  DAT_00cdd584 = local_40;
  DAT_00cdd588 = local_3c;
  DAT_00cdd58c = local_38;
  _DAT_00cdd590 = local_34;
  _DAT_00cdd598 = local_2c;
  _DAT_00cdd59c = local_28;
  _DAT_00cdd594 = local_30;
  _DAT_00cdd5a8 = local_1c;
  DAT_00cdd5ac._0_2_ = local_18;
  DAT_00cdd5a4 = local_20;
  _DAT_00cdd5b4 = local_10;
  _DAT_00cdd5b8 = local_c;
  _DAT_00cdd57c = (ushort)local_48;
  DAT_00cdd5a0 = local_24;
  _DAT_00cdd5b0 = local_14;
  iVar8 = 0x40;
  piVar4 = &local_48;
  do {
    *(undefined1 *)piVar4 = 0;
    piVar4 = (int *)((int)piVar4 + 1);
    iVar8 = iVar8 + -1;
  } while (iVar8 != 0);
  uVar9 = 0;
  if (DAT_02dbb28c != 0) {
    iVar8 = 0;
    do {
      puVar5 = (ushort *)(DAT_02dbb288 + iVar8);
      uVar9 = uVar9 + 1;
      iVar8 = iVar8 + 0x18;
      uVar2 = (ushort)puVar5;
      *puVar5 = (*puVar5 >> 4 | *puVar5 << 0xc) ^ uVar2 ^ (ushort)local_48;
      puVar5[1] = (puVar5[1] >> 4 | puVar5[1] << 0xc) ^ uVar2 + 2 ^ DAT_00cdd580;
      puVar5[2] = (puVar5[2] >> 4 | puVar5[2] << 0xc) ^ uVar2 + 4 ^ DAT_00cdd584;
      puVar5[3] = (puVar5[3] >> 4 | puVar5[3] << 0xc) ^ uVar2 + 6 ^ DAT_00cdd588;
      puVar5[4] = (puVar5[4] >> 4 | puVar5[4] << 0xc) ^ uVar2 + 8 ^ DAT_00cdd58c;
      puVar5[5] = (puVar5[5] >> 4 | puVar5[5] << 0xc) ^ uVar2 + 10 ^ _DAT_00cdd590;
      puVar1 = (uint *)(puVar5 + 8);
      puVar5[6] = (puVar5[6] >> 4 | puVar5[6] << 0xc) ^ uVar2 + 0xc ^ _DAT_00cdd594;
      puVar6 = (uint *)(puVar5 + 10);
      *puVar1 = (*puVar1 >> 8 | *puVar1 << 0x18) ^ (uint)puVar1 ^ _DAT_00cdd598;
      *puVar6 = (*puVar6 >> 8 | *puVar6 << 0x18) ^ (uint)puVar6 ^ _DAT_00cdd59c;
    } while (uVar9 < DAT_02dbb28c);
  }
  uVar2 = DAT_00cdd5a0;
  uVar9 = 0;
  if (DAT_02db8ac8 != 0) {
    iVar8 = 0;
    do {
      puVar5 = (ushort *)(DAT_02db8ac4 + iVar8);
      puVar7 = (ushort *)(DAT_02db8ac4 + iVar8);
      uVar9 = uVar9 + 1;
      iVar8 = iVar8 + 0x28;
      *puVar7 = (*puVar5 >> 4 | *puVar5 << 0xc) ^ (ushort)puVar7 ^ uVar2;
    } while (uVar9 < DAT_02db8ac8);
  }
  uVar9 = 0;
  if (DAT_02dbba30 != 0) {
    iVar8 = 0;
    do {
      puVar5 = (ushort *)(DAT_02dbba2c + iVar8);
      puVar7 = (ushort *)(DAT_02dbba2c + iVar8);
      uVar9 = uVar9 + 1;
      iVar8 = iVar8 + 0x4c;
      *puVar7 = (*puVar5 >> 4 | *puVar5 << 0xc) ^ (ushort)puVar7 ^ DAT_00cdd5a4;
    } while (uVar9 < DAT_02dbba30);
  }
  uVar9 = 0;
  if (DAT_02dbba38 != 0) {
    iVar8 = 0;
    do {
      puVar5 = (ushort *)(DAT_02dbba34 + iVar8);
      puVar7 = (ushort *)(DAT_02dbba34 + iVar8);
      uVar9 = uVar9 + 1;
      iVar8 = iVar8 + 0xe;
      *puVar7 = (*puVar5 >> 4 | *puVar5 << 0xc) ^ (ushort)puVar7 ^ _DAT_00cdd5a8;
      puVar7[2] = (puVar7[2] >> 4 | puVar7[2] << 0xc) ^ (ushort)puVar7 + 4 ^ (ushort)DAT_00cdd5ac;
    } while (uVar9 < DAT_02dbba38);
  }
  uVar9 = 0;
  if (DAT_02dbba40 != 0) {
    iVar8 = 0;
    do {
      puVar5 = (ushort *)(DAT_02dbba3c + iVar8);
      puVar7 = (ushort *)(DAT_02dbba3c + iVar8);
      uVar9 = uVar9 + 1;
      iVar8 = iVar8 + 0x10;
      *puVar7 = (*puVar5 >> 4 | *puVar5 << 0xc) ^ (ushort)puVar7 ^ _DAT_00cdd5b0;
    } while (uVar9 < DAT_02dbba40);
  }
  uVar9 = 0;
  if (DAT_02dbba48 != 0) {
    iVar8 = 0;
    do {
      puVar5 = (ushort *)(DAT_02dbba44 + iVar8);
      puVar7 = (ushort *)(DAT_02dbba44 + iVar8);
      uVar9 = uVar9 + 1;
      iVar8 = iVar8 + 0x28;
      *puVar7 = (*puVar5 >> 4 | *puVar5 << 0xc) ^ (ushort)puVar7 ^ _DAT_00cdd5b4;
    } while (uVar9 < DAT_02dbba48);
  }
  uVar9 = 0;
  if (DAT_02dbba50 != 0) {
    iVar8 = 0;
    do {
      puVar5 = (ushort *)(DAT_02dbba4c + iVar8);
      puVar7 = (ushort *)(DAT_02dbba4c + iVar8);
      uVar9 = uVar9 + 1;
      iVar8 = iVar8 + 0x14;
      *puVar7 = (*puVar5 >> 4 | *puVar5 << 0xc) ^ (ushort)puVar7 ^ _DAT_00cdd5b8;
    } while (uVar9 < DAT_02dbba50);
  }
  __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
  return;
}

