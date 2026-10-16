// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.currency
// Analyst label: 点券结果处理入口
// VA: 0x004a4890; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_7ad9c9ea3911405e75eb46fbce016bfbfb626c976948c5b9146a231598bd19b7
// BEGIN PSEUDOCODE

void FUN_004a4890(int param_1)

{
  int iVar1;
  LONG LVar2;
  undefined4 *puVar3;
  undefined4 *local_8;
  
  iVar1 = FUN_006fed10();
  if (iVar1 != 0) {
    iVar1 = FUN_00a3c920();
    if (iVar1 == 2) {
      iVar1 = FUN_00a42310(&DAT_00c4e869);
      if (iVar1 != 0) {
        FUN_00a4bfc0(&local_8,*(undefined4 *)(param_1 + 0x38),1);
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

