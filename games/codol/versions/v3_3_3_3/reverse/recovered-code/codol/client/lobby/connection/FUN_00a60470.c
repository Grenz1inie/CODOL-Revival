// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.connection
// Analyst label: 发送队列链表插入
// VA: 0x00a60470; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby-tail.json
// BEGIN PSEUDOCODE

void FUN_00a60470(int param_1,undefined4 param_2)

{
  int iVar1;
  int *in_ECX;
  
  iVar1 = func_0x00a38020(0x20);
  if (iVar1 == 0) {
    iVar1 = 0;
  }
  else {
    func_0x00a5fe20(param_2);
  }
  if (param_1 != 0) {
    *(undefined4 *)(iVar1 + 0x18) = *(undefined4 *)(param_1 + 0x18);
    *(int *)(iVar1 + 0x1c) = param_1;
    if (*(int *)(param_1 + 0x18) != 0) {
      *(int *)(*(int *)(param_1 + 0x18) + 0x1c) = iVar1;
      *(int *)(param_1 + 0x18) = iVar1;
      in_ECX[2] = in_ECX[2] + 1;
      return;
    }
    in_ECX[1] = iVar1;
    *(int *)(param_1 + 0x18) = iVar1;
    in_ECX[2] = in_ECX[2] + 1;
    return;
  }
  *(undefined4 *)(iVar1 + 0x18) = 0;
  *(int *)(iVar1 + 0x1c) = in_ECX[1];
  if (in_ECX[1] != 0) {
    *(int *)(in_ECX[1] + 0x18) = iVar1;
    in_ECX[2] = in_ECX[2] + 1;
    in_ECX[1] = iVar1;
    return;
  }
  in_ECX[2] = in_ECX[2] + 1;
  *in_ECX = iVar1;
  in_ECX[1] = iVar1;
  return;
}

