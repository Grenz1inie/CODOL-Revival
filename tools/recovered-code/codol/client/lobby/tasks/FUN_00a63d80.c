// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.tasks
// Analyst label: 任务参数对象引用清理
// VA: 0x00a63d80; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a63d80(void)

{
  uint uVar1;
  int iVar2;
  undefined4 *in_ECX;
  int *unaff_FS_OFFSET;
  int iStack_10;
  undefined *puStack_c;
  undefined4 uStack_8;
  
  puStack_c = &DAT_00b44828;
  iStack_10 = *unaff_FS_OFFSET;
  uVar1 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  *in_ECX = &UNK_00c080a8;
  uStack_8 = 0;
  if (in_ECX[0xb] != 0) {
    iVar2 = InterlockedDecrement(in_ECX[0xb] + 4);
    if (iVar2 == 0) {
      if ((undefined4 *)in_ECX[0xb] != (undefined4 *)0x0) {
        (*(code *)**(undefined4 **)in_ECX[0xb])(1);
      }
      in_ECX[0xb] = 0;
    }
  }
  uStack_8 = 0xffffffff;
  func_0x00a63a60(uVar1);
  *unaff_FS_OFFSET = iStack_10;
  return;
}

