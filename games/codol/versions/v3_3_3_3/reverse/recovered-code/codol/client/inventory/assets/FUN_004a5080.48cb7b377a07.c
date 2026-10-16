// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 资产获取重试回调与远程任务替换
// VA: 0x004a5080; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-retry.json
// BEGIN PSEUDOCODE

void FUN_004a5080(undefined4 param_1)

{
  int iVar1;
  undefined4 *puVar2;
  undefined4 *puStack_8;
  
  iVar1 = func_0x006fed10();
  if (iVar1 != 0) {
    iVar1 = func_0x00a3c920();
    if (iVar1 == 2) {
      iVar1 = func_0x00a421e0(&UNK_00c4e869);
      if (iVar1 != 0) {
        func_0x00a472b0(&puStack_8,0x7bdc6f8);
        if (puStack_8 != (undefined4 *)0x0) {
          puVar2 = puStack_8;
          if (puStack_8 != (undefined4 *)0x0) {
            InterlockedIncrement(puStack_8 + 1);
          }
          func_0x006f60d0(puVar2,param_1);
          if (puStack_8 != (undefined4 *)0x0) {
            iVar1 = InterlockedDecrement(puStack_8 + 1);
            if ((iVar1 == 0) && (puStack_8 != (undefined4 *)0x0)) {
              (**(code **)*puStack_8)(1);
            }
          }
        }
      }
    }
  }
  return;
}

