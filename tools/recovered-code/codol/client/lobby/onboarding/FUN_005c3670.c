// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.onboarding
// Analyst label: un_mp_tutorial 完成判断
// VA: 0x005c3670; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_6bc47e9711bca44a0b74c03346ff294d057cc900ef70ed75f0fc0c942c4a1cd8
// BEGIN PSEUDOCODE

undefined4 FUN_005c3670(void)

{
  char cVar1;
  undefined4 uVar2;
  
  uVar2 = FUN_005c6350("un_mp_tutorial");
  cVar1 = FUN_005953a0(uVar2);
  if ((cVar1 == '\0') && (*(int *)(DAT_0783fa70 + 0xc) == 0)) {
    return 0;
  }
  return 1;
}

