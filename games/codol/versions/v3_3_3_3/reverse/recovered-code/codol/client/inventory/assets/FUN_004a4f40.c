// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 权益刷新完成处理与监听通知
// VA: 0x004a4f40; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_004a4f40(int param_1,undefined4 param_2)

{
  undefined4 *puVar1;
  undefined4 *puVar2;
  int iVar3;
  
  iVar3 = func_0x006fed10();
  if (iVar3 != 0) {
    func_0x006fed10();
    iVar3 = func_0x008e7db0();
    if (iVar3 != 0) {
      func_0x006fed10();
      func_0x008e7db0();
      func_0x00a3b0a0();
    }
  }
  if (((char)param_2 != '\0') && (DAT_07817df0 == '\0')) {
    DAT_07817df0 = '\x01';
    func_0x004a4fd0();
    func_0x004a4e70(0x7be4708);
  }
  puVar2 = _DAT_07a336c4;
  if (*(int *)(param_1 + 0x1c) == 0) {
    while (puVar2 != (undefined4 *)0x0) {
      puVar1 = (undefined4 *)puVar2[1];
      (**(code **)(*(int *)*puVar2 + 0x10))(param_2);
      puVar2 = puVar1;
    }
  }
  return;
}

