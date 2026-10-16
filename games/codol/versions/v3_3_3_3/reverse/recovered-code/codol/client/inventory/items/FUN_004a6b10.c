// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.items
// Analyst label: 库存刷新请求入口
// VA: 0x004a6b10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_a75942a23166f1ee68c25350f20abdbc15df21892b7349b4f317f76c1c3e9d4b
// BEGIN PSEUDOCODE

undefined4 FUN_004a6b10(void)

{
  int iVar1;
  LONG LVar2;
  undefined *puVar3;
  undefined4 *puVar4;
  code *pcVar5;
  code *pcVar6;
  undefined4 *local_8;
  
  if (DAT_07817df2 != '\0') {
    DAT_07817df3 = 1;
    return 1;
  }
  iVar1 = FUN_006fed10();
  if (iVar1 != 0) {
    iVar1 = FUN_00a3c920();
    if (iVar1 == 2) {
      iVar1 = FUN_00a421e0(&DAT_00c4e869);
      if (iVar1 != 0) {
        puVar3 = &DAT_07bec448;
        do {
          FUN_00a4b4e0();
          puVar3 = puVar3 + 0xa8;
        } while ((int)puVar3 < 0x7f20948);
        DAT_07817ddc = 0;
        FUN_00a468c0(&local_8,&DAT_07bec448,20000);
        if (local_8 != (undefined4 *)0x0) {
          pcVar6 = FUN_004a6a10;
          pcVar5 = FUN_004a6c10;
          puVar4 = local_8;
          if (local_8 != (undefined4 *)0x0) {
            InterlockedIncrement(local_8 + 1);
          }
          FUN_006f6070(0x58,puVar4,pcVar5,pcVar6);
          DAT_07817df2 = 1;
          if (local_8 != (undefined4 *)0x0) {
            LVar2 = InterlockedDecrement(local_8 + 1);
            if ((LVar2 == 0) && (local_8 != (undefined4 *)0x0)) {
              (**(code **)*local_8)(1);
            }
          }
          return 1;
        }
      }
    }
  }
  return 0;
}

