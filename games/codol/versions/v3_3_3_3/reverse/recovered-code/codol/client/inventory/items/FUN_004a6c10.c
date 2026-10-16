// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.items
// Analyst label: 库存刷新完成回调
// VA: 0x004a6c10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_aba63b6ab247c23295bb66f1974ff01c286eca734e7f031e47153d81c8d3b2f7
// BEGIN PSEUDOCODE

void FUN_004a6c10(int param_1,undefined4 param_2)

{
  undefined4 *puVar1;
  undefined4 *puVar2;
  int iVar3;
  undefined4 uVar4;
  
  DAT_07817df2 = 0;
  if (DAT_07817df3 == '\0') {
    iVar3 = FUN_006fed10();
    if (iVar3 != 0) {
      FUN_006fed10();
      iVar3 = FUN_008e7db0();
      if (iVar3 != 0) {
        FUN_006fed10();
        FUN_008e7db0();
        FUN_00a3b0a0();
      }
    }
    uVar4 = FUN_00a44cb0();
    FUN_004a6cc0(param_2,uVar4);
    puVar2 = DAT_07a336c4;
    if (*(int *)(param_1 + 0x1c) == 0) {
      while (puVar2 != (undefined4 *)0x0) {
        puVar1 = (undefined4 *)puVar2[1];
        (**(code **)(*(int *)*puVar2 + 0xc))(param_2,&DAT_07bec448,DAT_07817ddc);
        puVar2 = puVar1;
      }
    }
    return;
  }
  DAT_07817df3 = 0;
  FUN_004a6b10();
  return;
}

