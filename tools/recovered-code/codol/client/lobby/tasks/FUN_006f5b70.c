// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 任务槽位初始化并保存完成回调
// VA: 0x006f5b70; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006f5b70(undefined4 param_1,undefined4 *param_2,undefined4 param_3,undefined4 param_4,
                 undefined4 param_5,undefined4 param_6,int *param_7,int param_8,float param_9)

{
  int *piVar1;
  undefined4 *puVar2;
  char cVar3;
  undefined4 *in_EAX;
  int iVar4;
  int iVar5;
  bool bVar6;
  undefined4 uStack_c;
  undefined4 uStack_8;
  
  cVar3 = param_9._0_1_;
  func_0x006f59a0();
  bVar6 = _DAT_0788c760 == 0;
  *in_EAX = param_1;
  if (bVar6) {
    _DAT_03749354 = timeGetTime();
    QueryPerformanceCounter(&uStack_c);
    _DAT_03749468 = uStack_c;
    _DAT_0374946c = uStack_8;
    _DAT_0788c760 = 1;
  }
  iVar4 = timeGetTime();
  iVar4 = iVar4 - _DAT_03749354;
  in_EAX[2] = iVar4;
  in_EAX[3] = iVar4 + 15000;
  in_EAX[5] = *param_7;
  if (cVar3 == '\0') {
    iVar4 = 0;
  }
  else {
    iVar4 = param_7[2];
  }
  in_EAX[6] = iVar4;
  if (cVar3 == '\0') {
    iVar4 = 0;
  }
  else {
    iVar4 = param_7[3];
  }
  in_EAX[8] = iVar4;
  piVar1 = in_EAX + 10;
  if (&param_2 != (undefined4 **)piVar1) {
    if (((*piVar1 != 0) && (iVar4 = InterlockedDecrement(*piVar1 + 4), iVar4 == 0)) &&
       ((undefined4 *)*piVar1 != (undefined4 *)0x0)) {
      (*(code *)**(undefined4 **)*piVar1)(1);
    }
    *piVar1 = (int)param_2;
    if (param_2 != (undefined4 *)0x0) {
      InterlockedIncrement(param_2 + 1);
    }
  }
  iVar4 = param_8;
  puVar2 = param_2;
  in_EAX[0xc] = param_3;
  in_EAX[0xd] = param_4;
  in_EAX[0xe] = param_5;
  in_EAX[0xb] = &UNK_006f62d0;
  in_EAX[0xf] = param_6;
  in_EAX[0x10] = param_8;
  param_9 = (float)*param_7;
  if (*param_7 < 0) {
    param_9 = param_9 + 4.2949673e+09;
  }
  param_9 = param_9 / 1000.0;
  if (param_9 < 60.0 == (param_9 == 60.0)) {
    param_9 = 60.0;
  }
  if (param_2 != (undefined4 *)0x0) {
    InterlockedIncrement(param_2 + 1);
  }
  func_0x00a44cd0(param_9);
  if ((puVar2 != (undefined4 *)0x0) && (iVar5 = InterlockedDecrement(puVar2 + 1), iVar5 == 0)) {
    (**(code **)*puVar2)(1);
  }
  if (iVar4 != 0) {
    *(undefined1 *)(iVar4 + 0xf8) = 0;
  }
  func_0x006f5710(iVar4 != 0);
  if (((param_2 != (undefined4 *)0x0) && (iVar4 = InterlockedDecrement(param_2 + 1), iVar4 == 0)) &&
     (param_2 != (undefined4 *)0x0)) {
    (**(code **)*param_2)(1);
  }
  return;
}

