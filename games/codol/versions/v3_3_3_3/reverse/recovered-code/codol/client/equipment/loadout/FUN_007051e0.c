// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.loadout
// Analyst label: 当前角色和套装组合索引读取
// VA: 0x007051e0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_007051e0(void)

{
  int iVar1;
  int iVar2;
  undefined *puStack_14;
  int iStack_10;
  undefined4 uStack_c;
  
  iVar2 = _DAT_078a046c;
  if (_DAT_00cd7e3c == -1) {
    puStack_14 = &UNK_00c78550;
    iStack_10 = func_0x006da140();
    iStack_10 = iStack_10 + 0x90;
    uStack_c = 0x7ffc;
    _DAT_00cd7e3c = func_0x00592930(&puStack_14);
    if (_DAT_00cd7e3c < 0) {
      _DAT_00cd7e3c = 0;
    }
  }
  iVar1 = _DAT_00cd7e3c;
  if (_DAT_00cd7e3c == -1) {
    iVar1 = func_0x0068a0e0();
  }
  if (iVar2 == -1) {
    iVar2 = _DAT_078a046c;
  }
  return iVar2 + iVar1 * 5;
}

