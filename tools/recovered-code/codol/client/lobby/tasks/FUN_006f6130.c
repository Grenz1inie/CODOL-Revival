// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 重试任务引用更新和退避间隔递增
// VA: 0x006f6130; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-task-callbacks.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006f6130(undefined4 *param_1,int param_2)

{
  int *piVar1;
  float fVar2;
  undefined4 *puVar3;
  int *in_EAX;
  int iVar4;
  uint uVar5;
  int iVar6;
  undefined4 uStack_c;
  int *piStack_8;
  
  iVar6 = param_2;
  func_0x00a367e0();
  if (_DAT_0788c760 == 0) {
    _DAT_03749354 = timeGetTime();
    QueryPerformanceCounter(&uStack_c);
    _DAT_03749468 = uStack_c;
    _DAT_0374946c = piStack_8;
    _DAT_0788c760 = 1;
  }
  iVar4 = timeGetTime();
  iVar4 = iVar4 - _DAT_03749354;
  in_EAX[4] = 0;
  in_EAX[2] = iVar4;
  in_EAX[3] = iVar4 + 15000;
  piStack_8 = (int *)(iVar6 + 4);
  iVar4 = *piStack_8;
  in_EAX[7] = in_EAX[7] + 1;
  in_EAX[5] = iVar4;
  uVar5 = func_0x00a36760();
  uVar5 = *(int *)(iVar6 + 8) * (1 << ((byte)(uVar5 % (uint)in_EAX[7]) & 0x1f));
  if (60000 < uVar5) {
    uVar5 = 60000;
  }
  piVar1 = in_EAX + 10;
  in_EAX[6] = uVar5;
  if (&param_1 != (undefined4 **)piVar1) {
    if (((*piVar1 != 0) && (iVar6 = InterlockedDecrement(*piVar1 + 4), iVar6 == 0)) &&
       ((undefined4 *)*piVar1 != (undefined4 *)0x0)) {
      (*(code *)**(undefined4 **)*piVar1)(1);
    }
    *piVar1 = (int)param_1;
    if (param_1 != (undefined4 *)0x0) {
      InterlockedIncrement(param_1 + 1);
    }
  }
  puVar3 = param_1;
  fVar2 = (float)*piStack_8;
  if (*piStack_8 < 0) {
    fVar2 = fVar2 + 4.2949673e+09;
  }
  piStack_8 = (int *)(fVar2 / 1000.0);
  if (param_1 != (undefined4 *)0x0) {
    InterlockedIncrement(param_1 + 1);
  }
  func_0x00a44cd0(piStack_8);
  if ((puVar3 != (undefined4 *)0x0) && (iVar6 = InterlockedDecrement(puVar3 + 1), iVar6 == 0)) {
    (**(code **)*puVar3)(1);
  }
  piVar1 = (int *)(*in_EAX * 0x28 + 0x780740c);
  *piVar1 = *piVar1 + 1;
  func_0x00a53d80();
  if (((param_1 != (undefined4 *)0x0) && (iVar6 = InterlockedDecrement(param_1 + 1), iVar6 == 0)) &&
     (param_1 != (undefined4 *)0x0)) {
    (**(code **)*param_1)(1);
  }
  return;
}

