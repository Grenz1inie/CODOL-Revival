// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.loadout
// Analyst label: 武器类别与装备槽位匹配判断
// VA: 0x006c4160; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment-tail.json
// BEGIN PSEUDOCODE

bool FUN_006c4160(void)

{
  byte bVar1;
  char cVar2;
  int in_EAX;
  int iVar3;
  uint unaff_EDI;
  
  if (in_EAX == 0) {
    return true;
  }
  iVar3 = func_0x005845b0();
  if (iVar3 != 0) {
    iVar3 = func_0x005845b0();
    if (iVar3 == 0) {
      bVar1 = 10;
    }
    else {
      bVar1 = *(byte *)(iVar3 + 6);
    }
    if (5 < bVar1 == unaff_EDI) {
      return true;
    }
    if (unaff_EDI == 1) {
      cVar2 = func_0x006c2800();
      return cVar2 != '\0';
    }
  }
  return false;
}

