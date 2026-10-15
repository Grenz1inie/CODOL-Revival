// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.progression
// Analyst label: 武器最大 rank 查询
// VA: 0x0046ee30; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_a249b6294ecdb11e0a5e9f32b8ebac08303fc276f642dd2da8c1292d9d4ceacf
// BEGIN PSEUDOCODE

void FUN_0046ee30(char param_1)

{
  int iVar1;
  int iVar2;
  undefined1 *puVar3;
  char *pcVar4;
  
  if (param_1 == '\0') {
    pcVar4 = "mp/coWeaponSecondaryRankTable.csv";
  }
  else {
    pcVar4 = "mp/coWeaponPrimaryRankTable.csv";
  }
  iVar2 = FUN_0049e7d0(0x25,pcVar4,1);
  iVar1 = *(int *)(iVar2 + 8) + -1;
  if ((((*(int *)(iVar2 + 4) < 1) || (*(int *)(iVar2 + 8) <= iVar1)) || (iVar1 < 0)) ||
     (puVar3 = *(undefined1 **)(*(int *)(iVar2 + 0xc) + *(int *)(iVar2 + 4) * iVar1 * 8),
     puVar3 == (undefined1 *)0x0)) {
    puVar3 = &DAT_00c4e869;
  }
  FUN_00af6e68(puVar3);
  return;
}

