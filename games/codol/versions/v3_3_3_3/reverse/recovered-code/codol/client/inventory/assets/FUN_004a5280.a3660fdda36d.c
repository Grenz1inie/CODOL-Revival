// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 资产结果与已有权益和库存的对比诊断
// VA: 0x004a5280; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_004a5280(void)

{
  int iVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  undefined4 *puVar6;
  int *piVar7;
  int **ppiVar8;
  undefined4 *puVar9;
  undefined4 auStack_a0 [7];
  undefined4 uStack_84;
  int *apiStack_80 [7];
  uint uStack_64;
  int iStack_54;
  int iStack_50;
  undefined4 uStack_48;
  int iStack_44;
  undefined1 *puStack_40;
  undefined1 auStack_3c [4];
  int *piStack_38;
  int iStack_34;
  int *piStack_30;
  int *piStack_2c;
  undefined4 uStack_28;
  undefined4 uStack_24;
  
  if (DAT_00cd9b42 != '\0') {
    DAT_00cd9b42 = 0;
    return;
  }
  uStack_64 = (uint)_DAT_07f20978;
  apiStack_80[6] = (int *)(uint)_DAT_07be4738;
  apiStack_80[5] = (int *)&UNK_00c65d8c;
  apiStack_80[4] = (int *)0x4a52bd;
  func_0x00637c60();
  puVar6 = (undefined4 *)0x7f20958;
  ppiVar8 = apiStack_80;
  for (iVar3 = 8; iVar3 != 0; iVar3 = iVar3 + -1) {
    *ppiVar8 = (int *)*puVar6;
    puVar6 = puVar6 + 1;
    ppiVar8 = ppiVar8 + 1;
  }
  puVar6 = (undefined4 *)0x7be4718;
  puVar9 = auStack_a0;
  for (iVar3 = 8; iVar3 != 0; iVar3 = iVar3 + -1) {
    *puVar9 = *puVar6;
    puVar6 = puVar6 + 1;
    puVar9 = puVar9 + 1;
  }
  func_0x00637c60(&UNK_00c65da4);
  uStack_64 = 0x7f20958;
  apiStack_80[6] = (int *)0x4a52fb;
  func_0x00a45630();
  piStack_38 = &iStack_34;
  uVar5 = 0;
  iVar3 = 0;
  iStack_34 = 0;
  uStack_28 = 1;
  uStack_24 = 0;
  piStack_30 = piStack_38;
  piStack_2c = piStack_38;
  if (_DAT_07be4738 != 0) {
    do {
      apiStack_80[6] = (int *)&stack0xffffffa8;
      apiStack_80[5] = (int *)0x4a5349;
      func_0x004a7d30();
      iVar3 = iVar3 + 1;
    } while (iVar3 < (int)(uint)_DAT_07be4738);
  }
  iVar3 = 0;
  if (_DAT_07f20978 != 0) {
    do {
      apiStack_80[6] = *(int **)(iVar3 * 4 + 0x7f2097c);
      piVar7 = piStack_38;
      if (piStack_38 != &iStack_34) {
        do {
          if ((int)apiStack_80[6] < *piVar7) {
            piVar7 = (int *)piVar7[1];
          }
          else {
            if ((int)apiStack_80[6] <= *piVar7) break;
            piVar7 = (int *)piVar7[2];
          }
        } while (piVar7 != &iStack_34);
      }
      apiStack_80[5] = (int *)&UNK_00c65dc8;
      apiStack_80[4] = (int *)0x4a53ac;
      func_0x00637c60();
      iVar3 = iVar3 + 1;
    } while (iVar3 < (int)(uint)_DAT_07f20978);
  }
  apiStack_80[6] = (int *)0x3f400000;
  apiStack_80[5] = (int *)0x4a53ce;
  func_0x006ee030();
  if (_DAT_0783f860 != (int *)0x0) {
    uVar2 = 0;
    if (*_DAT_0783f860 != 0) {
      if (_DAT_0783f860[1] != 0) {
        piVar7 = (int *)_DAT_0783f860[4];
        do {
          if (*piVar7 != 0) break;
          uVar2 = uVar2 + 1;
          piVar7 = piVar7 + 1;
        } while (uVar2 < (uint)_DAT_0783f860[1]);
      }
      uVar2 = *(uint *)(_DAT_0783f860[4] + uVar2 * 4);
    }
    while (uVar4 = uVar2, uVar4 != 0) {
      apiStack_80[5] = (int *)&stack0xffffffa4;
      apiStack_80[4] = (int *)&stack0xffffffa8;
      apiStack_80[3] = (int *)0x4a5450;
      func_0x004a7940();
      uVar2 = *(uint *)(uVar4 + 0x24);
      if (*(uint *)(uVar4 + 0x24) == 0) {
        uVar2 = _DAT_0783f860[1];
        uVar4 = (uVar2 - 1 &
                ((((uint)*(byte *)(uVar4 + 0x20) * 0x1000193 ^ (uint)*(byte *)(uVar4 + 0x21)) *
                  0x1000193 ^ (uint)*(byte *)(uVar4 + 0x22)) * 0x1000193 ^
                (uint)*(byte *)(uVar4 + 0x23))) + 1;
        if (uVar2 <= uVar4) break;
        piVar7 = (int *)(_DAT_0783f860[4] + uVar4 * 4);
        while (*piVar7 == 0) {
          uVar4 = uVar4 + 1;
          piVar7 = piVar7 + 1;
          if (uVar2 <= uVar4) goto LAB_004a54b9;
        }
        uVar2 = *(uint *)(_DAT_0783f860[4] + uVar4 * 4);
      }
    }
  }
LAB_004a54b9:
  if (_DAT_07bdc9b0 != 0) {
    iVar3 = 0;
    do {
      apiStack_80[5] = *(int **)(iVar3 + 0x30 + _DAT_07bdc9b4);
      if (iStack_54 != 0) {
        for (piVar7 = *(int **)(iStack_44 +
                               (iStack_50 - 1U &
                               (((((uint)apiStack_80[5] & 0xff) * 0x1000193 ^
                                 (uint)apiStack_80[5] >> 8 & 0xff) * 0x1000193 ^
                                (uint)apiStack_80[5] >> 0x10 & 0xff) * 0x1000193 ^
                               (uint)apiStack_80[5] >> 0x18)) * 4); piVar7 != (int *)0x0;
            piVar7 = (int *)piVar7[2]) {
          if (apiStack_80[5] == (int *)piVar7[1]) goto LAB_004a5527;
        }
      }
      piVar7 = (int *)0x0;
LAB_004a5527:
      apiStack_80[4] = (int *)&UNK_00c65dd8;
      apiStack_80[3] = (int *)0x4a5532;
      func_0x00637c60();
      if (((piVar7 != (int *)0x0) && (_DAT_0783f860 != (int *)0x0)) &&
         (uVar2 = (*piVar7 << 0x18 | *piVar7 >> 8) ^ _DAT_00cdc27c, *_DAT_0783f860 != 0)) {
        for (iVar1 = *(int *)(_DAT_0783f860[4] +
                             (_DAT_0783f860[1] - 1U &
                             ((((uVar2 & 0xff) * 0x1000193 ^ uVar2 >> 8 & 0xff) * 0x1000193 ^
                              uVar2 >> 0x10 & 0xff) * 0x1000193 ^ uVar2 >> 0x18)) * 4); iVar1 != 0;
            iVar1 = *(int *)(iVar1 + 0x24)) {
          if (uVar2 == *(uint *)(iVar1 + 0x20)) {
            apiStack_80[5] = *(int **)(iVar3 + 0x34 + _DAT_07bdc9b4);
            apiStack_80[4] = *(int **)(iVar1 + 8);
            apiStack_80[3] = (int *)&UNK_00c65de8;
            apiStack_80[2] = (int *)0x4a55cf;
            func_0x00637c60();
            apiStack_80[2] = *(int **)(iVar3 + 0x38 + _DAT_07bdc9b4);
            apiStack_80[1] = *(int **)(iVar1 + 0x18);
            apiStack_80[0] = (int *)&UNK_00c65dfc;
            uStack_84 = 0x4a55e7;
            func_0x00637c60();
            break;
          }
        }
      }
      uVar5 = uVar5 + 1;
      iVar3 = iVar3 + 0xa8;
    } while (uVar5 < _DAT_07bdc9b0);
  }
  apiStack_80[5] = &iStack_54;
  apiStack_80[4] = (int *)0x4a5607;
  func_0x004a7bf0();
  apiStack_80[4] = (int *)uStack_48;
  apiStack_80[3] = (int *)0x4a5611;
  func_0x00a38040();
  if (puStack_40 != auStack_3c) {
    apiStack_80[4] = *(int **)(puStack_40 + 4);
    apiStack_80[3] = (int *)0x4a562f;
    func_0x004a8020();
    apiStack_80[3] = *(int **)(puStack_40 + 8);
    apiStack_80[2] = (int *)0x4a563c;
    func_0x004a8020();
    apiStack_80[2] = (int *)puStack_40;
    apiStack_80[1] = (int *)0x4a5642;
    func_0x00a38040();
  }
  return;
}

