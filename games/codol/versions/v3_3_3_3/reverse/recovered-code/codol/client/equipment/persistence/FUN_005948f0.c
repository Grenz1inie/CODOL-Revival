// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.persistence
// Analyst label: 遍历脏装备缓存并触发档案字段同步
// VA: 0x005948f0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_005948f0(void)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iStack_48;
  int iStack_44;
  int iStack_40;
  undefined *puStack_3c;
  int iStack_38;
  int iStack_34;
  int iStack_30;
  int iStack_2c;
  int iStack_28;
  int iStack_24;
  undefined4 uStack_20;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  undefined4 uStack_10;
  undefined4 uStack_c;
  
  iStack_48 = 0;
  iStack_40 = 0;
  iStack_44 = 0;
  iVar1 = _DAT_00cd7e3c;
  do {
    iVar3 = iStack_48;
    if ((iStack_48 == -1) && (iVar3 = iVar1, iVar1 == -1)) {
      puStack_3c = &UNK_00c78550;
      if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
        if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
          iVar1 = func_0x00a59520();
          iStack_38 = *(int *)(iVar1 + 0x20);
          iStack_34 = *(int *)(iVar1 + 0x24);
        }
        if ((_DAT_0c95bd80 != iStack_38) || (_DAT_0c95bd84 != iStack_34)) {
          func_0x006d9da0(0,&iStack_38);
        }
      }
      uStack_20 = 0xc95be10;
      uStack_1c = 0x7ffc;
      iVar1 = func_0x00592930(&puStack_3c);
      iVar3 = iVar1;
      _DAT_00cd7e3c = iVar1;
      if (iVar1 < 0) {
        iVar1 = 0;
        _DAT_00cd7e3c = 0;
        iVar3 = iVar1;
      }
    }
    iVar2 = _DAT_078a046c;
    iVar4 = iStack_40;
    if (iStack_40 == -1) {
      iVar4 = _DAT_078a046c;
    }
    iVar4 = iVar4 + iVar3 * 5;
    if (iVar4 == -1) {
      if (iVar1 == -1) {
        puStack_3c = &UNK_00c78550;
        if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
          if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
            iVar1 = func_0x00a59520();
            iStack_30 = *(int *)(iVar1 + 0x20);
            iStack_2c = *(int *)(iVar1 + 0x24);
          }
          if ((_DAT_0c95bd80 != iStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
            func_0x006d9da0(0,&iStack_30);
          }
        }
        uStack_18 = 0xc95be10;
        uStack_14 = 0x7ffc;
        iVar1 = func_0x00592930(&puStack_3c);
        if (iVar1 < 0) {
LAB_00594b48:
          iVar1 = 0;
          _DAT_00cd7e3c = 0;
        }
        else {
          _DAT_00cd7e3c = iVar1;
          if (iVar1 == -1) {
            puStack_3c = &UNK_00c78550;
            if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
              if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
                iVar1 = func_0x00a59520();
                iStack_28 = *(int *)(iVar1 + 0x20);
                iStack_24 = *(int *)(iVar1 + 0x24);
              }
              if ((_DAT_0c95bd80 != iStack_28) || (_DAT_0c95bd84 != iStack_24)) {
                func_0x006d9da0(0,&iStack_28);
              }
            }
            uStack_10 = 0xc95be10;
            uStack_c = 0x7ffc;
            iVar1 = func_0x00592930(&puStack_3c);
            _DAT_00cd7e3c = iVar1;
            if (iVar1 < 0) goto LAB_00594b48;
          }
        }
      }
      if (iVar2 == -1) {
        iVar2 = _DAT_078a046c;
      }
      iVar4 = iVar2 + iVar1 * 5;
    }
    iVar3 = iStack_44;
    if (iStack_44 == 2) {
      iVar3 = _DAT_078a0470;
    }
    iVar4 = iVar4 * 2;
    if (iVar3 == 1) {
      iVar4 = iVar4 + 1;
    }
    if ((*(char *)(iVar4 * 0x28 + 0x2e7405c) != '\0') &&
       (func_0x006c4240(iStack_40,iStack_44), iVar1 = _DAT_00cd7e3c,
       *(char *)(iVar4 * 0x28 + 0x2e7405c) != '\0')) {
      func_0x00592b10();
      *(undefined1 *)(iVar4 / 2 + 0x783f668) = 1;
      *(undefined1 *)(iVar4 * 0x28 + 0x2e7405c) = 0;
      iVar1 = func_0x006da140();
      if ((*(int *)(iVar1 + 0x84) == 2) || (*(int *)(iVar1 + 0x84) == 0)) {
        *(byte *)(iVar1 + 0x9095) = *(byte *)(iVar1 + 0x9095) | 1;
        *(undefined1 *)(iVar1 + 0x9094) = 1;
      }
      DAT_0783811f = 1;
      iVar1 = _DAT_00cd7e3c;
    }
    iStack_44 = iStack_44 + 1;
    if (1 < iStack_44) {
      iStack_40 = iStack_40 + 1;
      if (iStack_40 < 5) {
        iStack_44 = 0;
      }
      else {
        iStack_48 = iStack_48 + 1;
        if (0xb < iStack_48) {
          return;
        }
        iStack_40 = 0;
        iStack_44 = 0;
      }
    }
  } while( true );
}

