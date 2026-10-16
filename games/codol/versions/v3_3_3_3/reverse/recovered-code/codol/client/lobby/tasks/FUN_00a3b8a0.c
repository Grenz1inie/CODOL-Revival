// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 任务缓冲检查与传输虚调用
// VA: 0x00a3b8a0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby-tail.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined4 FUN_00a3b8a0(int *param_1,int *param_2)

{
  int *piVar1;
  int *piVar2;
  char cVar3;
  int iVar4;
  int in_ECX;
  int *unaff_FS_OFFSET;
  int iStack_30;
  undefined4 uStack_2c;
  int *piStack_28;
  uint uStack_24;
  undefined4 uStack_14;
  int iStack_10;
  undefined *puStack_c;
  undefined4 uStack_8;
  
  piVar2 = param_2;
  puStack_c = &DAT_00b40a18;
  iStack_10 = *unaff_FS_OFFSET;
  uStack_24 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  uStack_8 = 0;
  uStack_14 = 0;
  piStack_28 = (int *)0xa3b8da;
  cVar3 = func_0x00a38920();
  if (cVar3 != '\0') {
    piStack_28 = (int *)(uint)*(byte *)(in_ECX + 0x48);
    piVar1 = *(int **)(in_ECX + 0x44);
    uStack_2c = 0xa3b8ed;
    uStack_2c = func_0x00a38660();
    iStack_30 = *piVar2;
    param_2 = &iStack_30;
    piVar2 = &iStack_30;
    if (iStack_30 != 0) {
      InterlockedIncrement(iStack_30 + 4);
      piVar2 = param_2;
    }
    param_2 = piVar2;
    cVar3 = (**(code **)(*piVar1 + 4))();
    if (cVar3 != '\0') {
      uStack_2c = *(undefined4 *)(in_ECX + 0xc);
      piStack_28 = (int *)&param_1;
      iStack_30 = 0xa3b975;
      func_0x00b28930();
      iVar4 = *param_1;
      iStack_30 = 0xa3b983;
      iStack_30 = func_0x00a38660();
      (**(code **)(iVar4 + 0xc))(0);
      goto LAB_00a3b924;
    }
  }
  uStack_14 = 3;
  param_1[5] = 3;
  param_1[0xe] = 3;
LAB_00a3b924:
  uStack_8 = 0xffffffff;
  if (param_1 != (int *)0x0) {
    piStack_28 = param_1 + 1;
    uStack_2c = 0xa3b93c;
    iVar4 = InterlockedDecrement();
    if ((iVar4 == 0) && (param_1 != (int *)0x0)) {
      piStack_28 = (int *)0x1;
      uStack_2c = 0xa3b94f;
      (**(code **)*param_1)();
    }
  }
  *unaff_FS_OFFSET = iStack_10;
  return uStack_14;
}

