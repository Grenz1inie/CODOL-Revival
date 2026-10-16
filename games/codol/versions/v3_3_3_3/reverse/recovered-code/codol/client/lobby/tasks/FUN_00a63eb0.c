// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 任务参数追加账号字段的有效性检查
// VA: 0x00a63eb0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

void FUN_00a63eb0(void)

{
  char cVar1;
  int *in_ECX;
  
  if ((char)in_ECX[5] == '\0') {
    cVar1 = (**(code **)(*in_ECX + 4))();
    if (cVar1 != '\0') {
      if ((char)in_ECX[3] != '\0') {
        if (in_ECX[4] != 0) {
          InterlockedIncrement(in_ECX[4] + 4);
        }
        cVar1 = func_0x00a45850();
        if (cVar1 != '\0') {
          *(undefined1 *)(in_ECX + 3) = 1;
          return;
        }
      }
      *(undefined1 *)(in_ECX + 3) = 0;
      return;
    }
  }
  else {
    func_0x00a53d80();
    *(undefined1 *)(in_ECX + 3) = 0;
  }
  return;
}

