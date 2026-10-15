// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 带上下文的客户端异步任务登记包装
// VA: 0x006f6070; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

void FUN_006f6070(undefined4 param_1,undefined4 *param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  undefined4 *puVar2;
  
  puVar2 = param_2;
  if (param_2 != (undefined4 *)0x0) {
    InterlockedIncrement(param_2 + 1);
  }
  func_0x006f5d20(param_1,puVar2,param_3,param_4);
  if (param_2 != (undefined4 *)0x0) {
    iVar1 = InterlockedDecrement(param_2 + 1);
    if ((iVar1 == 0) && (param_2 != (undefined4 *)0x0)) {
      (**(code **)*param_2)(1);
    }
  }
  return;
}

