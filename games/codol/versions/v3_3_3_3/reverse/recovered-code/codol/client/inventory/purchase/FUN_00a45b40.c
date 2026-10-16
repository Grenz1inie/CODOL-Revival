// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.purchase
// Analyst label: 购买参数序列化
// VA: 0x00a45b40; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_60c09e85610a6653145703c27de72c972088f74add7dd4d4167b918cd8c06a23
// BEGIN PSEUDOCODE

void FUN_00a45b40(int *param_1,undefined4 param_2)

{
  byte bVar1;
  char cVar2;
  undefined1 uVar3;
  undefined4 uVar4;
  uint uVar5;
  undefined4 *puVar6;
  undefined4 *puVar7;
  undefined4 *puVar8;
  int iVar9;
  undefined4 *puVar10;
  undefined4 *in_stack_0000002c;
  undefined4 *in_stack_00000030;
  byte in_stack_00000034;
  undefined4 in_stack_00000038;
  undefined1 *in_stack_0000003c;
  int in_stack_00000040;
  int in_stack_00000044;
  undefined4 *in_stack_00000048;
  int in_stack_0000004c;
  undefined4 in_stack_00000050;
  undefined4 *in_stack_00000054;
  undefined1 *puVar11;
  undefined4 local_6c;
  undefined4 *local_68;
  undefined4 *local_64;
  undefined4 *local_60;
  char local_59;
  undefined4 *local_58;
  undefined1 local_34 [32];
  uint local_14;
  void *local_10;
  undefined1 *puStack_c;
  uint local_8;
  
  puVar10 = in_stack_00000054;
  iVar9 = in_stack_0000004c;
  puStack_c = &LAB_00b41a98;
  local_10 = ExceptionList;
  local_14 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_58 = in_stack_0000002c;
  local_68 = in_stack_00000030;
  local_60 = (undefined4 *)in_stack_0000003c;
  local_64 = in_stack_00000048;
  local_8 = 0;
  uVar4 = FUN_00a456e0(local_14);
  local_8._0_1_ = 1;
  local_59 = FUN_00a45630(uVar4);
  local_8 = (uint)local_8._1_3_ << 8;
  FUN_00a45620();
  puVar8 = local_58;
  if ((local_64 != (undefined4 *)0x0) && (uVar5 = 0, in_stack_00000034 != 0)) {
    do {
      if (0x40 < *(uint *)(iVar9 + uVar5 * 4)) {
        FUN_00a53d80(local_64[uVar5]);
        goto LAB_00a45c57;
      }
      bVar1 = (char)uVar5 + 1;
      uVar5 = (uint)bVar1;
    } while (bVar1 < in_stack_00000034);
  }
  if (((local_58 == (undefined4 *)0x0) || (local_68 == (undefined4 *)0x0)) ||
     (in_stack_00000034 == 0)) {
LAB_00a45c57:
    local_8 = 0xffffffff;
    FUN_00a45620();
  }
  else {
    FUN_00a63eb0(param_2);
    if (local_59 == '\0') {
      FUN_00a63e20(&stack0x0000000c);
    }
    puVar6 = (undefined4 *)(uint)in_stack_00000034;
    local_58 = puVar6;
    cVar2 = (**(code **)(*param_1 + 4))(4,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38f30(puVar6), cVar2 == '\0')) {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    puVar7 = puVar6;
    if (in_stack_00000034 != 0) {
      do {
        cVar2 = (**(code **)(*param_1 + 4))(4,1);
        if (cVar2 != '\0') {
          if ((char)param_1[5] != '\0') {
            param_1[6] = param_1[6] + -1;
          }
          if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38f30(*puVar8), cVar2 == '\0')) {
            uVar3 = 0;
          }
          else {
            uVar3 = 1;
          }
          *(undefined1 *)(param_1 + 3) = uVar3;
        }
        puVar8 = puVar8 + 1;
        puVar6 = (undefined4 *)((int)puVar6 + -1);
        puVar7 = local_58;
      } while (puVar6 != (undefined4 *)0x0);
    }
    cVar2 = (**(code **)(*param_1 + 4))(4,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38f30(puVar7), cVar2 == '\0')) {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    puVar8 = local_58;
    puVar6 = local_68;
    if (in_stack_00000034 != 0) {
      do {
        cVar2 = (**(code **)(*param_1 + 4))(4,1);
        if (cVar2 != '\0') {
          if ((char)param_1[5] != '\0') {
            param_1[6] = param_1[6] + -1;
          }
          if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38f30(*puVar6), cVar2 == '\0')) {
            uVar3 = 0;
          }
          else {
            uVar3 = 1;
          }
          *(undefined1 *)(param_1 + 3) = uVar3;
        }
        puVar8 = (undefined4 *)((int)puVar8 + -1);
        puVar6 = puVar6 + 1;
      } while (puVar8 != (undefined4 *)0x0);
    }
    cVar2 = (**(code **)(*param_1 + 4))(1,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38e60(in_stack_00000038), cVar2 == '\0')) {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    cVar2 = (**(code **)(*param_1 + 4))(4,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38f30(local_58), cVar2 == '\0')) {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    local_6c = 0;
    local_68 = (undefined4 *)0x0;
    FUN_00a455f0(&local_6c);
    local_8 = CONCAT31(local_8._1_3_,2);
    puVar8 = local_58;
    puVar6 = local_60;
    if (in_stack_00000034 != 0) {
      do {
        puVar11 = (undefined1 *)puVar6;
        if (local_60 == (undefined4 *)0x0) {
          puVar11 = local_34;
        }
        FUN_00a63e20(puVar11);
        puVar8 = (undefined4 *)((int)puVar8 + -1);
        puVar6 = (undefined4 *)((int)puVar6 + 0x20);
      } while (puVar8 != (undefined4 *)0x0);
    }
    cVar2 = (**(code **)(*param_1 + 4))(4,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38f30(in_stack_00000044), cVar2 == '\0')) {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    if (local_64 == (undefined4 *)0x0) {
      cVar2 = (**(code **)(*param_1 + 4))(4,1);
      if (cVar2 != '\0') {
        if ((char)param_1[5] != '\0') {
          param_1[6] = param_1[6] + -1;
        }
        if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38f30(0), cVar2 == '\0')) {
          uVar3 = 0;
        }
        else {
          uVar3 = 1;
        }
        *(undefined1 *)(param_1 + 3) = uVar3;
      }
    }
    else {
      cVar2 = (**(code **)(*param_1 + 4))();
      if (cVar2 != '\0') {
        if ((char)param_1[5] != '\0') {
          param_1[6] = param_1[6] + -1;
        }
        if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38f30(local_58), cVar2 == '\0')) {
          uVar3 = 0;
        }
        else {
          uVar3 = 1;
        }
        *(undefined1 *)(param_1 + 3) = uVar3;
      }
      if (local_58 != (undefined4 *)0x0) {
        iVar9 = iVar9 - (int)local_64;
        local_60 = local_58;
        puVar8 = local_64;
        do {
          FUN_00a63c50(*puVar8,*(undefined4 *)(iVar9 + (int)puVar8));
          puVar8 = puVar8 + 1;
          local_60 = (undefined4 *)((int)local_60 + -1);
        } while (local_60 != (undefined4 *)0x0);
        local_60 = (undefined4 *)0x0;
      }
    }
    cVar2 = (**(code **)(*param_1 + 4))(1,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38ea0(in_stack_00000050), cVar2 == '\0')) {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    cVar2 = (**(code **)(*param_1 + 4))(4,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38f30(local_58), cVar2 == '\0')) {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    if ((puVar10 != (undefined4 *)0x0) && (puVar8 = local_58, in_stack_00000034 != 0)) {
      do {
        cVar2 = (**(code **)(*param_1 + 4))(4,1);
        if (cVar2 != '\0') {
          if ((char)param_1[5] != '\0') {
            param_1[6] = param_1[6] + -1;
          }
          if (((char)param_1[3] == '\0') || (cVar2 = FUN_00a38f30(*puVar10), cVar2 == '\0')) {
            uVar3 = 0;
          }
          else {
            uVar3 = 1;
          }
          *(undefined1 *)(param_1 + 3) = uVar3;
        }
        puVar10 = puVar10 + 1;
        puVar8 = (undefined4 *)((int)puVar8 + -1);
      } while (puVar8 != (undefined4 *)0x0);
    }
    if ((param_1[8] == 0) && (param_1[9] == 0)) {
      param_1[8] = in_stack_00000040;
      param_1[10] = in_stack_00000044;
    }
    else {
      FUN_00a53d80();
      *(undefined1 *)(param_1 + 3) = 0;
    }
    local_8 = local_8 & 0xffffff00;
    FUN_00a45620();
    local_8 = 0xffffffff;
    FUN_00a45620();
  }
  ExceptionList = local_10;
  __security_check_cookie(local_14 ^ (uint)&stack0xfffffffc);
  return;
}

