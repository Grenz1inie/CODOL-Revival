// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.loadout
// Analyst label: WL_EquipWeapon 注册入口
// VA: 0x006b7740; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/loadout.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006b7740(void)

{
  undefined4 *puVar1;
  int unaff_EDI;
  undefined1 auStack_28 [8];
  int *piStack_20;
  uint uStack_1c;
  undefined4 uStack_18;
  
  piStack_20 = (int *)0x0;
  uStack_1c = 0;
  puVar1 = (undefined4 *)(**(code **)(*_DAT_00cee208 + 0x28))(8,0);
  if (puVar1 == (undefined4 *)0x0) {
    puVar1 = (undefined4 *)0x0;
  }
  else {
    *puVar1 = &UNK_00c6d28c;
    puVar1[1] = 1;
    *puVar1 = &UNK_00c7bc4c;
  }
  func_0x00719d50(auStack_28,puVar1,0);
  if ((uStack_1c & 0x8f) != 0) {
    (**(code **)(**(int **)(unaff_EDI + 8) + 0x14))
              (*(undefined4 *)(unaff_EDI + 0x10),&UNK_00c7b964,auStack_28,
               ((byte)*(undefined4 *)(unaff_EDI + 0xc) & 0x8f) == 10);
  }
  if (puVar1 != (undefined4 *)0x0) {
    func_0x009724b0();
  }
  if ((uStack_1c >> 6 & 1) != 0) {
    (**(code **)(*piStack_20 + 8))(auStack_28,uStack_18);
  }
  return;
}

