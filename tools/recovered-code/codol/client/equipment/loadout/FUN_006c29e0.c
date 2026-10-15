// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.loadout
// Analyst label: 按类别清除冲突装备并提交变更
// VA: 0x006c29e0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_006c29e0(int param_1)

{
  int iVar1;
  int iVar2;
  uint uVar3;
  
  if (param_1 == -1) {
    param_1 = FUN_007051e0();
  }
  iVar1 = func_0x006c2780();
  if (iVar1 != 3) {
    iVar2 = func_0x00706760();
    if (iVar2 == 0) {
      func_0x006c2680();
    }
    else if (iVar2 == 1) {
      func_0x006c2680();
    }
    else if (iVar2 == 2) {
      func_0x006c2680();
    }
    else if (iVar2 == 3) {
      iVar2 = param_1;
      if (param_1 == -1) {
        iVar2 = FUN_007051e0();
      }
      if (iVar2 == -1) {
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
      if ((0 < _DAT_077ea4ec) && (iVar2 = func_0x00707b70(), iVar2 == 0)) {
        func_0x006c1ff0(param_1);
      }
    }
    else if (iVar2 == 4) {
      iVar2 = param_1;
      if (param_1 == -1) {
        iVar2 = FUN_007051e0();
      }
      if (iVar2 == -1) {
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
      if (0 < _DAT_077ea504) {
        func_0x006c22e0(param_1,_DAT_077ea504,0);
      }
    }
    else if (iVar2 == 5) {
      iVar2 = param_1;
      if (param_1 == -1) {
        iVar2 = FUN_007051e0();
      }
      if (iVar2 == -1) {
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
      if (0 < _DAT_077ea500) {
        func_0x006c22e0(param_1,_DAT_077ea500,1);
      }
    }
    else if (iVar2 == 6) {
      iVar2 = func_0x006c2eb0();
      if (((iVar2 != 0) && (iVar2 = func_0x005845b0(), iVar2 != 0)) &&
         (*(char *)(iVar2 + 6) == '\x02')) {
        func_0x006c2e10();
      }
    }
    else if (((iVar2 == 7) && (iVar2 = func_0x006c2eb0(), iVar2 != 0)) &&
            ((iVar2 = func_0x005845b0(), iVar2 != 0 && (*(char *)(iVar2 + 6) == '\0')))) {
      if (*(char *)(param_1 * 0x70 + 0x2e88f3b) == '\0') {
        uVar3 = 0;
      }
      else {
        uVar3 = *(uint *)(param_1 * 0x70 + 0x2e88f7c) ^ _DAT_00cdd280;
        uVar3 = uVar3 << 8 | uVar3 >> 0x18;
      }
      if (uVar3 == 1) {
        func_0x006c2fb0(1);
      }
    }
    param_1 = param_1 * 0x70;
    *(undefined1 *)(param_1 + 0x2e88f84) = 1;
    *(undefined4 *)(param_1 + 0x2e88f58 + iVar1 * 4) = 0;
    *(undefined1 *)(param_1 + 0x2e88f32 + iVar1) = 0;
    func_0x00594e90();
    return 1;
  }
  return 0;
}

