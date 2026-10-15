// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: 校验武器与六槽配件并清理无效缓存
// VA: 0x006c4240; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment-tail.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006c4240(int param_1,int param_2)

{
  ushort uVar1;
  uint uVar2;
  bool bVar3;
  char cVar4;
  int iVar5;
  uint uVar6;
  int in_ECX;
  int iVar7;
  undefined1 auStack_6c [7];
  char cStack_65;
  int iStack_64;
  int iStack_60;
  int iStack_5c;
  undefined1 auStack_58 [4];
  char cStack_54;
  uint auStack_24 [6];
  uint uStack_c;
  
  uStack_c = _DAT_00cc7c80 ^ (uint)auStack_6c;
  if (in_ECX == -1) {
    in_ECX = func_0x0068a0e0();
  }
  iVar7 = param_1;
  if (param_1 == -1) {
    iVar7 = _DAT_078a046c;
  }
  iVar7 = iVar7 + in_ECX * 5;
  iStack_60 = iVar7;
  iStack_5c = iVar7;
  if (iVar7 == -1) {
    iStack_60 = func_0x007051e0();
  }
  iVar5 = param_2;
  if (param_2 == 2) {
    iVar5 = _DAT_078a0470;
  }
  iStack_60 = iStack_60 * 2;
  if (iVar5 == 1) {
    iStack_60 = iStack_60 + 1;
  }
  FUN_005945b0(&iStack_64);
  if (iStack_64 != 0) {
    if ((iStack_64 < 0) || (func_0x00695bc0(iStack_64,auStack_58), cStack_54 == '\0')) {
      func_0x006bfc60(param_1);
      func_0x00af6b2f();
      return;
    }
    cVar4 = FUN_006c4160(iVar7);
    if (cVar4 == '\0') {
      func_0x006bfc60(param_1);
      func_0x00af6b2f();
      return;
    }
    cStack_65 = '\0';
    iVar7 = 0;
    do {
      uVar2 = auStack_24[iVar7];
      if (0 < (int)uVar2) {
        bVar3 = false;
        iVar5 = 0;
        if (0 < iVar7) {
          do {
            if (uVar2 == auStack_24[iVar5]) {
              bVar3 = true;
              break;
            }
            iVar5 = iVar5 + 1;
          } while (iVar5 < iVar7);
        }
        if ((((((short)uVar2 == 0) ||
              (uVar6 = (uint)(ushort)(*(short *)(((uVar2 & 0xffff) / 1000) * 2 + 0x2db8ad4) +
                                     (short)((ulonglong)(uVar2 & 0xffff) % 1000)),
              _DAT_02db8ad0 <= uVar6)) ||
             (uVar1 = *(ushort *)(_DAT_02db8acc + uVar6 * 2), uVar1 == 0)) ||
            ((_DAT_02db8ac8 <= uVar1 || (_DAT_02db8ac4 + (uint)uVar1 * 0x28 == 0)))) ||
           ((bVar3 || ((func_0x00695bc0(uVar2,auStack_58), cStack_54 == '\0' ||
                       (cVar4 = FUN_006c41c0(iStack_64,param_2,iVar7,iStack_5c), cVar4 == '\0'))))))
        {
          auStack_24[iVar7] = 0;
          cStack_65 = '\x01';
        }
      }
      iVar7 = iVar7 + 1;
    } while (iVar7 < 6);
    if (cStack_65 != '\0') {
      func_0x005946c0(auStack_24);
      func_0x00594890();
      func_0x00af6b2f();
      return;
    }
  }
  func_0x00af6b2f();
  return;
}

