// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 远程任务错误码读取
// VA: 0x00a44cf0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

undefined4 FUN_00a44cf0(void)

{
  int in_ECX;
  
  return *(undefined4 *)(in_ECX + 0x38);
}

