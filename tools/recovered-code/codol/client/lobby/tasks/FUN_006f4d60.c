// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 异步任务计数和耗时统计
// VA: 0x006f4d60; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-task-callbacks.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006f4d60(uint param_1)

{
  int iVar1;
  int iVar2;
  int unaff_EDI;
  undefined4 uStack_c;
  undefined4 uStack_8;
  
  iVar1 = *(int *)(unaff_EDI + 0x24) * 0x18;
  if (_DAT_0788c760 == 0) {
    _DAT_03749354 = timeGetTime();
    QueryPerformanceCounter(&uStack_c);
    _DAT_03749468 = uStack_c;
    _DAT_0374946c = uStack_8;
    _DAT_0788c760 = 1;
  }
  iVar2 = timeGetTime();
  *(int *)(iVar1 + 0x780474c) = iVar2 - _DAT_03749354;
  *(undefined1 *)(iVar1 + 0x7804744) = *(undefined1 *)(unaff_EDI + 4);
  _DAT_078b085c = _DAT_078b085c + param_1;
  _DAT_078b0864 = _DAT_078b0864 + 1;
  *(uint *)(iVar1 + 0x7804754) = -(uint)(*(char *)(unaff_EDI + 4) != '\0') & param_1;
  return;
}

