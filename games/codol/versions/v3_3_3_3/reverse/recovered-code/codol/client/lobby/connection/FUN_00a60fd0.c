// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.connection
// Analyst label: 握手输出加入发送队列并驱动发送
// VA: 0x00a60fd0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a60fd0(void)

{
  int iVar1;
  int in_ECX;
  undefined4 *puVar2;
  int *unaff_FS_OFFSET;
  undefined1 auStack_2c [24];
  int iStack_14;
  int iStack_10;
  undefined *puStack_c;
  undefined4 uStack_8;
  
  uStack_8 = 0xffffffff;
  puStack_c = &DAT_00b444bb;
  iStack_10 = *unaff_FS_OFFSET;
  *unaff_FS_OFFSET = (int)&iStack_10;
  iStack_14 = func_0x00a38020();
  puVar2 = (undefined4 *)0x0;
  uStack_8 = 0;
  if (iStack_14 != 0) {
    puVar2 = (undefined4 *)func_0x005ddee0();
  }
  if (puVar2 != (undefined4 *)0x0) {
    InterlockedIncrement();
  }
  uStack_8 = 1;
  if (puVar2 != (undefined4 *)0x0) {
    InterlockedIncrement(puVar2 + 1);
  }
  func_0x00a5fdb0();
  uStack_8._0_1_ = 2;
  func_0x00a60470(*(undefined4 *)(in_ECX + 0xbc),auStack_2c);
  func_0x00a60690();
  uStack_8 = CONCAT31(uStack_8._1_3_,1);
  func_0x00a5fe70();
  uStack_8 = 0xffffffff;
  if (puVar2 != (undefined4 *)0x0) {
    iVar1 = InterlockedDecrement(puVar2 + 1);
    if (iVar1 == 0) {
      (**(code **)*puVar2)(1);
    }
  }
  *unaff_FS_OFFSET = iStack_10;
  return;
}

