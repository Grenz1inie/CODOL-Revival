// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.progression
// Analyst label: 物品描述符查询
// VA: 0x005845b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_4c37cba6d19d74e3823fbb069616560442edd4bca6ca3495235bc8a7d81761fb
// BEGIN PSEUDOCODE

int FUN_005845b0(void)

{
  ushort uVar1;
  ushort in_AX;
  uint uVar2;
  
  if ((((in_AX != 0) &&
       (uVar2 = (uint)(ushort)((&DAT_02db8ad4)[in_AX / 1000] +
                              (short)((ulonglong)(uint)in_AX % 1000)), uVar2 < DAT_02db8ad0)) &&
      (uVar1 = *(ushort *)(DAT_02db8acc + uVar2 * 2), uVar1 != 0)) && (uVar1 < DAT_02db8ac8)) {
    return DAT_02db8ac4 + (uint)uVar1 * 0x28;
  }
  return 0;
}

