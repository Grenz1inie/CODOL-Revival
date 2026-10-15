// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.items
// Analyst label: 库存哈希表按编码物品 ID 查找
// VA: 0x004a7a50; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_004a7a50(void)

{
  int iVar1;
  byte *in_ECX;
  
  if ((*_DAT_0783f860 != 0) &&
     (iVar1 = *(int *)(_DAT_0783f860[4] +
                      (_DAT_0783f860[1] - 1U &
                      ((((uint)*in_ECX * 0x1000193 ^ (uint)in_ECX[1]) * 0x1000193 ^ (uint)in_ECX[2])
                       * 0x1000193 ^ (uint)in_ECX[3])) * 4), iVar1 != 0)) {
    do {
      if (*(int *)in_ECX == *(int *)(iVar1 + 0x20)) {
        return iVar1;
      }
      iVar1 = *(int *)(iVar1 + 0x24);
    } while (iVar1 != 0);
  }
  return 0;
}

