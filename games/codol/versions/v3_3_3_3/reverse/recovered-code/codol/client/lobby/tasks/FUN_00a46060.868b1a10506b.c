// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 任务参数有效性检查与提交包装
// VA: 0x00a46060; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

void FUN_00a46060(undefined4 param_1,int param_2)

{
  int iVar1;
  
  if ((*(char *)(param_2 + 0x14) != '\0') || (*(int *)(param_2 + 0x18) != 0)) {
    func_0x00a53d80(*(undefined4 *)(param_2 + 0x18));
  }
  if ((((*(char *)(param_2 + 0x14) == '\0') && (*(int *)(param_2 + 0x18) == 0)) &&
      (*(char *)(param_2 + 0xc) != '\0')) &&
     ((*(int *)(param_2 + 0x10) != 0 && (*(int *)(*(int *)(param_2 + 0x10) + 0xc) != 0)))) {
    iVar1 = func_0x00a3c6f0(param_1,param_2);
    if (iVar1 != 0) {
      func_0x00a53d80(iVar1);
      return;
    }
  }
  else {
    func_0x00a53d80();
  }
  return;
}

