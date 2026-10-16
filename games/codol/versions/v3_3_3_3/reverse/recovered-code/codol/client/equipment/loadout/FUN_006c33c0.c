// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.loadout
// Analyst label: 装备占用计数与数量限制输入
// VA: 0x006c33c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

uint FUN_006c33c0(undefined *param_1)

{
  char cVar1;
  undefined *puVar2;
  int iVar3;
  undefined *puVar4;
  uint uVar5;
  int iVar6;
  int iVar7;
  uint uStack_54;
  int iStack_50;
  undefined *puStack_4c;
  undefined *puStack_48;
  int iStack_44;
  undefined *puStack_40;
  int iStack_3c;
  undefined *puStack_38;
  int iStack_34;
  undefined *puStack_30;
  int iStack_2c;
  undefined4 uStack_28;
  undefined4 uStack_24;
  undefined4 uStack_20;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  undefined4 uStack_10;
  undefined4 uStack_c;
  
  if (param_1 == (undefined *)0xffffffff) {
    param_1 = (undefined *)FUN_007051e0();
  }
  puVar2 = param_1;
  if (param_1 == (undefined *)0xffffffff) {
    puVar2 = (undefined *)FUN_007051e0();
  }
  if (puVar2 == (undefined *)0xffffffff) {
    FUN_007051e0();
  }
  _DAT_077ea4ec = 0;
  _DAT_077ea4fc = 0;
  _DAT_077ea500 = 0;
  _DAT_077ea504 = 0;
  _DAT_077ea508 = 0;
  _DAT_077ea50c = 0;
  _DAT_077ea510 = 0;
  func_0x005945b0(&DAT_077ea4ec);
  uStack_54 = (uint)(0 < _DAT_077ea4ec);
  puVar2 = param_1;
  if (param_1 == (undefined *)0xffffffff) {
    puVar2 = (undefined *)FUN_007051e0();
  }
  if (puVar2 == (undefined *)0xffffffff) {
    FUN_007051e0();
  }
  _DAT_077ea4ec = 0;
  _DAT_077ea4fc = 0;
  _DAT_077ea500 = 0;
  _DAT_077ea504 = 0;
  _DAT_077ea508 = 0;
  _DAT_077ea50c = 0;
  _DAT_077ea510 = 0;
  func_0x005945b0(&DAT_077ea4ec);
  if (0 < _DAT_077ea4ec) {
    uStack_54 = uStack_54 + 1;
  }
  iVar7 = 0;
  do {
    if (((iVar7 == 0) || (iVar7 == 1)) || (iVar7 == 2)) {
      puVar2 = param_1;
      if (param_1 == (undefined *)0xffffffff) {
        puVar2 = (undefined *)FUN_007051e0();
      }
      if (puVar2 == (undefined *)0xffffffff) {
        FUN_007051e0();
      }
      _DAT_077ea4ec = 0;
      _DAT_077ea4fc = 0;
      _DAT_077ea500 = 0;
      _DAT_077ea504 = 0;
      _DAT_077ea508 = 0;
      _DAT_077ea50c = 0;
      _DAT_077ea510 = 0;
      func_0x005945b0(&DAT_077ea4ec);
      if (0 < *(int *)(&DAT_077ea4fc + iVar7 * 4)) {
        uStack_54 = uStack_54 + 1;
      }
      puVar2 = param_1;
      if (param_1 == (undefined *)0xffffffff) {
        puVar2 = (undefined *)FUN_007051e0();
      }
      if (puVar2 == (undefined *)0xffffffff) {
        FUN_007051e0();
      }
      _DAT_077ea4ec = 0;
      _DAT_077ea4fc = 0;
      _DAT_077ea500 = 0;
      _DAT_077ea504 = 0;
      _DAT_077ea508 = 0;
      _DAT_077ea50c = 0;
      _DAT_077ea510 = 0;
      func_0x005945b0(&DAT_077ea4ec);
      if (0 < *(int *)(&DAT_077ea4fc + iVar7 * 4)) {
        uStack_54 = uStack_54 + 1;
      }
    }
    iVar7 = iVar7 + 1;
  } while (iVar7 < 6);
  iStack_50 = 0x28;
  iVar7 = _DAT_00cd7e3c;
  iVar6 = 3;
  do {
    puVar4 = _DAT_078a046c;
    puVar2 = param_1;
    if (param_1 == (undefined *)0xffffffff) {
      if (iVar7 == -1) {
        puStack_4c = &UNK_00c78550;
        if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
          if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
            iVar7 = func_0x00a59520();
            puStack_48 = *(undefined **)(iVar7 + 0x20);
            iStack_44 = *(int *)(iVar7 + 0x24);
          }
          if ((_DAT_0c95bd80 != puStack_48) || (_DAT_0c95bd84 != iStack_44)) {
            func_0x006d9da0(0,&puStack_48);
          }
        }
        uStack_28 = 0xc95be10;
        uStack_24 = 0x7ffc;
        iVar7 = func_0x00592930(&puStack_4c);
        if (iVar7 < 0) {
LAB_006c36f9:
          iVar7 = 0;
          _DAT_00cd7e3c = 0;
        }
        else {
          _DAT_00cd7e3c = iVar7;
          if (iVar7 == -1) {
            puStack_4c = &UNK_00c78550;
            if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
              if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
                iVar7 = func_0x00a59520();
                puStack_40 = *(undefined **)(iVar7 + 0x20);
                iStack_3c = *(int *)(iVar7 + 0x24);
              }
              if ((_DAT_0c95bd80 != puStack_40) || (_DAT_0c95bd84 != iStack_3c)) {
                func_0x006d9da0(0,&puStack_40);
              }
            }
            uStack_20 = 0xc95be10;
            uStack_1c = 0x7ffc;
            iVar7 = func_0x00592930(&puStack_4c);
            _DAT_00cd7e3c = iVar7;
            if (iVar7 < 0) goto LAB_006c36f9;
          }
        }
      }
      if (puVar4 == (undefined *)0xffffffff) {
        puVar4 = _DAT_078a046c;
      }
      puVar2 = puVar4 + iVar7 * 5;
    }
    puVar4 = _DAT_078a046c;
    iVar3 = (int)puVar2 * 0x70 + 0x2e88f18;
    cVar1 = (char)iVar6;
    if ((*(char *)(iVar6 + 0x11 + iVar3) != '\0') &&
       (uVar5 = (_DAT_00cdd280 >> (0x13U - cVar1 & 0x1f) | _DAT_00cdd280 << (cVar1 + 0xdU & 0x1f)) ^
                *(uint *)(iStack_50 + iVar3), 0 < (int)(uVar5 << 8 | uVar5 >> 0x18))) {
      uStack_54 = uStack_54 + 1;
    }
    puVar2 = param_1;
    if (param_1 == (undefined *)0xffffffff) {
      if (iVar7 == -1) {
        puStack_4c = &UNK_00c78550;
        if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
          if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
            iVar7 = func_0x00a59520();
            puStack_38 = *(undefined **)(iVar7 + 0x20);
            iStack_34 = *(int *)(iVar7 + 0x24);
          }
          if ((_DAT_0c95bd80 != puStack_38) || (_DAT_0c95bd84 != iStack_34)) {
            func_0x006d9da0(0,&puStack_38);
          }
        }
        uStack_18 = 0xc95be10;
        uStack_14 = 0x7ffc;
        iVar7 = func_0x00592930(&puStack_4c);
        if (iVar7 < 0) {
LAB_006c38aa:
          iVar7 = 0;
          _DAT_00cd7e3c = 0;
        }
        else {
          _DAT_00cd7e3c = iVar7;
          if (iVar7 == -1) {
            puStack_4c = &UNK_00c78550;
            if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
              if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
                iVar7 = func_0x00a59520();
                puStack_30 = *(undefined **)(iVar7 + 0x20);
                iStack_2c = *(int *)(iVar7 + 0x24);
              }
              if ((_DAT_0c95bd80 != puStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
                func_0x006d9da0(0,&puStack_30);
              }
            }
            uStack_10 = 0xc95be10;
            uStack_c = 0x7ffc;
            iVar7 = func_0x00592930(&puStack_4c);
            _DAT_00cd7e3c = iVar7;
            if (iVar7 < 0) goto LAB_006c38aa;
          }
        }
      }
      if (puVar4 == (undefined *)0xffffffff) {
        puVar4 = _DAT_078a046c;
      }
      puVar2 = puVar4 + iVar7 * 5;
    }
    iVar3 = (int)puVar2 * 0x70 + 0x2e88f18;
    if ((*(char *)(iVar6 + 0x14 + iVar3) != '\0') &&
       (uVar5 = (_DAT_00cdd280 >> (0x10U - cVar1 & 0x1f) | _DAT_00cdd280 << (cVar1 + 0x10U & 0x1f))
                ^ *(uint *)(iStack_50 + 0xc + iVar3), 0 < (int)(uVar5 << 8 | uVar5 >> 0x18))) {
      uStack_54 = uStack_54 + 1;
    }
    iStack_50 = iStack_50 + 4;
    iVar3 = iVar6 + -2;
    iVar6 = iVar6 + 1;
  } while (iVar3 < 3);
  iVar6 = 0;
  iStack_50 = 0x40;
  do {
    puStack_48 = param_1;
    if (param_1 == (undefined *)0xffffffff) {
      puStack_48 = _DAT_078a046c;
      if (iVar7 == -1) {
        puStack_4c = &UNK_00c78550;
        if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
          if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
            iVar7 = func_0x00a59520();
            puStack_30 = *(undefined **)(iVar7 + 0x20);
            iStack_2c = *(int *)(iVar7 + 0x24);
          }
          if ((_DAT_0c95bd80 != puStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
            func_0x006d9da0(0,&puStack_30);
          }
        }
        uStack_10 = 0xc95be10;
        uStack_c = 0x7ffc;
        iVar7 = func_0x00592930(&puStack_4c);
        if (iVar7 < 0) {
LAB_006c3a7b:
          iVar7 = 0;
          _DAT_00cd7e3c = 0;
        }
        else {
          _DAT_00cd7e3c = iVar7;
          if (iVar7 == -1) {
            puStack_4c = &UNK_00c78550;
            if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
              if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
                iVar7 = func_0x00a59520();
                puStack_38 = *(undefined **)(iVar7 + 0x20);
                iStack_34 = *(int *)(iVar7 + 0x24);
              }
              if ((_DAT_0c95bd80 != puStack_38) || (_DAT_0c95bd84 != iStack_34)) {
                func_0x006d9da0(0,&puStack_38);
              }
            }
            uStack_18 = 0xc95be10;
            uStack_14 = 0x7ffc;
            iVar7 = func_0x00592930(&puStack_4c);
            _DAT_00cd7e3c = iVar7;
            if (iVar7 < 0) goto LAB_006c3a7b;
          }
        }
      }
      if (puStack_48 == (undefined *)0xffffffff) {
        puStack_48 = _DAT_078a046c;
      }
      puStack_48 = puStack_48 + iVar7 * 5;
    }
    puVar2 = _DAT_078a046c;
    if ((*(char *)((int)puStack_48 * 0x70 + 0x2e88f32 + iVar6) != '\0') &&
       (uVar5 = (_DAT_00cdd280 >> (0x10U - (char)iVar6 & 0x1f) |
                _DAT_00cdd280 << ((char)iVar6 + 0x10U & 0x1f)) ^
                *(uint *)(iStack_50 + (int)puStack_48 * 0x70 + 0x2e88f18),
       0 < (int)(uVar5 << 8 | uVar5 >> 0x18))) {
      uStack_54 = uStack_54 + 1;
    }
    iStack_50 = iStack_50 + 4;
    iVar6 = iVar6 + 1;
  } while (iStack_50 < 0x4c);
  puVar4 = param_1;
  if (param_1 == (undefined *)0xffffffff) {
    if (iVar7 == -1) {
      puStack_48 = &UNK_00c78550;
      if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
        if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
          iVar7 = func_0x00a59520();
          puStack_30 = *(undefined **)(iVar7 + 0x20);
          iStack_2c = *(int *)(iVar7 + 0x24);
        }
        if ((_DAT_0c95bd80 != puStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
          func_0x006d9da0(0,&puStack_30);
        }
      }
      uStack_10 = 0xc95be10;
      uStack_c = 0x7ffc;
      iVar7 = func_0x00592930(&puStack_48);
      if (iVar7 < 0) {
LAB_006c3c3d:
        iVar7 = 0;
        _DAT_00cd7e3c = 0;
      }
      else {
        _DAT_00cd7e3c = iVar7;
        if (iVar7 == -1) {
          puStack_48 = &UNK_00c78550;
          if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
            if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
              iVar7 = func_0x00a59520();
              puStack_30 = *(undefined **)(iVar7 + 0x20);
              iStack_2c = *(int *)(iVar7 + 0x24);
            }
            if ((_DAT_0c95bd80 != puStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
              func_0x006d9da0(0,&puStack_30);
            }
          }
          uStack_10 = 0xc95be10;
          uStack_c = 0x7ffc;
          iVar7 = func_0x00592930(&puStack_48);
          _DAT_00cd7e3c = iVar7;
          if (iVar7 < 0) goto LAB_006c3c3d;
        }
      }
    }
    if (puVar2 == (undefined *)0xffffffff) {
      puVar2 = _DAT_078a046c;
    }
    puVar4 = puVar2 + iVar7 * 5;
  }
  puVar2 = _DAT_078a046c;
  if ((*(char *)((int)puVar4 * 0x70 + 0x2e88f38) != '\0') &&
     (uVar5 = (_DAT_00cdd280 << 0x10 | _DAT_00cdd280 >> 0x10) ^
              *(uint *)((int)puVar4 * 0x70 + 0x2e88f70), 0 < (int)(uVar5 << 8 | uVar5 >> 0x18))) {
    uStack_54 = uStack_54 + 1;
  }
  puVar4 = param_1;
  if (param_1 == (undefined *)0xffffffff) {
    if (iVar7 == -1) {
      puStack_48 = &UNK_00c78550;
      if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
        if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
          iVar7 = func_0x00a59520();
          puStack_30 = *(undefined **)(iVar7 + 0x20);
          iStack_2c = *(int *)(iVar7 + 0x24);
        }
        if ((_DAT_0c95bd80 != puStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
          func_0x006d9da0(0,&puStack_30);
        }
      }
      uStack_10 = 0xc95be10;
      uStack_c = 0x7ffc;
      iVar7 = func_0x00592930(&puStack_48);
      if (iVar7 < 0) {
LAB_006c3dd4:
        iVar7 = 0;
        _DAT_00cd7e3c = 0;
      }
      else {
        _DAT_00cd7e3c = iVar7;
        if (iVar7 == -1) {
          puStack_48 = &UNK_00c78550;
          if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
            if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
              iVar7 = func_0x00a59520();
              puStack_30 = *(undefined **)(iVar7 + 0x20);
              iStack_2c = *(int *)(iVar7 + 0x24);
            }
            if ((_DAT_0c95bd80 != puStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
              func_0x006d9da0(0,&puStack_30);
            }
          }
          uStack_10 = 0xc95be10;
          uStack_c = 0x7ffc;
          iVar7 = func_0x00592930(&puStack_48);
          _DAT_00cd7e3c = iVar7;
          if (iVar7 < 0) goto LAB_006c3dd4;
        }
      }
    }
    if (puVar2 == (undefined *)0xffffffff) {
      puVar2 = _DAT_078a046c;
    }
    puVar4 = puVar2 + iVar7 * 5;
  }
  puVar2 = _DAT_078a046c;
  if ((*(char *)((int)puVar4 * 0x70 + 0x2e88f3a) != '\0') &&
     (uVar5 = (_DAT_00cdd280 >> 0xe | _DAT_00cdd280 << 0x12) ^
              *(uint *)((int)puVar4 * 0x70 + 0x2e88f78), 0 < (int)(uVar5 << 8 | uVar5 >> 0x18))) {
    uStack_54 = uStack_54 + 1;
  }
  puVar4 = param_1;
  if (param_1 == (undefined *)0xffffffff) {
    if (iVar7 == -1) {
      puStack_48 = &UNK_00c78550;
      if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
        if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
          iVar7 = func_0x00a59520();
          puStack_30 = *(undefined **)(iVar7 + 0x20);
          iStack_2c = *(int *)(iVar7 + 0x24);
        }
        if ((_DAT_0c95bd80 != puStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
          func_0x006d9da0(0,&puStack_30);
        }
      }
      uStack_10 = 0xc95be10;
      uStack_c = 0x7ffc;
      iVar7 = func_0x00592930(&puStack_48);
      if (iVar7 < 0) {
LAB_006c3f6b:
        iVar7 = 0;
        _DAT_00cd7e3c = 0;
      }
      else {
        _DAT_00cd7e3c = iVar7;
        if (iVar7 == -1) {
          puStack_48 = &UNK_00c78550;
          if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
            if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
              iVar7 = func_0x00a59520();
              puStack_30 = *(undefined **)(iVar7 + 0x20);
              iStack_2c = *(int *)(iVar7 + 0x24);
            }
            if ((_DAT_0c95bd80 != puStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
              func_0x006d9da0(0,&puStack_30);
            }
          }
          uStack_10 = 0xc95be10;
          uStack_c = 0x7ffc;
          iVar7 = func_0x00592930(&puStack_48);
          _DAT_00cd7e3c = iVar7;
          if (iVar7 < 0) goto LAB_006c3f6b;
        }
      }
    }
    if (puVar2 == (undefined *)0xffffffff) {
      puVar2 = _DAT_078a046c;
    }
    puVar4 = puVar2 + iVar7 * 5;
  }
  puVar2 = _DAT_078a046c;
  if (*(char *)((int)puVar4 * 0x70 + 0x2e88f3b) == '\0') {
    uVar5 = 0;
  }
  else {
    uVar5 = *(uint *)((int)puVar4 * 0x70 + 0x2e88f7c) ^ _DAT_00cdd280;
    uVar5 = uVar5 << 8 | uVar5 >> 0x18;
  }
  if (uVar5 == 1) {
    uStack_54 = uStack_54 + 1;
  }
  if (param_1 != (undefined *)0xffffffff) goto LAB_006c4120;
  if (iVar7 == -1) {
    puStack_48 = &UNK_00c78550;
    if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
      if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
        iVar7 = func_0x00a59520();
        puStack_30 = *(undefined **)(iVar7 + 0x20);
        iStack_2c = *(int *)(iVar7 + 0x24);
      }
      if ((_DAT_0c95bd80 != puStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
        func_0x006d9da0(0,&puStack_30);
      }
    }
    uStack_10 = 0xc95be10;
    uStack_c = 0x7ffc;
    iVar7 = func_0x00592930(&puStack_48);
    if (iVar7 < 0) {
LAB_006c4107:
      iVar7 = 0;
      _DAT_00cd7e3c = 0;
    }
    else {
      _DAT_00cd7e3c = iVar7;
      if (iVar7 == -1) {
        puStack_48 = &UNK_00c78550;
        if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
          if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
            iVar7 = func_0x00a59520();
            puStack_30 = *(undefined **)(iVar7 + 0x20);
            iStack_2c = *(int *)(iVar7 + 0x24);
          }
          if ((_DAT_0c95bd80 != puStack_30) || (_DAT_0c95bd84 != iStack_2c)) {
            func_0x006d9da0(0,&puStack_30);
          }
        }
        uStack_10 = 0xc95be10;
        uStack_c = 0x7ffc;
        iVar7 = func_0x00592930(&puStack_48);
        _DAT_00cd7e3c = iVar7;
        if (iVar7 < 0) goto LAB_006c4107;
      }
    }
  }
  if (puVar2 == (undefined *)0xffffffff) {
    puVar2 = _DAT_078a046c;
  }
  param_1 = puVar2 + iVar7 * 5;
LAB_006c4120:
  if (*(char *)((int)param_1 * 0x70 + 0x2e88f3c) == '\0') {
    uVar5 = 0;
  }
  else {
    uVar5 = *(uint *)((int)param_1 * 0x70 + 0x2e88f80) ^ _DAT_00cdd280;
    uVar5 = uVar5 << 8 | uVar5 >> 0x18;
  }
  if (uVar5 == 1) {
    uStack_54 = uStack_54 + 1;
  }
  return uStack_54;
}

