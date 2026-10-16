// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 异步任务完成回调调用与槽位回收
// VA: 0x006f6470; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-task-dispatch.json
// BEGIN PSEUDOCODE

void FUN_006f6470(void)

{
  int iVar1;
  int *in_EAX;
  
  func_0x006f5830();
  if ((((DAT_0783f7bc == '\0') || (iVar1 = *in_EAX, iVar1 == 0x7a)) || (iVar1 == 0x1b)) ||
     (iVar1 == 0x1a)) {
    *(undefined1 *)((int)in_EAX + 6) = 1;
    (*(code *)in_EAX[0xc])();
    *(undefined1 *)((int)in_EAX + 6) = 0;
  }
  *in_EAX = 1;
  func_0x006f59a0();
  return;
}

