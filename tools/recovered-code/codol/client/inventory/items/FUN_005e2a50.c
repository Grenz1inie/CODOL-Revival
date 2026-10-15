// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.items
// Analyst label: 库存到物品目录的映射
// VA: 0x005e2a50; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_883293686dd4fe1ff3fcea00d54d3b7715790c84069ec14d03701088d2223057
// BEGIN PSEUDOCODE

void FUN_005e2a50(void)

{
  ushort uVar1;
  uint uVar2;
  uint uVar3;
  int iVar4;
  undefined4 *puVar5;
  bool local_2c [4];
  uint local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 local_10;
  uint local_c;
  int local_8;
  
  FUN_005e2b70();
  local_8 = 0;
  if (0 < DAT_07817ddc) {
    puVar5 = &DAT_07bec4c8;
    iVar4 = DAT_0783f860;
    do {
      uVar2 = puVar5[-0x14];
      if (((short)uVar2 != 0) &&
         (uVar3 = (uint)(ushort)((&DAT_02db8ad4)[(uVar2 & 0xffff) / 1000] +
                                (short)((ulonglong)(uVar2 & 0xffff) % 1000)), uVar3 < DAT_02db8ad0))
      {
        uVar1 = *(ushort *)(DAT_02db8acc + uVar3 * 2);
        local_28 = 0;
        if ((uVar1 != 0) &&
           (((uVar1 < DAT_02db8ac8 && (DAT_02db8ac4 + (uint)uVar1 * 0x28 != 0)) && (iVar4 != 0)))) {
          local_2c[0] = 0 < (int)uVar2;
          if (local_2c[0]) {
            local_28 = (uVar2 << 0x18 | (int)uVar2 >> 8) ^ DAT_00cdc27c;
          }
          local_24 = puVar5[-0x13];
          local_20 = *puVar5;
          local_1c = puVar5[2];
          local_18 = puVar5[3];
          local_14 = puVar5[-0x12];
          local_10 = puVar5[5];
          local_c = (uVar2 << 0x18 | (int)uVar2 >> 8) ^ DAT_00cdc27c;
          FUN_0057e900(&local_c,local_2c);
          iVar4 = DAT_0783f860;
        }
      }
      local_8 = local_8 + 1;
      puVar5 = puVar5 + 0x2a;
    } while (local_8 < DAT_07817ddc);
  }
  return;
}

