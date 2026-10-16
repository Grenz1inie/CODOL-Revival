// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案远程任务引用转移
// VA: 0x006d7290; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

void FUN_006d7290(int *param_1)

{
  int iVar1;
  int *in_ECX;
  
  if (param_1 != in_ECX) {
    if (*in_ECX != 0) {
      iVar1 = InterlockedDecrement(*in_ECX + 4);
      if ((iVar1 == 0) && ((undefined4 *)*in_ECX != (undefined4 *)0x0)) {
        (*(code *)**(undefined4 **)*in_ECX)(1);
      }
    }
    iVar1 = *param_1;
    *in_ECX = iVar1;
    if (iVar1 != 0) {
      InterlockedIncrement(iVar1 + 4);
    }
  }
  return;
}

