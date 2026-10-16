// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: 配件目录关系表兼容性查询
// VA: 0x007096c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

uint FUN_007096c0(void)

{
  int iVar1;
  ushort uVar2;
  int iVar3;
  uint uVar4;
  int iVar5;
  
  iVar3 = func_0x005845b0();
  iVar1 = _DAT_02dbba34;
  uVar4 = 0;
  if (iVar3 != 0) {
    uVar4 = (uint)*(ushort *)(iVar3 + 2);
    iVar3 = _DAT_02dbba34 + uVar4 * 0xe;
    if (iVar3 != 0) {
      iVar5 = func_0x005845b0();
      uVar4 = 0;
      if ((((iVar5 != 0) &&
           (iVar1 = iVar1 + (uint)*(ushort *)(iVar5 + 2) * 0xe, uVar4 = 0, iVar1 != 0)) &&
          (uVar4 = (uint)*(ushort *)(iVar1 + 2) * 0x10 + _DAT_02dbba3c, uVar4 != 0)) &&
         (uVar2 = *(ushort *)(iVar3 + 2), uVar2 <= *(ushort *)(uVar4 + 0xc))) {
        return CONCAT31((int3)(uVar4 >> 8),*(int *)(*(int *)(uVar4 + 8) + (uint)uVar2 * 4) != 0);
      }
    }
  }
  return uVar4 & 0xffffff00;
}

