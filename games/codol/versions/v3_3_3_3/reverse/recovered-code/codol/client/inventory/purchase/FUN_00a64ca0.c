// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.purchase
// Analyst label: 点券购买参数校验与序列化
// VA: 0x00a64ca0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment-tail.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a64ca0(int *param_1,undefined4 param_2)

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
  int *unaff_FS_OFFSET;
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
  undefined4 uStack_6c;
  undefined4 *puStack_68;
  undefined4 *puStack_64;
  undefined4 *puStack_60;
  char cStack_59;
  undefined4 *puStack_58;
  undefined1 auStack_34 [32];
  uint uStack_14;
  int iStack_10;
  undefined *puStack_c;
  uint uStack_8;
  
  puVar10 = in_stack_00000054;
  iVar9 = in_stack_0000004c;
  puStack_c = &DAT_00b41a98;
  iStack_10 = *unaff_FS_OFFSET;
  uStack_14 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  *unaff_FS_OFFSET = (int)&iStack_10;
  puStack_58 = in_stack_0000002c;
  puStack_68 = in_stack_00000030;
  puStack_60 = (undefined4 *)in_stack_0000003c;
  puStack_64 = in_stack_00000048;
  uStack_8 = 0;
  uVar4 = func_0x00a456e0(uStack_14);
  uStack_8._0_1_ = 1;
  cStack_59 = FUN_00a45630(uVar4);
  uStack_8 = (uint)uStack_8._1_3_ << 8;
  func_0x00a45620();
  puVar8 = puStack_58;
  if ((puStack_64 != (undefined4 *)0x0) && (uVar5 = 0, in_stack_00000034 != 0)) {
    do {
      if (0x40 < *(uint *)(iVar9 + uVar5 * 4)) {
        func_0x00a53d80(puStack_64[uVar5]);
        goto LAB_00a65186;
      }
      bVar1 = (char)uVar5 + 1;
      uVar5 = (uint)bVar1;
    } while (bVar1 < in_stack_00000034);
  }
  if (((puStack_58 == (undefined4 *)0x0) || (puStack_68 == (undefined4 *)0x0)) ||
     (in_stack_00000034 == 0)) {
    func_0x00a53d80();
LAB_00a65186:
    uStack_8 = 0xffffffff;
    func_0x00a45620();
  }
  else {
    func_0x00a63eb0(param_2);
    if (cStack_59 == '\0') {
      func_0x00a63e20(&stack0x0000000c);
    }
    puVar6 = (undefined4 *)(uint)in_stack_00000034;
    puStack_58 = puVar6;
    cVar2 = (**(code **)(*param_1 + 4))(4,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(puVar6), cVar2 == '\0')) {
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
          if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(*puVar8), cVar2 == '\0')) {
            uVar3 = 0;
          }
          else {
            uVar3 = 1;
          }
          *(undefined1 *)(param_1 + 3) = uVar3;
        }
        puVar8 = puVar8 + 1;
        puVar6 = (undefined4 *)((int)puVar6 + -1);
        puVar7 = puStack_58;
      } while (puVar6 != (undefined4 *)0x0);
    }
    cVar2 = (**(code **)(*param_1 + 4))(4,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(puVar7), cVar2 == '\0')) {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    puVar8 = puStack_58;
    puVar6 = puStack_68;
    if (in_stack_00000034 != 0) {
      do {
        cVar2 = (**(code **)(*param_1 + 4))(4,1);
        if (cVar2 != '\0') {
          if ((char)param_1[5] != '\0') {
            param_1[6] = param_1[6] + -1;
          }
          if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(*puVar6), cVar2 == '\0')) {
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
      if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38e60(in_stack_00000038), cVar2 == '\0'))
      {
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
      if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(puStack_58), cVar2 == '\0')) {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    uStack_6c = 0;
    puStack_68 = (undefined4 *)0x0;
    func_0x00a455f0(&uStack_6c);
    uStack_8 = CONCAT31(uStack_8._1_3_,2);
    puVar8 = puStack_58;
    puVar6 = puStack_60;
    if (in_stack_00000034 != 0) {
      do {
        puVar11 = (undefined1 *)puVar6;
        if (puStack_60 == (undefined4 *)0x0) {
          puVar11 = auStack_34;
        }
        func_0x00a63e20(puVar11);
        puVar8 = (undefined4 *)((int)puVar8 + -1);
        puVar6 = (undefined4 *)((int)puVar6 + 0x20);
      } while (puVar8 != (undefined4 *)0x0);
    }
    cVar2 = (**(code **)(*param_1 + 4))(4,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(in_stack_00000044), cVar2 == '\0'))
      {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    if (puStack_64 == (undefined4 *)0x0) {
      cVar2 = (**(code **)(*param_1 + 4))(4,1);
      if (cVar2 != '\0') {
        if ((char)param_1[5] != '\0') {
          param_1[6] = param_1[6] + -1;
        }
        if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(0), cVar2 == '\0')) {
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
        if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(puStack_58), cVar2 == '\0')) {
          uVar3 = 0;
        }
        else {
          uVar3 = 1;
        }
        *(undefined1 *)(param_1 + 3) = uVar3;
      }
      if (puStack_58 != (undefined4 *)0x0) {
        iVar9 = iVar9 - (int)puStack_64;
        puStack_60 = puStack_58;
        puVar8 = puStack_64;
        do {
          func_0x00a63c50(*puVar8,*(undefined4 *)(iVar9 + (int)puVar8));
          puVar8 = puVar8 + 1;
          puStack_60 = (undefined4 *)((int)puStack_60 + -1);
        } while (puStack_60 != (undefined4 *)0x0);
        puStack_60 = (undefined4 *)0x0;
      }
    }
    cVar2 = (**(code **)(*param_1 + 4))(1,1);
    if (cVar2 != '\0') {
      if ((char)param_1[5] != '\0') {
        param_1[6] = param_1[6] + -1;
      }
      if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38ea0(in_stack_00000050), cVar2 == '\0'))
      {
        uVar3 = 0;
      }
      else {
        uVar3 = 1;
      }
      *(undefined1 *)(param_1 + 3) = uVar3;
    }
    cVar2 = (**(code **)(*param_1 + 4))(4,1);
    if (puVar10 == (undefined4 *)0x0) {
      if (cVar2 != '\0') {
        if ((char)param_1[5] != '\0') {
          param_1[6] = param_1[6] + -1;
        }
        if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(0), cVar2 == '\0')) {
          uVar3 = 0;
        }
        else {
          uVar3 = 1;
        }
        *(undefined1 *)(param_1 + 3) = uVar3;
      }
    }
    else {
      if (cVar2 != '\0') {
        if ((char)param_1[5] != '\0') {
          param_1[6] = param_1[6] + -1;
        }
        if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(puStack_58), cVar2 == '\0')) {
          uVar3 = 0;
        }
        else {
          uVar3 = 1;
        }
        *(undefined1 *)(param_1 + 3) = uVar3;
      }
      puVar8 = puStack_58;
      if (in_stack_00000034 != 0) {
        do {
          cVar2 = (**(code **)(*param_1 + 4))(4,1);
          if (cVar2 != '\0') {
            if ((char)param_1[5] != '\0') {
              param_1[6] = param_1[6] + -1;
            }
            if (((char)param_1[3] == '\0') || (cVar2 = func_0x00a38f30(*puVar10), cVar2 == '\0')) {
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
    }
    if ((param_1[8] == 0) && (param_1[9] == 0)) {
      param_1[8] = in_stack_00000040;
      param_1[10] = in_stack_00000044;
    }
    else {
      func_0x00a53d80();
      *(undefined1 *)(param_1 + 3) = 0;
    }
    uStack_8 = uStack_8 & 0xffffff00;
    func_0x00a45620();
    uStack_8 = 0xffffffff;
    func_0x00a45620();
  }
  *unaff_FS_OFFSET = iStack_10;
  func_0x00af6b2f();
  return;
}

