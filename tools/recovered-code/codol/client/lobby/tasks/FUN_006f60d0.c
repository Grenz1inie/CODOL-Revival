// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 按任务类型转发远程任务引用
// VA: 0x006f60d0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

void FUN_006f60d0(undefined4 *param_1)

{
  int in_EAX;
  int iVar1;
  undefined4 *puVar2;
  
  iVar1 = *(int *)(in_EAX * 8 + 0xcd686c) * 0x10 + 0xce6028;
  puVar2 = param_1;
  if (param_1 != (undefined4 *)0x0) {
    InterlockedIncrement(param_1 + 1);
  }
  func_0x006f6130(puVar2,iVar1);
  if (param_1 != (undefined4 *)0x0) {
    iVar1 = InterlockedDecrement(param_1 + 1);
    if ((iVar1 == 0) && (param_1 != (undefined4 *)0x0)) {
      (**(code **)*param_1)(1);
    }
  }
  return;
}

