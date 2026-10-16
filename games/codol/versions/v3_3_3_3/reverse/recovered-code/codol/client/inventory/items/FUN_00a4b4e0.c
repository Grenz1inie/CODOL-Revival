// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.items
// Analyst label: 库存条目默认值初始化
// VA: 0x00a4b4e0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_62b6c641a80115cc8af23d1b718afabc77d48612d9993ac6e356b27bcfd074a4
// BEGIN PSEUDOCODE

void FUN_00a4b4e0(void)

{
  uint uVar1;
  int in_ECX;
  undefined4 local_3c;
  undefined4 local_38;
  undefined1 local_34 [32];
  uint local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_00b423f8;
  local_10 = ExceptionList;
  uVar1 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_3c = 0;
  local_38 = 0;
  local_14 = uVar1;
  FUN_00a455f0(&local_3c);
  local_8 = 0;
  FUN_00a45750(local_34);
  local_8 = 0xffffffff;
  FUN_00a45620(uVar1);
  *(undefined4 *)(in_ECX + 0x30) = 0;
  *(undefined4 *)(in_ECX + 0x34) = 0;
  *(undefined4 *)(in_ECX + 0x38) = 0;
  *(undefined1 *)(in_ECX + 0x7c) = 0;
  *(undefined4 *)(in_ECX + 0x80) = 0xffffffff;
  *(undefined4 *)(in_ECX + 0x88) = 0xffffffff;
  *(undefined4 *)(in_ECX + 0x8c) = 0x7fffffff;
  *(undefined2 *)(in_ECX + 0x90) = 0;
  *(undefined4 *)(in_ECX + 0x94) = 0xffffffff;
  _memset((void *)(in_ECX + 0x3c),0,0x40);
  *(undefined1 *)(in_ECX + 0x98) = 0;
  ExceptionList = local_10;
  __security_check_cookie(local_14 ^ (uint)&stack0xfffffffc);
  return;
}

