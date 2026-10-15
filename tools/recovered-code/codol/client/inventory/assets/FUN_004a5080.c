// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 资产获取重试回调与远程任务替换
// VA: 0x004a5080; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_753b822071512c172aea6e1d3b587980eb2e1da9998b38c837defd2598498d7d
// BEGIN PSEUDOCODE

void FUN_004a5080(undefined4 param_1)

{
  int iVar1;
  LONG LVar2;
  undefined4 *puVar3;
  undefined4 *local_8;
  
  iVar1 = FUN_006fed10();
  if (iVar1 != 0) {
    iVar1 = FUN_00a3c920();
    if (iVar1 == 2) {
      iVar1 = FUN_00a421e0(&DAT_00c4e869);
      if (iVar1 != 0) {
        FUN_00a472b0(&local_8,&DAT_07bdc6f8);
        if (local_8 != (undefined4 *)0x0) {
          puVar3 = local_8;
          if (local_8 != (undefined4 *)0x0) {
            InterlockedIncrement(local_8 + 1);
          }
          FUN_006f60d0(puVar3,param_1);
          if (local_8 != (undefined4 *)0x0) {
            LVar2 = InterlockedDecrement(local_8 + 1);
            if ((LVar2 == 0) && (local_8 != (undefined4 *)0x0)) {
              (**(code **)*local_8)(1);
            }
          }
        }
      }
    }
  }
  return;
}

