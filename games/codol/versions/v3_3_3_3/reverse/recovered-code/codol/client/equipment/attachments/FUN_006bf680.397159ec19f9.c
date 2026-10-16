// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: 配件槽位同步到编辑缓存
// VA: 0x006bf680; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006bf680(int param_1)

{
  int iVar1;
  int iVar2;
  int in_EAX;
  uint uVar3;
  
  iVar2 = in_EAX * 0x3c;
  if (*(char *)(iVar2 + 0x78a0478) != '\0') {
    FUN_007051e0();
    FUN_006bf0c0();
    iVar1 = *(int *)(&DAT_077ea4fc + param_1 * 4);
    if (0 < iVar1) {
      uVar3 = (iVar1 << 0x18 | iVar1 >> 8) ^ _DAT_00cd64c0;
      *(undefined1 *)(iVar2 + 0x78a0484 + param_1 * 8) = 1;
      *(uint *)(iVar2 + 0x78a0488 + param_1 * 8) = uVar3;
      return;
    }
    *(undefined4 *)(iVar2 + 0x78a0488 + param_1 * 8) = 0;
    *(undefined1 *)(iVar2 + 0x78a0484 + param_1 * 8) = 0;
  }
  return;
}

