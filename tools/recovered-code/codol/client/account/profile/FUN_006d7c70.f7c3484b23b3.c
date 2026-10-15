// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案数据和扩展缓存清空
// VA: 0x006d7c70; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

void FUN_006d7c70(void)

{
  int in_EAX;
  
  func_0x00afd440(in_EAX + 0x7c,0,0x8000);
  FUN_006d8a00();
  func_0x00afd440(in_EAX + 0x8084,0,0x1000);
  if (*(int *)(in_EAX + 37000) != 0) {
    func_0x00af6cad(*(int *)(in_EAX + 37000));
    *(undefined4 *)(in_EAX + 37000) = 0;
    *(undefined4 *)(in_EAX + 0x908c) = 0;
  }
  *(undefined4 *)(in_EAX + 0x8080) = 0;
  *(undefined4 *)(in_EAX + 0x807c) = 0;
  *(undefined2 *)(in_EAX + 0x9084) = 0;
  return;
}

