// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.connection
// Analyst label: 连接失败状态切换和 socket 清理
// VA: 0x00a613c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

void FUN_00a613c0(void)

{
  char cVar1;
  int in_ECX;
  undefined4 unaff_ESI;
  
  if (*(int *)(in_ECX + 200) == 1) {
    func_0x00a61250(0);
  }
  else if (*(int *)(in_ECX + 200) != 4) {
    func_0x00a5fcb0();
  }
  *(undefined4 *)(in_ECX + 200) = 4;
  cVar1 = func_0x00b2e180(*(undefined4 *)(in_ECX + 0xc4),unaff_ESI);
  *(undefined4 *)(in_ECX + 0xc4) = 0xffffffff;
  if (cVar1 == '\0') {
    return;
  }
  return;
}

