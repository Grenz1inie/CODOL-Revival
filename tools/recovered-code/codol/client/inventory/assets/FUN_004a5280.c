// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 资产结果与已有权益和库存的对比诊断
// VA: 0x004a5280; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_02d3506b8a815d96abaa6149290f407aae1811c1b0a5de9c4df6cd19b2025c46
// BEGIN PSEUDOCODE

void FUN_004a5280(void)

{
  uint uVar1;
  int iVar2;
  char *pcVar3;
  char *pcVar4;
  int iVar5;
  uint uVar6;
  uint uVar7;
  undefined4 *puVar8;
  int *piVar9;
  char **ppcVar10;
  undefined4 *puVar11;
  undefined4 auStack_a0 [8];
  char *apcStack_80 [4];
  undefined4 uStack_70;
  char *pcStack_6c;
  uint *puStack_68;
  uint *local_64;
  uint local_54;
  uint local_50;
  int local_4c;
  int local_48;
  int local_3c;
  int *local_34;
  int local_30;
  int *local_2c;
  int *local_28;
  undefined4 local_24;
  undefined4 local_20;
  
  if (DAT_00cd9b42 != '\0') {
    DAT_00cd9b42 = 0;
    return;
  }
  local_64 = (uint *)(uint)DAT_07f20978;
  puStack_68 = (uint *)(uint)DAT_07be4738;
  pcStack_6c = "entitlement num: %d %d";
  uStack_70 = 0x4a52bd;
  FUN_00637c60();
  puVar8 = &DAT_07f20958;
  ppcVar10 = apcStack_80;
  for (iVar5 = 8; iVar5 != 0; iVar5 = iVar5 + -1) {
    *ppcVar10 = (char *)*puVar8;
    puVar8 = puVar8 + 1;
    ppcVar10 = ppcVar10 + 1;
  }
  puVar8 = &DAT_07be4718;
  puVar11 = auStack_a0;
  for (iVar5 = 8; iVar5 != 0; iVar5 = iVar5 + -1) {
    *puVar11 = *puVar8;
    puVar8 = puVar8 + 1;
    puVar11 = puVar11 + 1;
  }
  FUN_00637c60("entitlement player id: %llu %llu");
  local_64 = &DAT_07f20958;
  puStack_68 = (uint *)0x4a52fb;
  FUN_00a45630();
  local_34 = &local_30;
  uVar7 = 0;
  iVar5 = 0;
  local_30 = 0;
  local_24 = 1;
  local_20 = 0;
  local_2c = local_34;
  local_28 = local_34;
  if (DAT_07be4738 != 0) {
    do {
      local_54 = (&DAT_07be473c)[iVar5];
      local_64 = &local_54;
      puStack_68 = (uint *)0x4a5349;
      FUN_004a7d30();
      iVar5 = iVar5 + 1;
    } while (iVar5 < (int)(uint)DAT_07be4738);
  }
  iVar5 = 0;
  if (DAT_07f20978 != 0) {
    do {
      local_64 = (uint *)(&DAT_07f2097c)[iVar5];
      piVar9 = local_34;
      if (local_34 != &local_30) {
        do {
          if ((int)local_64 < *piVar9) {
            piVar9 = (int *)piVar9[1];
          }
          else {
            if ((int)local_64 <= *piVar9) break;
            piVar9 = (int *)piVar9[2];
          }
        } while (piVar9 != &local_30);
      }
      puStack_68 = (uint *)0xc65dc8;
      pcStack_6c = (char *)0x4a53ac;
      FUN_00637c60();
      iVar5 = iVar5 + 1;
    } while (iVar5 < (int)(uint)DAT_07f20978);
  }
  local_64 = (uint *)0x3f400000;
  puStack_68 = (uint *)0x4a53ce;
  FUN_006ee030();
  local_54 = 0;
  if (DAT_0783f860 != (int *)0x0) {
    pcVar4 = (char *)0x0;
    if (*DAT_0783f860 != 0) {
      if ((char *)DAT_0783f860[1] != (char *)0x0) {
        piVar9 = (int *)DAT_0783f860[4];
        do {
          if (*piVar9 != 0) break;
          pcVar4 = pcVar4 + 1;
          piVar9 = piVar9 + 1;
        } while (pcVar4 < (char *)DAT_0783f860[1]);
      }
      pcVar4 = *(char **)(DAT_0783f860[4] + (int)pcVar4 * 4);
    }
    while (pcVar3 = pcVar4, pcVar3 != (char *)0x0) {
      if ((DAT_0783f860 == (int *)0x0) || (*pcVar3 == '\0')) {
        local_50 = 0;
      }
      else {
        local_50 = (*(uint *)(pcVar3 + 4) ^ DAT_00cdc27c) << 8 |
                   (*(uint *)(pcVar3 + 4) ^ DAT_00cdc27c) >> 0x18;
      }
      local_64 = &local_54;
      puStack_68 = &local_50;
      pcStack_6c = (char *)0x4a5450;
      FUN_004a7940();
      local_54 = local_54 + 1;
      pcVar4 = *(char **)(pcVar3 + 0x24);
      if (*(char **)(pcVar3 + 0x24) == (char *)0x0) {
        uVar1 = DAT_0783f860[1];
        uVar6 = (uVar1 - 1 &
                ((((uint)(byte)pcVar3[0x20] * 0x1000193 ^ (uint)(byte)pcVar3[0x21]) * 0x1000193 ^
                 (uint)(byte)pcVar3[0x22]) * 0x1000193 ^ (uint)(byte)pcVar3[0x23])) + 1;
        if (uVar1 <= uVar6) break;
        piVar9 = (int *)(DAT_0783f860[4] + uVar6 * 4);
        while (*piVar9 == 0) {
          uVar6 = uVar6 + 1;
          piVar9 = piVar9 + 1;
          if (uVar1 <= uVar6) goto LAB_004a54b9;
        }
        pcVar4 = *(char **)(DAT_0783f860[4] + uVar6 * 4);
      }
    }
  }
LAB_004a54b9:
  if (DAT_07bdc9b0 != 0) {
    iVar5 = 0;
    do {
      local_64 = *(uint **)(iVar5 + 0x30 + DAT_07bdc9b4);
      if (local_4c != 0) {
        for (piVar9 = *(int **)(local_3c +
                               (local_48 - 1U &
                               (((((uint)local_64 & 0xff) * 0x1000193 ^ (uint)local_64 >> 8 & 0xff)
                                 * 0x1000193 ^ (uint)local_64 >> 0x10 & 0xff) * 0x1000193 ^
                               (uint)local_64 >> 0x18)) * 4); piVar9 != (int *)0x0;
            piVar9 = (int *)piVar9[2]) {
          if (local_64 == (uint *)piVar9[1]) goto LAB_004a5527;
        }
      }
      piVar9 = (int *)0x0;
LAB_004a5527:
      puStack_68 = (uint *)0xc65dd8;
      pcStack_6c = (char *)0x4a5532;
      local_54 = (uint)local_64;
      FUN_00637c60();
      if (((piVar9 != (int *)0x0) && (DAT_0783f860 != (int *)0x0)) &&
         (local_54 = (*piVar9 << 0x18 | *piVar9 >> 8) ^ DAT_00cdc27c, *DAT_0783f860 != 0)) {
        for (iVar2 = *(int *)(DAT_0783f860[4] +
                             (DAT_0783f860[1] - 1U &
                             ((((local_54 & 0xff) * 0x1000193 ^ local_54 >> 8 & 0xff) * 0x1000193 ^
                              local_54 >> 0x10 & 0xff) * 0x1000193 ^ local_54 >> 0x18)) * 4);
            iVar2 != 0; iVar2 = *(int *)(iVar2 + 0x24)) {
          if (local_54 == *(uint *)(iVar2 + 0x20)) {
            local_64 = *(uint **)(iVar5 + 0x34 + DAT_07bdc9b4);
            puStack_68 = *(uint **)(iVar2 + 8);
            pcStack_6c = "item count: %d %d";
            uStack_70 = 0x4a55cf;
            FUN_00637c60();
            uStack_70 = *(undefined4 *)(iVar5 + 0x38 + DAT_07bdc9b4);
            apcStack_80[3] = *(char **)(iVar2 + 0x18);
            apcStack_80[2] = "item xp: %d %d";
            apcStack_80[1] = (char *)0x4a55e7;
            FUN_00637c60();
            break;
          }
        }
      }
      uVar7 = uVar7 + 1;
      iVar5 = iVar5 + 0xa8;
    } while (uVar7 < DAT_07bdc9b0);
  }
  local_64 = (uint *)&local_4c;
  puStack_68 = (uint *)0x4a5607;
  FUN_004a7bf0();
  local_64 = (uint *)local_3c;
  puStack_68 = (uint *)0x4a5611;
  FUN_00a38040();
  piVar9 = local_34;
  if (local_34 != &local_30) {
    local_64 = (uint *)local_34[1];
    puStack_68 = (uint *)0x4a562f;
    FUN_004a8020();
    local_64 = (uint *)piVar9[2];
    puStack_68 = (uint *)0x4a563c;
    FUN_004a8020();
    local_64 = (uint *)piVar9;
    puStack_68 = (uint *)0x4a5642;
    FUN_00a38040();
  }
  return;
}

