// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.assets
// Analyst label: 余额、库存和权益复合对象读取
// VA: 0x00a4a6b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_4dd3cf17d58d8e07a368625ce759e071d269b23eab90f9f029e275cc6e927840
// BEGIN PSEUDOCODE

void FUN_00a4a6b0(undefined4 *param_1)

{
  bool bVar1;
  char cVar2;
  int iVar3;
  LONG LVar4;
  int in_ECX;
  int iVar5;
  uint uVar6;
  void *pvVar7;
  uint uVar8;
  uint local_c4;
  undefined1 local_bc [168];
  uint local_14;
  void *local_10;
  undefined1 *puStack_c;
  int local_8;
  
  puStack_c = &LAB_00b422d5;
  local_10 = ExceptionList;
  local_14 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  uVar6 = 0;
  local_8 = 0;
  if (param_1 != (undefined4 *)0x0) {
    InterlockedIncrement(param_1 + 1);
  }
  cVar2 = FUN_00a45950();
  if ((cVar2 == '\0') || (cVar2 = FUN_00a38a60(), cVar2 == '\0')) {
    bVar1 = false;
  }
  else {
    bVar1 = true;
  }
  if (*(int *)(in_ECX + 0x30) != 0) {
    do {
      if (bVar1) {
        uVar8 = uVar6;
        if (8 < uVar6) {
          uVar8 = 9;
        }
        FUN_00a456f0();
        if (param_1 != (undefined4 *)0x0) {
          InterlockedIncrement(param_1 + 1);
        }
        cVar2 = (**(code **)(*(int *)(uVar8 * 0x40 + 0x38 + in_ECX) + 8))();
        if (cVar2 == '\0') goto LAB_00a4a78b;
        bVar1 = true;
      }
      else {
LAB_00a4a78b:
        bVar1 = false;
      }
      uVar6 = uVar6 + 1;
    } while (uVar6 < *(uint *)(in_ECX + 0x30));
  }
  if (bVar1) {
    cVar2 = FUN_00a38a60();
    bVar1 = true;
    if (cVar2 != '\0') goto LAB_00a4a7ba;
  }
  bVar1 = false;
LAB_00a4a7ba:
  FUN_00a38040();
  *(undefined4 *)(in_ECX + 700) = 0;
  *(undefined4 *)(in_ECX + 0x2c4) = 0;
  *(undefined4 *)(in_ECX + 0x2c0) = 0;
  iVar5 = *(int *)(in_ECX + 0x2b8);
  if (iVar5 != 0) {
    if (iVar5 == 0) {
      iVar5 = 0;
    }
    pvVar7 = (void *)0x0;
    if (iVar5 != 0) {
      pvVar7 = (void *)FUN_00a38020();
      if (*(int *)(in_ECX + 0x2c4) != 0) {
        FID_conflict__memcpy(pvVar7,*(void **)(in_ECX + 700),*(int *)(in_ECX + 0x2c4) * 0xa8);
      }
    }
    FUN_00a38040();
    *(void **)(in_ECX + 700) = pvVar7;
    *(int *)(in_ECX + 0x2c0) = iVar5;
  }
  local_c4 = 0;
  if (*(int *)(in_ECX + 0x2b8) != 0) {
    do {
      FUN_00a4b5c0();
      local_8 = CONCAT31(local_8._1_3_,1);
      if (bVar1) {
        FUN_00a456f0();
        if (param_1 != (undefined4 *)0x0) {
          InterlockedIncrement(param_1 + 1);
        }
        cVar2 = FUN_00a4b850();
        bVar1 = true;
        if (cVar2 == '\0') goto LAB_00a4a8ca;
      }
      else {
LAB_00a4a8ca:
        bVar1 = false;
      }
      iVar5 = *(int *)(in_ECX + 0x2c0);
      if (*(int *)(in_ECX + 0x2c4) == iVar5) {
        iVar3 = 1;
        if (iVar5 != 0) {
          iVar3 = iVar5;
        }
        pvVar7 = (void *)0x0;
        if (iVar5 + iVar3 != 0) {
          pvVar7 = (void *)FUN_00a38020();
          if (*(int *)(in_ECX + 0x2c4) != 0) {
            FID_conflict__memcpy(pvVar7,*(void **)(in_ECX + 700),*(int *)(in_ECX + 0x2c4) * 0xa8);
          }
        }
        FUN_00a38040();
        *(void **)(in_ECX + 700) = pvVar7;
        *(int *)(in_ECX + 0x2c0) = iVar5 + iVar3;
      }
      FID_conflict__memcpy
                ((void *)(*(int *)(in_ECX + 0x2c4) * 0xa8 + *(int *)(in_ECX + 700)),local_bc,0xa8);
      *(int *)(in_ECX + 0x2c4) = *(int *)(in_ECX + 0x2c4) + 1;
      local_8._0_1_ = 3;
      FUN_00a45620();
      local_8._0_1_ = 2;
      FUN_00a473f0();
      local_8 = (uint)local_8._1_3_ << 8;
      FUN_00a45540();
      FUN_00a37f60();
      local_c4 = local_c4 + 1;
    } while (local_c4 < *(uint *)(in_ECX + 0x2b8));
  }
  if (bVar1) {
    FUN_00a456f0();
    if (param_1 != (undefined4 *)0x0) {
      InterlockedIncrement(param_1 + 1);
    }
    (**(code **)(*(int *)(in_ECX + 0x2c8) + 8))();
  }
  local_8 = 0xffffffff;
  if (((param_1 != (undefined4 *)0x0) && (LVar4 = InterlockedDecrement(param_1 + 1), LVar4 == 0)) &&
     (param_1 != (undefined4 *)0x0)) {
    (**(code **)*param_1)();
  }
  ExceptionList = local_10;
  __security_check_cookie(local_14 ^ (uint)&stack0xfffffffc);
  return;
}

