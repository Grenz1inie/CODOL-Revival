// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 资产对象构造
// VA: 0x00a4a5b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_10a1e8e3b697111e325ce5bf5cd148f25a7dec8b893a6aa09f561f686799161b
// BEGIN PSEUDOCODE

void FUN_00a4a5b0(int param_1)

{
  uint uVar1;
  undefined4 *in_ECX;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_00b42282;
  local_10 = ExceptionList;
  uVar1 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  if (param_1 != 0) {
    in_ECX[1] = &DAT_00c076d8;
    in_ECX[3] = &DAT_00c076d0;
    in_ECX[0x2002] = bdReferencable::vftable;
    in_ECX[0x2003] = 0;
    local_8 = 0;
  }
  FUN_00a45500(0);
  local_8 = 1;
  FUN_00a473b0(0);
  *in_ECX = &PTR_FUN_00c076c4;
  in_ECX[2] = &PTR_FUN_00c076bc;
  *(undefined ***)(*(int *)(in_ECX[1] + 4) + 4 + (int)in_ECX) = &PTR_FUN_00c076b8;
  local_8._0_1_ = 2;
  FUN_00a456e0(uVar1);
  local_8._0_1_ = 3;
  _eh_vector_vbase_constructor_iterator_
            (in_ECX + 0xe,0x40,10,FUN_00a64990,(_func_void_void_ptr *)&LAB_004a4740);
  in_ECX[0xaf] = 0;
  in_ECX[0xb0] = 0;
  in_ECX[0xb1] = 0;
  local_8._0_1_ = 5;
  FUN_00a4bbc0(1);
  local_8 = CONCAT31(local_8._1_3_,6);
  FUN_00a4a470();
  ExceptionList = local_10;
  return;
}

