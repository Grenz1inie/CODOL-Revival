// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.purchase
// Analyst label: 购买完成回调分派
// VA: 0x004a6940; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_4265e1a8b42fc9000850e9b2a9b52acd95009f5329516c59df17fc469143e1e4
// BEGIN PSEUDOCODE

void FUN_004a6940(int param_1,undefined4 param_2)

{
  int *piVar1;
  undefined4 *puVar2;
  int iVar3;
  undefined4 uVar4;
  
  puVar2 = DAT_07a336c4;
  while (puVar2 != (undefined4 *)0x0) {
    piVar1 = (int *)*puVar2;
    puVar2 = (undefined4 *)puVar2[1];
    iVar3 = *piVar1;
    uVar4 = FUN_00a44cf0(*(undefined1 *)(param_1 + 5));
    (**(code **)(iVar3 + 0x14))(param_2,uVar4);
  }
  return;
}

