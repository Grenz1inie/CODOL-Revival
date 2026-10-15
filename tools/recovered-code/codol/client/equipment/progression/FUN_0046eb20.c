// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.progression
// Analyst label: 经验到武器 rank 查询
// VA: 0x0046eb20; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_a249b6294ecdb11e0a5e9f32b8ebac08303fc276f642dd2da8c1292d9d4ceacf
// BEGIN PSEUDOCODE

void FUN_0046eb20(int param_1,char param_2)

{
  int iVar1;
  int iVar2;
  undefined1 *puVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  char *pcVar7;
  int local_8;
  
  if (param_2 == '\0') {
    pcVar7 = "mp/coWeaponSecondaryRankTable.csv";
  }
  else {
    pcVar7 = "mp/coWeaponPrimaryRankTable.csv";
  }
  iVar2 = FUN_0049e7d0(0x25,pcVar7,1);
  local_8 = *(int *)(iVar2 + 8) + -1;
  iVar6 = local_8 / 2;
  _param_2 = 0;
  if (0 < local_8) {
    do {
      if ((((*(int *)(iVar2 + 4) < 2) || (*(int *)(iVar2 + 8) <= iVar6)) || (iVar6 < 0)) ||
         (puVar3 = *(undefined1 **)(*(int *)(iVar2 + 0xc) + 8 + *(int *)(iVar2 + 4) * iVar6 * 8),
         puVar3 == (undefined1 *)0x0)) {
        puVar3 = &DAT_00c4e869;
      }
      iVar4 = FUN_00af6e68(puVar3);
      iVar1 = iVar6 + 1;
      if (((*(int *)(iVar2 + 4) < 2) || (*(int *)(iVar2 + 8) <= iVar1)) ||
         ((iVar1 < 0 ||
          (puVar3 = *(undefined1 **)(*(int *)(iVar2 + 0xc) + 8 + iVar1 * *(int *)(iVar2 + 4) * 8),
          puVar3 == (undefined1 *)0x0)))) {
        puVar3 = &DAT_00c4e869;
      }
      iVar5 = FUN_00af6e68(puVar3);
      if (param_1 < iVar4) {
        local_8 = iVar6 + -1;
      }
      else {
        _param_2 = iVar1;
        if (param_1 < iVar5) break;
      }
      iVar6 = (local_8 - _param_2) / 2 + _param_2;
    } while (_param_2 < local_8);
  }
  if (((*(int *)(iVar2 + 4) < 1) || (*(int *)(iVar2 + 8) <= iVar6)) ||
     ((iVar6 < 0 ||
      (puVar3 = *(undefined1 **)(*(int *)(iVar2 + 0xc) + *(int *)(iVar2 + 4) * iVar6 * 8),
      puVar3 == (undefined1 *)0x0)))) {
    puVar3 = &DAT_00c4e869;
  }
  FUN_00af6e68(puVar3);
  return;
}

