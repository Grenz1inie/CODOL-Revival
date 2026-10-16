// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.items
// Analyst label: 库存刷新完成回调
// VA: 0x004a6c10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_004a6c10(int param_1,undefined4 param_2)

{
  undefined4 *puVar1;
  undefined4 *puVar2;
  int iVar3;
  undefined4 uVar4;
  
  DAT_07817df2 = 0;
  if (DAT_07817df3 == '\0') {
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
    uVar4 = FUN_00a44cb0();
    func_0x004a6cc0(param_2,uVar4);
    puVar2 = _DAT_07a336c4;
    if (*(int *)(param_1 + 0x1c) == 0) {
      while (puVar2 != (undefined4 *)0x0) {
        puVar1 = (undefined4 *)puVar2[1];
        (**(code **)(*(int *)*puVar2 + 0xc))(param_2,0x7bec448,_DAT_07817ddc);
        puVar2 = puVar1;
      }
    }
    return;
  }
  DAT_07817df3 = 0;
  FUN_004a6b10();
  return;
}

