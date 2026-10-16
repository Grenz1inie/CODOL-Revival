// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.progression
// Analyst label: 物品描述符查询
// VA: 0x005845b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/loadout.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

int FUN_005845b0(void)

{
  ushort uVar1;
  ushort in_AX;
  uint uVar2;
  
  if ((((in_AX != 0) &&
       (uVar2 = (uint)(ushort)(*(short *)((in_AX / 1000) * 2 + 0x2db8ad4) +
                              (short)((ulonglong)(uint)in_AX % 1000)), uVar2 < _DAT_02db8ad0)) &&
      (uVar1 = *(ushort *)(_DAT_02db8acc + uVar2 * 2), uVar1 != 0)) && (uVar1 < _DAT_02db8ac8)) {
    return _DAT_02db8ac4 + (uint)uVar1 * 0x28;
  }
  return 0;
}

