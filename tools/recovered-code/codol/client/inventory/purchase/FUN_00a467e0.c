// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.purchase
// Analyst label: 游戏币购买任务 80/154 参数构造
// VA: 0x00a467e0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_885f94242f8bba673f4cc68571e18e34148e02f0ed6cb3528eca8278e8df1c1e
// BEGIN PSEUDOCODE

undefined4 * FUN_00a467e0(undefined4 *param_1)

{
  char cVar1;
  int in_ECX;
  undefined1 local_44 [48];
  undefined4 local_14;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puStack_c = &LAB_00b41c11;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  *param_1 = 0;
  local_8 = 0;
  local_14 = 1;
  FUN_00a63f20();
  local_8 = 1;
  FUN_00a456e0();
  cVar1 = FUN_00a45b40(local_44,in_ECX + 4);
  if (cVar1 != '\0') {
    FUN_00a46060();
  }
  local_8 = local_8 & 0xffffff00;
  FUN_00a63d80();
  ExceptionList = local_10;
  return param_1;
}

