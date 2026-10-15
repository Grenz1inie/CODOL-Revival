// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 远程任务缓冲内存和游标初始化
// VA: 0x00a62c40; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby-tail.json
// BEGIN PSEUDOCODE

void FUN_00a62c40(int param_1)

{
  int iVar1;
  int in_ECX;
  
  if (param_1 != 0) {
    *(undefined4 *)(in_ECX + 0x28) = 0x18;
    *(int *)(in_ECX + 0x20) = param_1 + 0x37;
    iVar1 = func_0x00a38020(param_1 + 0x37);
    *(int *)(in_ECX + 0x1c) = iVar1;
    *(int *)(in_ECX + 0xc) = iVar1 + 0x1f;
    *(undefined4 *)(in_ECX + 0x24) = 0x1f;
    *(int *)(in_ECX + 8) = param_1;
  }
  *(undefined4 *)(in_ECX + 0x14) = *(undefined4 *)(in_ECX + 0xc);
  *(undefined4 *)(in_ECX + 0x10) = *(undefined4 *)(in_ECX + 0xc);
  return;
}

