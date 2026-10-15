// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 账号标识对象的类型字段和 ID 比较
// VA: 0x00a45630; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_59d656721327b854e3dbcc2136386131613815d4e06f26ce595a2168d15b9253
// BEGIN PSEUDOCODE

undefined4 FUN_00a45630(int param_1)

{
  int iVar1;
  int in_ECX;
  
  iVar1 = _strncmp((char *)(in_ECX + 8),(char *)(param_1 + 8),10);
  if (((iVar1 == 0) && (*(int *)(in_ECX + 0x18) == *(int *)(param_1 + 0x18))) &&
     (*(int *)(in_ECX + 0x1c) == *(int *)(param_1 + 0x1c))) {
    return 1;
  }
  return 0;
}

