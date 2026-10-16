// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.onboarding
// Analyst label: UI 通知定义查询
// VA: 0x005c6350; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_6bc47e9711bca44a0b74c03346ff294d057cc900ef70ed75f0fc0c942c4a1cd8
// BEGIN PSEUDOCODE

void FUN_005c6350(undefined4 param_1)

{
  int iVar1;
  int iVar2;
  undefined1 *puVar3;
  
  iVar1 = FUN_0049e7d0(0x25,"mp/uiNotifications.csv",1);
  if (iVar1 != 0) {
    iVar2 = FUN_0062f6c0(iVar1,0,param_1);
    if ((((1 < *(int *)(iVar1 + 4)) && (iVar2 < *(int *)(iVar1 + 8))) && (-1 < iVar2)) &&
       (puVar3 = *(undefined1 **)(*(int *)(iVar1 + 0xc) + 8 + *(int *)(iVar1 + 4) * iVar2 * 8),
       puVar3 != (undefined1 *)0x0)) goto LAB_005c639e;
  }
  puVar3 = &DAT_00c4e869;
LAB_005c639e:
  FUN_00af6e68(puVar3);
  return;
}

