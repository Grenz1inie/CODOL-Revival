// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: WL_EquipWeaponAttachment 配件装备回调
// VA: 0x006b43c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006b43c0(int param_1)

{
  char cVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  char cVar5;
  int iVar6;
  uint uVar7;
  int iVar8;
  char *pcVar9;
  int iVar10;
  
  iVar4 = _DAT_078a0474;
  iVar3 = _DAT_078a0470;
  iVar6 = *(int *)(param_1 + 0x10);
  iVar2 = *(int *)(iVar6 + 0x10);
  if (*(char *)(iVar6 + 0x50) == '\0') {
    FUN_006c2090(iVar2,_DAT_078a0470,_DAT_078a0474,*(undefined1 *)(iVar6 + 0x30));
    func_0x00699de0();
    return;
  }
  if (*(char *)(iVar6 + 0x70) != '\0') {
    if ((iVar2 == 0) || (iVar6 = func_0x005845b0(), iVar6 == 0)) {
      cVar1 = '\x10';
    }
    else {
      cVar1 = *(char *)(iVar6 + 6);
    }
    iVar10 = 0;
    iVar6 = iVar3 * 0x3c;
    pcVar9 = (char *)(iVar6 + 0x78a0484);
    do {
      FUN_006bf680(iVar10);
      if ((*(char *)(iVar6 + 0x78a0478) == '\0') || (*pcVar9 == '\0')) {
        uVar7 = 0;
      }
      else {
        uVar7 = (*(uint *)(pcVar9 + 4) ^ _DAT_00cd64c0) << 8 |
                (*(uint *)(pcVar9 + 4) ^ _DAT_00cd64c0) >> 0x18;
      }
      if ((iVar10 != iVar4) && (uVar7 != 0)) {
        iVar8 = func_0x005845b0();
        if (iVar8 == 0) {
          cVar5 = '\x10';
        }
        else {
          cVar5 = *(char *)(iVar8 + 6);
        }
        if ((cVar1 == cVar5) && (*(char *)(iVar6 + 0x78a0478) != '\0')) {
          pcVar9[4] = '\0';
          pcVar9[5] = '\0';
          pcVar9[6] = '\0';
          pcVar9[7] = '\0';
          *pcVar9 = '\0';
        }
      }
      iVar10 = iVar10 + 1;
      pcVar9 = pcVar9 + 8;
    } while (iVar10 < 6);
  }
  iVar3 = iVar3 * 0x3c;
  if (*(char *)(iVar3 + 0x78a0478) != '\0') {
    if (0 < iVar2) {
      uVar7 = (iVar2 << 0x18 | iVar2 >> 8) ^ _DAT_00cd64c0;
      *(undefined1 *)(iVar3 + 0x78a0484 + iVar4 * 8) = 1;
      *(uint *)(iVar3 + 0x78a0488 + iVar4 * 8) = uVar7;
      func_0x00699de0();
      return;
    }
    *(undefined4 *)(iVar3 + 0x78a0488 + iVar4 * 8) = 0;
    *(undefined1 *)(iVar3 + 0x78a0484 + iVar4 * 8) = 0;
  }
  func_0x00699de0();
  return;
}

