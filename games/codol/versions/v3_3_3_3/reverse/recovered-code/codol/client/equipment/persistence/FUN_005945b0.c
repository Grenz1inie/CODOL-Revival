// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.persistence
// Analyst label: 读取编码缓存中的武器与六个配件槽
// VA: 0x005945b0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment-tail.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_005945b0(uint *param_1)

{
  int in_EAX;
  uint uVar1;
  uint *in_EDX;
  
  if (*(char *)(in_EAX * 0x28 + 0x2e74038) == '\0') {
    uVar1 = 0;
  }
  else {
    uVar1 = *(uint *)(in_EAX * 0x28 + 0x2e74040) ^ _DAT_00cdd280;
    uVar1 = uVar1 << 8 | uVar1 >> 0x18;
  }
  *param_1 = uVar1;
  if (*(char *)(in_EAX * 0x28 + 0x2e74039) == '\0') {
    uVar1 = 0;
  }
  else {
    uVar1 = (_DAT_00cdd280 << 0x10 | _DAT_00cdd280 >> 0x10) ^ *(uint *)(in_EAX * 0x28 + 0x2e74044);
    uVar1 = uVar1 << 8 | uVar1 >> 0x18;
  }
  *in_EDX = uVar1;
  if (*(char *)(in_EAX * 0x28 + 0x2e7403a) == '\0') {
    uVar1 = 0;
  }
  else {
    uVar1 = (_DAT_00cdd280 >> 0xf | _DAT_00cdd280 << 0x11) ^ *(uint *)(in_EAX * 0x28 + 0x2e74048);
    uVar1 = uVar1 << 8 | uVar1 >> 0x18;
  }
  in_EDX[1] = uVar1;
  if (*(char *)(in_EAX * 0x28 + 0x2e7403b) == '\0') {
    uVar1 = 0;
  }
  else {
    uVar1 = (_DAT_00cdd280 >> 0xe | _DAT_00cdd280 << 0x12) ^ *(uint *)(in_EAX * 0x28 + 0x2e7404c);
    uVar1 = uVar1 << 8 | uVar1 >> 0x18;
  }
  in_EDX[2] = uVar1;
  if (*(char *)(in_EAX * 0x28 + 0x2e7403c) == '\0') {
    uVar1 = 0;
  }
  else {
    uVar1 = (_DAT_00cdd280 >> 0xd | _DAT_00cdd280 << 0x13) ^ *(uint *)(in_EAX * 0x28 + 0x2e74050);
    uVar1 = uVar1 << 8 | uVar1 >> 0x18;
  }
  in_EDX[3] = uVar1;
  if (*(char *)(in_EAX * 0x28 + 0x2e7403d) == '\0') {
    uVar1 = 0;
  }
  else {
    uVar1 = (_DAT_00cdd280 >> 0xc | _DAT_00cdd280 << 0x14) ^ *(uint *)(in_EAX * 0x28 + 0x2e74054);
    uVar1 = uVar1 << 8 | uVar1 >> 0x18;
  }
  in_EDX[4] = uVar1;
  if (*(char *)(in_EAX * 0x28 + 0x2e7403e) != '\0') {
    uVar1 = (_DAT_00cdd280 >> 0xb | _DAT_00cdd280 << 0x15) ^ *(uint *)(in_EAX * 0x28 + 0x2e74058);
    in_EDX[5] = uVar1 << 8 | uVar1 >> 0x18;
    return;
  }
  in_EDX[5] = 0;
  return;
}

