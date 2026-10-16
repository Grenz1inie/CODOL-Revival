// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: 装备变更后的界面状态刷新
// VA: 0x00699de0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/loadout.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00699de0(void)

{
  bool bVar1;
  char cVar2;
  int iVar3;
  uint uVar4;
  int iStack_50;
  char *pcStack_4c;
  undefined1 auStack_48 [8];
  int *piStack_40;
  uint uStack_3c;
  undefined4 uStack_38;
  undefined1 auStack_28 [8];
  int *piStack_20;
  uint uStack_1c;
  undefined4 uStack_18;
  
  piStack_40 = (int *)0x0;
  uStack_3c = 0;
  if (_DAT_0c80327c != 0) {
    iVar3 = func_0x006bed90();
    func_0x00719d30(auStack_48);
    if (iVar3 != 0) {
      func_0x006bee50();
    }
  }
  if (((uStack_3c & 0x8f) == 1) || ((uStack_3c & 0x8f) == 0)) goto LAB_0069a134;
  if (DAT_037e8d90 == '\0') {
    uVar4 = 0;
  }
  else {
    uVar4 = (_DAT_037e8d94 ^ _DAT_00cd64c0) << 8 | (_DAT_037e8d94 ^ _DAT_00cd64c0) >> 0x18;
  }
  iStack_50 = 0;
  if (uVar4 == 0) {
LAB_00699e6a:
    bVar1 = false;
  }
  else {
    cVar2 = func_0x00696640();
    bVar1 = true;
    if (cVar2 != '\0') goto LAB_00699e6a;
  }
  pcStack_4c = &DAT_037e8d90;
  do {
    if (((*pcStack_4c != '\0') &&
        (0 < (int)((*(uint *)(pcStack_4c + 4) ^ _DAT_00cd64c0) << 8 |
                  (*(uint *)(pcStack_4c + 4) ^ _DAT_00cd64c0) >> 0x18))) &&
       ((cVar2 = func_0x00696640(), cVar2 == '\0' || (bVar1)))) {
      piStack_20 = (int *)0x0;
      uStack_1c = 0;
      if (_DAT_0c80327c != 0) {
        iVar3 = func_0x006bed90();
        func_0x00719d10(auStack_28,&UNK_00c71a48,0,0);
        if (iVar3 != 0) {
          func_0x006bee50();
        }
      }
      func_0x006945a0(0);
      (**(code **)(*piStack_40 + 0x3c))(uStack_38,auStack_28);
      iStack_50 = iStack_50 + 1;
      if ((uStack_1c >> 6 & 1) != 0) {
        (**(code **)(*piStack_20 + 8))(auStack_28,uStack_18);
      }
    }
    pcStack_4c = pcStack_4c + 8;
  } while ((int)pcStack_4c < 0x37e8df0);
  if ((0 < _DAT_0788c7c0) && (iStack_50 == 0)) {
    func_0x0068a0e0();
    func_0x00688d10();
  }
  _DAT_0788c7c0 = iStack_50;
  iVar3 = _DAT_078a0470 * 0x3c;
  if ((((*(char *)(iVar3 + 0x78a0478) != '\0') && (*(char *)(iVar3 + 0x78a047c) != '\0')) &&
      (uVar4 = *(uint *)(iVar3 + 0x78a0480) ^ _DAT_00cd64c0, 0 < (int)(uVar4 << 8 | uVar4 >> 0x18)))
     && (cVar2 = func_0x00696640(), cVar2 == '\0')) {
    piStack_20 = (int *)0x0;
    uStack_1c = 0;
    if (_DAT_0c80327c != 0) {
      iVar3 = func_0x006bed90();
      func_0x00719d10(auStack_28,&UNK_00c71a48,0,0);
      if (iVar3 != 0) {
        func_0x006bee50();
      }
    }
    func_0x006945a0(0);
    (**(code **)(*piStack_40 + 0x3c))(uStack_38,auStack_28);
    if ((uStack_1c >> 6 & 1) != 0) {
      (**(code **)(*piStack_20 + 8))(auStack_28,uStack_18);
    }
  }
  pcStack_4c = (char *)0x0;
  do {
    iVar3 = _DAT_078a0470 * 0x3c;
    if (((*(char *)(iVar3 + 0x78a0478) != '\0') &&
        (*(char *)((int)pcStack_4c + 0x78a0484 + iVar3) != '\0')) &&
       ((uVar4 = *(uint *)((int)pcStack_4c + 0x78a0488 + iVar3) ^ _DAT_00cd64c0,
        0 < (int)(uVar4 << 8 | uVar4 >> 0x18) && (cVar2 = func_0x00696640(), cVar2 == '\0')))) {
      piStack_20 = (int *)0x0;
      uStack_1c = 0;
      if (_DAT_0c80327c != 0) {
        iVar3 = func_0x006bed90();
        func_0x00719d10(auStack_28,&UNK_00c71a48,0,0);
        if (iVar3 != 0) {
          func_0x006bee50();
        }
      }
      func_0x006945a0(0);
      (**(code **)(*piStack_40 + 0x3c))(uStack_38,auStack_28);
      if ((uStack_1c >> 6 & 1) != 0) {
        (**(code **)(*piStack_20 + 8))(auStack_28,uStack_18);
      }
    }
    pcStack_4c = (char *)((int)pcStack_4c + 8);
  } while ((int)pcStack_4c < 0x30);
  func_0x005ea5c0(&UNK_00c78ee4,0,auStack_48,1);
LAB_0069a134:
  if ((uStack_3c >> 6 & 1) != 0) {
    (**(code **)(*piStack_40 + 8))(auStack_48,uStack_38);
  }
  return;
}

