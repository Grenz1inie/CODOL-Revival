// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.onboarding
// Analyst label: onboard_complete 完成判断
// VA: 0x005c36f0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_39e507d47d9f4eba714664eed69aa68c73f6c1bb854e913cb8abf929d99490fa
// BEGIN PSEUDOCODE

uint FUN_005c36f0(void)

{
  char cVar1;
  uint in_EAX;
  undefined4 uVar2;
  
  if (DAT_0783f8c0 != 0) {
    return in_EAX & 0xffffff00;
  }
  uVar2 = FUN_005c6350("onboard_complete");
  cVar1 = FUN_005953a0(uVar2);
  if ((cVar1 == '\0') && (*(int *)(DAT_0783fa74 + 0xc) == 0)) {
    return 0;
  }
  return 1;
}

