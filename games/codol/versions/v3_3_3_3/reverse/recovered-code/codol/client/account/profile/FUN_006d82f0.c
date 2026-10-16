// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案任务结束和状态复位
// VA: 0x006d82f0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

undefined4 FUN_006d82f0(int param_1)

{
  int iVar1;
  int in_EAX;
  
  iVar1 = *(int *)(in_EAX + 0x74);
  if (iVar1 == 0) {
    return 0;
  }
  if ((iVar1 == 1) || (iVar1 == 3)) {
    func_0x006d7e60(param_1 == 1);
  }
  if (*(int *)(in_EAX + 0x74) == 4) {
    *(undefined4 *)(in_EAX + 0x909c) = 0;
    if (*(int *)(in_EAX + 37000) != 0) {
      func_0x00af6cad(*(int *)(in_EAX + 37000));
      *(undefined4 *)(in_EAX + 37000) = 0;
      *(undefined4 *)(in_EAX + 0x908c) = 0;
    }
  }
  if (*(int *)(in_EAX + 0x74) == 2) {
    *(undefined1 *)(in_EAX + 0x9085) = 0;
  }
  *(undefined4 *)(in_EAX + 0x74) = 0;
  return 1;
}

