// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 默认档案初始化路径
// VA: 0x006d87d0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_7d8cc19d471049d1a3ff1531d2d7ad1c114afe76de7bce5db1ab31474a9e3db0
// BEGIN PSEUDOCODE

void FUN_006d87d0(void)

{
  int in_ECX;
  
  if (((((DAT_00cd7000 != 4) && (DAT_00cd7000 != 6)) ||
       ((*(int *)(in_ECX + 0x6c) != 0 &&
        ((*(int *)(in_ECX + 0x60) != 0 || *(int *)(in_ECX + 100) != 0 ||
         (*(char *)(in_ECX + 0x68) != '\0')))))) && (*(int *)(in_ECX + 0x74) == 0)) &&
     ((*(int *)(in_ECX + 0x78) == 0 && (*(char *)(in_ECX + 0x68) == '\0')))) {
    FUN_006d84d0(1);
  }
  return;
}

