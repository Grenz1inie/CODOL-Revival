// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 登录资产结果转移到余额和库存缓存
// VA: 0x004a5680; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_843b7d460f215fcaa37cea103b937dc06164cd073609b4c60ff575136facc2d0
// BEGIN PSEUDOCODE

void FUN_004a5680(int param_1,undefined4 param_2)

{
  int iVar1;
  undefined4 *puVar2;
  undefined4 *puVar3;
  uint uVar4;
  undefined *puVar5;
  uint local_c;
  uint local_8;
  
  if ((char)param_2 != '\0') {
    iVar1 = *(int *)(param_1 + 0x38);
    FUN_00a4c3d0();
    if (DAT_07bdc728 != 0) {
      *(undefined1 *)(iVar1 + 0x10) = DAT_07bdc760;
      *(undefined4 *)(iVar1 + 0x14) = DAT_07bdc764;
    }
    DAT_07817dd6 = 0;
    DAT_07817dd7 = 0;
    FUN_00a38580();
    FUN_004a5280();
    puVar3 = DAT_07a336c4;
    while (puVar3 != (undefined4 *)0x0) {
      puVar2 = (undefined4 *)*puVar3;
      puVar3 = (undefined4 *)puVar3[1];
      (**(code **)*puVar2)();
    }
    FUN_004a4f40(param_1,param_2);
    local_c = DAT_07bdc9b0;
    if (19999 < DAT_07bdc9b0) {
      local_c = 20000;
    }
    puVar5 = &DAT_07bec448;
    do {
      FUN_00a4b4e0();
      puVar5 = puVar5 + 0xa8;
    } while ((int)puVar5 < 0x7f20948);
    uVar4 = 0;
    DAT_07817ddc = 0;
    local_8 = 0;
    do {
      if (local_8 < local_c) {
        FUN_004a57d0();
      }
      else {
        *(undefined4 *)((int)&DAT_07bec478 + uVar4) = 0;
      }
      local_8 = local_8 + 1;
      uVar4 = uVar4 + 0xa8;
    } while (uVar4 < 0x334500);
    FUN_004a6cc0(param_2,local_c);
    puVar3 = DAT_07a336c4;
    puVar2 = DAT_07a336c4;
    if (*(int *)(param_1 + 0x1c) == 0) {
      while (puVar2 = DAT_07a336c4, puVar3 != (undefined4 *)0x0) {
        puVar2 = (undefined4 *)puVar3[1];
        (**(code **)(*(int *)*puVar3 + 0xc))(param_2,&DAT_07bec448,DAT_07817ddc);
        puVar3 = puVar2;
      }
    }
    while (puVar2 != (undefined4 *)0x0) {
      puVar3 = (undefined4 *)puVar2[1];
      (**(code **)(*(int *)*puVar2 + 0x28))();
      puVar2 = puVar3;
    }
  }
  return;
}

