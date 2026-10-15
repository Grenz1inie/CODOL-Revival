// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 远程任务状态轮询和完成标志设置
// VA: 0x006f62d0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-task-callbacks.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006f62d0(int *param_1)

{
  int *piVar1;
  int iVar2;
  uint uVar3;
  undefined4 uVar4;
  undefined *puVar5;
  undefined4 uStack_50;
  int iStack_4c;
  uint uStack_8;
  
  uStack_8 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  if (param_1[10] == 0) {
    func_0x00af6b2f();
    return;
  }
  if (_DAT_0788c760 == 0) {
    _DAT_03749354 = timeGetTime();
    QueryPerformanceCounter(&uStack_50);
    _DAT_03749468 = uStack_50;
    _DAT_0374946c = iStack_4c;
    _DAT_0788c760 = 1;
  }
  iVar2 = timeGetTime();
  uVar3 = iVar2 - _DAT_03749354;
  iStack_4c = (**(code **)(*(int *)param_1[10] + 4))();
  iVar2 = func_0x00a44cf0();
  if (iStack_4c == 1) {
    if ((uint)param_1[3] < uVar3) {
      param_1[3] = uVar3 + 10000;
    }
    func_0x00af6b2f();
    return;
  }
  if (iStack_4c == 4) {
    param_1[4] = uVar3;
    if (param_1[6] == 0) {
      piVar1 = (int *)(*param_1 * 0x28 + 0x7807410);
      *piVar1 = *piVar1 + 1;
      func_0x006f6970();
      func_0x00af6b2f();
      return;
    }
    func_0x006f58d0();
    func_0x00af6b2f();
    return;
  }
  if (iVar2 == 0) goto LAB_006f6437;
  func_0x006fee60();
  if (iVar2 == 1) {
    if (0 < _DAT_02e8cfbc) goto LAB_006f6437;
    puVar5 = &UNK_00c783a0;
    uVar4 = 2;
  }
  else {
    if (iVar2 == 0x6c) {
      func_0x006f6970();
      goto LAB_006f6437;
    }
    if ((iVar2 != 0x66) || (0 < _DAT_02e8cfbc)) goto LAB_006f6437;
    puVar5 = &UNK_00c7fad4;
    uVar4 = 0;
  }
  func_0x00597d20(uVar4,puVar5);
LAB_006f6437:
  if ((iStack_4c == 2) && (iVar2 == 0)) {
    func_0x006f6970();
    *(undefined1 *)(param_1 + 1) = 1;
  }
  func_0x00af6b2f();
  return;
}

