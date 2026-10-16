// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.items
// Analyst label: 库存刷新请求入口
// VA: 0x004a6b10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_004a6b10(void)

{
  int iVar1;
  undefined4 *puVar2;
  code *pcVar3;
  undefined *puVar4;
  undefined4 *puStack_8;
  
  if (DAT_07817df2 != '\0') {
    DAT_07817df3 = 1;
    return 1;
  }
  iVar1 = func_0x006fed10();
  if (iVar1 != 0) {
    iVar1 = func_0x00a3c920();
    if (iVar1 == 2) {
      iVar1 = func_0x00a421e0(&UNK_00c4e869);
      if (iVar1 != 0) {
        iVar1 = 0x7bec448;
        do {
          func_0x00a4b4e0();
          iVar1 = iVar1 + 0xa8;
        } while (iVar1 < 0x7f20948);
        _DAT_07817ddc = 0;
        FUN_00a468c0(&puStack_8,0x7bec448,20000);
        if (puStack_8 != (undefined4 *)0x0) {
          puVar4 = &UNK_004a6a10;
          pcVar3 = FUN_004a6c10;
          puVar2 = puStack_8;
          if (puStack_8 != (undefined4 *)0x0) {
            InterlockedIncrement(puStack_8 + 1);
          }
          FUN_006f6070(0x58,puVar2,pcVar3,puVar4);
          DAT_07817df2 = 1;
          if (puStack_8 != (undefined4 *)0x0) {
            iVar1 = InterlockedDecrement(puStack_8 + 1);
            if ((iVar1 == 0) && (puStack_8 != (undefined4 *)0x0)) {
              (**(code **)*puStack_8)(1);
            }
          }
          return 1;
        }
      }
    }
  }
  return 0;
}

