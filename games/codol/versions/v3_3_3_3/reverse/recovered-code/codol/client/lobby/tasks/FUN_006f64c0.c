// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 异步任务轮询、重试和完成分支调度
// VA: 0x006f64c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-task-dispatch.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006f64c0(void)

{
  char cVar1;
  int *in_EAX;
  int iVar2;
  
  if ((*in_EAX != 0) && (*(char *)((int)in_EAX + 6) == '\0')) {
    if (in_EAX[4] == 0) {
      if ((in_EAX[10] != 0) && (_DAT_07809c88 == 0)) {
        func_0x006f5940();
        func_0x00a44cc0();
        func_0x006f59a0();
        return;
      }
      *(undefined1 *)((int)in_EAX + 6) = 1;
      cVar1 = (*(code *)in_EAX[0xb])();
      *(undefined1 *)((int)in_EAX + 6) = 0;
      if (cVar1 != '\0') {
        FUN_006f6470((char)in_EAX[1]);
      }
    }
    else {
      if (in_EAX[6] == 0) {
        FUN_006f6470(0);
        return;
      }
      iVar2 = func_0x006435e0();
      if (in_EAX[6] + in_EAX[4] <= iVar2) {
        if ((uint)in_EAX[8] <= (uint)in_EAX[7]) {
          FUN_006f6470(0);
          return;
        }
        *(undefined1 *)((int)in_EAX + 6) = 1;
        (*(code *)in_EAX[0xd])();
        *(undefined1 *)((int)in_EAX + 6) = 0;
        return;
      }
    }
  }
  return;
}

