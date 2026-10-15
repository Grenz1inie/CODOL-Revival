// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 客户端异步任务槽位分配及回调路径
// VA: 0x006f5d20; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby-tail.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006f5d20(int param_1,undefined4 *param_2,undefined4 param_3,undefined4 param_4,
                 undefined4 param_5,undefined4 param_6,undefined4 param_7,undefined4 param_8)

{
  float fVar1;
  int iVar2;
  int *piVar3;
  undefined4 *puVar4;
  int iStack_50;
  undefined2 uStack_4c;
  undefined1 uStack_4a;
  int iStack_48;
  undefined4 uStack_44;
  undefined4 uStack_40;
  undefined4 uStack_3c;
  undefined4 uStack_38;
  undefined4 uStack_34;
  undefined4 uStack_30;
  undefined4 uStack_2c;
  undefined4 *puStack_28;
  undefined4 uStack_24;
  code *pcStack_20;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  int iStack_10;
  undefined4 uStack_c;
  undefined4 uStack_8;
  
  GetCurrentThreadId();
  iVar2 = *(int *)(param_1 * 8 + 0xcd686c) * 0x10 + 0xce6028;
  piVar3 = (int *)0xc970108;
  do {
    if (*piVar3 == 0) {
      puVar4 = param_2;
      if (param_2 != (undefined4 *)0x0) {
        InterlockedIncrement(param_2 + 1);
      }
      func_0x006f5b70(param_1,puVar4,param_3,param_4,param_5,param_6,iVar2,param_7,param_8);
      if (param_2 == (undefined4 *)0x0) {
        return;
      }
      iVar2 = InterlockedDecrement(param_2 + 1);
      if (iVar2 != 0) {
        return;
      }
      if (param_2 == (undefined4 *)0x0) {
        return;
      }
      (**(code **)*param_2)(1);
      return;
    }
    piVar3 = piVar3 + 0x11;
  } while ((int)piVar3 < 0xc971208);
  puStack_28 = (undefined4 *)0x0;
  puVar4 = param_2;
  if (param_2 != (undefined4 *)0x0) {
    InterlockedIncrement(param_2 + 1);
  }
  func_0x006f5b70(param_1,puVar4,param_3,param_4,param_5,param_6,iVar2,param_7,param_8);
  if (iStack_50 == 0) {
    if ((puStack_28 == (undefined4 *)0x0) ||
       (iVar2 = InterlockedDecrement(puStack_28 + 1), iVar2 != 0)) goto LAB_006f5f79;
    if (puStack_28 != (undefined4 *)0x0) {
      (**(code **)*puStack_28)(1);
    }
  }
  else {
    uStack_4c = CONCAT11(1,(undefined1)uStack_4c);
    if (iStack_10 != 0) {
      *(undefined1 *)(iStack_10 + 0xf8) = 1;
    }
    func_0x006f4d60(0);
    if (_DAT_0788c760 == 0) {
      _DAT_03749354 = timeGetTime();
      QueryPerformanceCounter(&uStack_c);
      _DAT_03749468 = uStack_c;
      _DAT_0374946c = uStack_8;
      _DAT_0788c760 = 1;
    }
    iVar2 = timeGetTime();
    iStack_48 = (iVar2 - _DAT_03749354) - iStack_48;
    fVar1 = (float)iStack_48;
    if (iStack_48 < 0) {
      fVar1 = fVar1 + 4.2949673e+09;
    }
    fVar1 = fVar1 / 1000.0;
    iStack_50 = iStack_50 * 0x28;
    *(float *)(iStack_50 + 0x780741c) = fVar1 + *(float *)(iStack_50 + 0x780741c);
    if (*(float *)(iStack_50 + 0x7807420) < fVar1) {
      *(float *)(iStack_50 + 0x7807420) = fVar1;
    }
    if (puStack_28 != (undefined4 *)0x0) {
      func_0x00a44cc0();
    }
    iStack_50 = 1;
    uStack_4a = 1;
    (*pcStack_20)(&iStack_50,0);
    uStack_4a = 0;
    if (((puStack_28 != (undefined4 *)0x0) &&
        (iVar2 = InterlockedDecrement(puStack_28 + 1), iVar2 == 0)) &&
       (puStack_28 != (undefined4 *)0x0)) {
      (**(code **)*puStack_28)(1);
    }
    iStack_50 = 0;
    uStack_4c = 0;
    uStack_4a = 0;
    iStack_48 = 0;
    uStack_44 = 0;
    uStack_40 = 0;
    uStack_3c = 0;
    uStack_38 = 0;
    uStack_34 = 0;
    uStack_30 = 0;
    uStack_2c = 0;
    uStack_24 = 0;
    pcStack_20 = (code *)0x0;
    uStack_1c = 0;
    uStack_18 = 0;
    uStack_14 = 0;
    iStack_10 = 0;
  }
  puStack_28 = (undefined4 *)0x0;
LAB_006f5f79:
  if (((param_2 != (undefined4 *)0x0) && (iVar2 = InterlockedDecrement(param_2 + 1), iVar2 == 0)) &&
     (param_2 != (undefined4 *)0x0)) {
    (**(code **)*param_2)(1);
  }
  return;
}

