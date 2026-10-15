// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 登录资产结果转移到余额和库存缓存
// VA: 0x004a5680; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_004a5680(int param_1,undefined4 param_2)

{
  undefined4 *puVar1;
  undefined4 *puVar2;
  uint uVar3;
  int iVar4;
  uint uStack_c;
  uint uStack_8;
  
  if ((char)param_2 != '\0') {
    iVar4 = *(int *)(param_1 + 0x38);
    func_0x00a4c3d0();
    if (_DAT_07bdc728 != 0) {
      *(undefined1 *)(iVar4 + 0x10) = DAT_07bdc760;
      *(undefined4 *)(iVar4 + 0x14) = _DAT_07bdc764;
    }
    DAT_07817dd6 = 0;
    DAT_07817dd7 = 0;
    func_0x00a38580();
    FUN_004a5280();
    puVar2 = _DAT_07a336c4;
    while (puVar2 != (undefined4 *)0x0) {
      puVar1 = (undefined4 *)*puVar2;
      puVar2 = (undefined4 *)puVar2[1];
      (**(code **)*puVar1)();
    }
    FUN_004a4f40(param_1,param_2);
    uStack_c = _DAT_07bdc9b0;
    if (19999 < _DAT_07bdc9b0) {
      uStack_c = 20000;
    }
    iVar4 = 0x7bec448;
    do {
      func_0x00a4b4e0();
      iVar4 = iVar4 + 0xa8;
    } while (iVar4 < 0x7f20948);
    uVar3 = 0;
    _DAT_07817ddc = 0;
    uStack_8 = 0;
    do {
      if (uStack_8 < uStack_c) {
        func_0x004a57d0();
      }
      else {
        *(undefined4 *)(uVar3 + 0x7bec478) = 0;
      }
      uStack_8 = uStack_8 + 1;
      uVar3 = uVar3 + 0xa8;
    } while (uVar3 < 0x334500);
    func_0x004a6cc0(param_2,uStack_c);
    puVar2 = _DAT_07a336c4;
    puVar1 = _DAT_07a336c4;
    if (*(int *)(param_1 + 0x1c) == 0) {
      while (puVar1 = _DAT_07a336c4, puVar2 != (undefined4 *)0x0) {
        puVar1 = (undefined4 *)puVar2[1];
        (**(code **)(*(int *)*puVar2 + 0xc))(param_2,0x7bec448,_DAT_07817ddc);
        puVar2 = puVar1;
      }
    }
    while (puVar1 != (undefined4 *)0x0) {
      puVar2 = (undefined4 *)puVar1[1];
      (**(code **)(*(int *)*puVar1 + 0x28))();
      puVar1 = puVar2;
    }
  }
  return;
}

