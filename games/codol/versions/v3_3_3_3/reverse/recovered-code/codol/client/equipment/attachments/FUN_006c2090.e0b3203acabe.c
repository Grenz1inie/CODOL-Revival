// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: 配件装备直接写入路径
// VA: 0x006c2090; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006c2090(int param_1,int param_2,int param_3,char param_4)

{
  char cVar1;
  char cVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  bool bVar7;
  undefined1 auStack_38 [4];
  char cStack_34;
  
  iVar3 = FUN_007051e0();
  FUN_006bf0c0();
  FUN_00695bc0(param_1,auStack_38);
  if ((cStack_34 == '\0') || (FUN_00695bc0(_DAT_077ea4ec,auStack_38), cStack_34 == '\0')) {
    if (param_4 != '\0') {
      FUN_006bf310(param_2);
    }
    return;
  }
  if ((*(int *)(&DAT_077ea4fc + param_3 * 4) == 0) && (iVar4 = FUN_006c33c0(iVar3), 9 < iVar4)) {
    if (param_3 == 0) {
      return;
    }
    if (param_3 == 1) {
      return;
    }
    if (param_3 == 2) {
      return;
    }
  }
  FUN_006bf0c0();
  iVar4 = *(int *)(&DAT_077ea4fc + param_3 * 4);
  *(int *)(&DAT_077ea4fc + param_3 * 4) = param_1;
  FUN_006bf310(param_2);
  if ((param_1 == 0) || (iVar5 = func_0x005845b0(), iVar5 == 0)) {
    cVar2 = '\x10';
  }
  else {
    cVar2 = *(char *)(iVar5 + 6);
  }
  iVar5 = 0;
  do {
    if ((iVar5 != param_3) && (*(int *)(&DAT_077ea4fc + iVar5 * 4) != 0)) {
      iVar6 = func_0x005845b0();
      if (iVar6 == 0) {
        cVar1 = '\x10';
      }
      else {
        cVar1 = *(char *)(iVar6 + 6);
      }
      if (cVar1 == cVar2) {
        iVar6 = param_2 * 0x3c;
        cVar1 = *(char *)(iVar6 + 0x78a0478);
        *(undefined4 *)(&DAT_077ea4fc + iVar5 * 4) = 0;
        if (cVar1 != '\0') {
          *(undefined4 *)(iVar6 + 0x78a0488 + iVar5 * 8) = 0;
          *(undefined1 *)(iVar6 + 0x78a0484 + iVar5 * 8) = 0;
        }
      }
    }
    iVar5 = iVar5 + 1;
  } while (iVar5 < 6);
  if (_DAT_077ea50c == 0) goto LAB_006c226d;
  if (((param_1 == 0) || (iVar5 = func_0x005845b0(), iVar5 == 0)) ||
     (*(char *)(iVar5 + 6) != '\x03')) {
    if (((iVar4 < 1) || (iVar4 = func_0x005845b0(), iVar4 == 0)) ||
       ((*(char *)(iVar4 + 6) != '\x03' || (iVar4 = func_0x005845b0(), iVar4 == 0))))
    goto LAB_006c226d;
    bVar7 = *(char *)(iVar4 + 6) == '\x0f';
LAB_006c224b:
    if (!bVar7) goto LAB_006c226d;
  }
  else {
    iVar4 = func_0x005845b0();
    if ((iVar4 == 0) || (*(char *)(iVar4 + 6) != '\n')) {
      iVar4 = func_0x005845b0();
      if ((iVar4 == 0) || (*(char *)(iVar4 + 6) != '\x0f')) goto LAB_006c226d;
      cVar2 = FUN_007096c0(param_1);
      bVar7 = cVar2 == '\0';
      goto LAB_006c224b;
    }
  }
  _DAT_077ea50c = 0;
  FUN_006bf310(param_2);
LAB_006c226d:
  FUN_006bf050(iVar3);
  if (iVar3 == -1) {
    FUN_007051e0();
  }
  FUN_005946c0(&DAT_077ea4fc);
  FUN_005948f0();
  return;
}

