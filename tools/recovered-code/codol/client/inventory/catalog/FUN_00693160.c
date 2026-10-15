// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.catalog
// Analyst label: SKU 界面对象与购买条件
// VA: 0x00693160; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_3ee074541bb53e150ad3ffea7543647929a0df5a099cb2faa2eecc3dd29728fb
// BEGIN PSEUDOCODE

undefined1 FUN_00693160(int param_1)

{
  char cVar1;
  int iVar2;
  undefined4 local_98;
  undefined4 local_94;
  undefined4 local_90;
  int local_8c;
  undefined4 local_88;
  int local_84;
  undefined4 local_80;
  undefined4 local_7c;
  undefined4 local_78;
  undefined4 local_74;
  int local_70;
  undefined1 local_6c;
  char local_6b;
  int local_68;
  int local_64;
  int local_60;
  undefined4 local_5c;
  undefined4 local_58;
  int local_54;
  undefined1 local_50 [8];
  int *local_48;
  uint local_44;
  undefined4 local_40;
  undefined1 local_29;
  undefined1 local_28 [8];
  int *local_20;
  uint local_1c;
  char *local_18;
  
  cVar1 = FUN_007070b0();
  if (cVar1 == '\0') {
    return 0;
  }
  local_54 = local_70;
  if (0 < local_8c) {
    local_54 = local_8c;
  }
  if (local_6b == '\0') {
    FUN_004a4b10(local_94);
    cVar1 = FUN_004a4ca0(local_90);
    if (cVar1 == '\0') {
      cVar1 = FUN_004a4d10(local_90);
      local_29 = 0;
      if (cVar1 == '\0') goto LAB_006931d6;
    }
  }
  local_29 = 1;
LAB_006931d6:
  local_58 = 0;
  local_5c = 0;
  if (local_6b == '\0') {
    FUN_004a4c10(local_90,&local_5c,&local_58);
  }
  local_48 = (int *)0x0;
  local_44 = 0;
  if (DAT_0c80327c != 0) {
    iVar2 = FUN_006bed90();
    FUN_00719d10(local_50,"codo.objects.SKUObj",0,0);
    if (iVar2 != 0) {
      FUN_006bee50();
    }
  }
  local_18 = (char *)local_98;
  local_20 = (int *)0x0;
  local_1c = 3;
  (**(code **)(*local_48 + 0x14))(local_40,"productId",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)local_58;
  local_20 = (int *)0x0;
  local_1c = 3;
  (**(code **)(*local_48 + 0x14))
            (local_40,"requirementLevel",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)local_5c;
  local_20 = (int *)0x0;
  local_1c = 3;
  (**(code **)(*local_48 + 0x14))
            (local_40,"requirementPrestige",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)CONCAT31(local_18._1_3_,0 < local_8c);
  local_20 = (int *)0x0;
  local_1c = 2;
  (**(code **)(*local_48 + 0x14))(local_40,"stackable",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)CONCAT31(local_18._1_3_,local_29);
  local_20 = (int *)0x0;
  local_1c = 2;
  (**(code **)(*local_48 + 0x14))(local_40,"purchasable",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)local_88;
  local_20 = (int *)0x0;
  local_1c = 3;
  (**(code **)(*local_48 + 0x14))(local_40,&DAT_00c65b54,local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)local_7c;
  local_20 = (int *)0x0;
  local_1c = 3;
  (**(code **)(*local_48 + 0x14))(local_40,"price",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = "@SF_UI_CP";
  if (local_84 < 1) {
    local_18 = "@SF_UI_GP";
  }
  local_20 = (int *)0x0;
  local_1c = 6;
  (**(code **)(*local_48 + 0x14))(local_40,"currency",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_20 = (int *)0x0;
  local_1c = 3;
  local_18 = (char *)local_84;
  (**(code **)(*local_48 + 0x14))(local_40,&DAT_00c65e10,local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)local_80;
  local_20 = (int *)0x0;
  local_1c = 3;
  (**(code **)(*local_48 + 0x14))(local_40,&DAT_00c65e0c,local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)local_54;
  local_20 = (int *)0x0;
  local_1c = 3;
  (**(code **)(*local_48 + 0x14))(local_40,"duration",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)local_78;
  local_20 = (int *)0x0;
  local_1c = 3;
  (**(code **)(*local_48 + 0x14))(local_40,"startDate",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)local_74;
  local_20 = (int *)0x0;
  local_1c = 3;
  (**(code **)(*local_48 + 0x14))(local_40,"endDate",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)CONCAT31(local_18._1_3_,local_6b);
  local_20 = (int *)0x0;
  local_1c = 2;
  (**(code **)(*local_48 + 0x14))
            (local_40,"ignoreEntitlement",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  local_18 = (char *)CONCAT31(local_18._1_3_,local_6c);
  local_20 = (int *)0x0;
  local_1c = 2;
  (**(code **)(*local_48 + 0x14))(local_40,"couponEnable",local_28,((byte)local_44 & 0x8f) == 10);
  if ((local_1c >> 6 & 1) != 0) {
    (**(code **)(*local_20 + 8))(local_28,local_18);
  }
  if (((0 < local_64) && (0 < local_68)) && (0 < local_60)) {
    local_20 = (int *)0x0;
    local_1c = 3;
    (**(code **)(*local_48 + 0x14))(local_40,"originalPrice",local_28,((byte)local_44 & 0x8f) == 10)
    ;
    FUN_004045f0();
    local_20 = (int *)0x0;
    local_1c = 3;
    (**(code **)(*local_48 + 0x14))(local_40,"price",local_28,((byte)local_44 & 0x8f) == 10);
    FUN_004045f0();
    local_18 = (char *)local_64;
    local_20 = (int *)0x0;
    local_1c = 3;
    (**(code **)(*local_48 + 0x14))(local_40,"discountRate",local_28,((byte)local_44 & 0x8f) == 10);
    FUN_004045f0();
  }
  (**(code **)(**(int **)(param_1 + 8) + 0x3c))(*(undefined4 *)(param_1 + 0x10),local_50);
  if ((local_44 >> 6 & 1) != 0) {
    (**(code **)(*local_48 + 8))(local_50,local_40);
  }
  return 1;
}

