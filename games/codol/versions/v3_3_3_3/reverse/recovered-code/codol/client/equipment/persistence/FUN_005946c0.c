// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.persistence
// Analyst label: 武器与六槽配件写入编码缓存并标脏
// VA: 0x005946c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_005946c0(int *param_1)

{
  int iVar1;
  int iVar2;
  uint uVar3;
  int in_EAX;
  int in_EDX;
  
  uVar3 = _DAT_00cdd280;
  iVar2 = in_EAX * 0x28;
  *(undefined1 *)(iVar2 + 0x2e7405c) = 1;
  if (in_EDX < 1) {
    *(undefined4 *)(iVar2 + 0x2e74040) = 0;
    *(undefined1 *)(iVar2 + 0x2e74038) = 0;
  }
  else {
    *(uint *)(iVar2 + 0x2e74040) = (in_EDX << 0x18 | in_EDX >> 8) ^ uVar3;
    *(undefined1 *)(iVar2 + 0x2e74038) = 1;
  }
  iVar1 = *param_1;
  if (iVar1 < 1) {
    *(undefined4 *)(iVar2 + 0x2e74044) = 0;
    *(undefined1 *)(iVar2 + 0x2e74039) = 0;
  }
  else {
    *(uint *)(iVar2 + 0x2e74044) =
         (iVar1 << 0x18 | iVar1 >> 8) ^ (uVar3 << 0x10 | _DAT_00cdd280 >> 0x10);
    *(undefined1 *)(iVar2 + 0x2e74039) = 1;
  }
  iVar1 = param_1[1];
  if (iVar1 < 1) {
    *(undefined4 *)(iVar2 + 0x2e74048) = 0;
    *(undefined1 *)(iVar2 + 0x2e7403a) = 0;
  }
  else {
    *(uint *)(iVar2 + 0x2e74048) = (uVar3 >> 0xf | uVar3 << 0x11) ^ (iVar1 << 0x18 | iVar1 >> 8);
    *(undefined1 *)(iVar2 + 0x2e7403a) = 1;
  }
  iVar1 = param_1[2];
  if (iVar1 < 1) {
    *(undefined4 *)(iVar2 + 0x2e7404c) = 0;
    *(undefined1 *)(iVar2 + 0x2e7403b) = 0;
  }
  else {
    *(uint *)(iVar2 + 0x2e7404c) = (uVar3 >> 0xe | uVar3 << 0x12) ^ (iVar1 << 0x18 | iVar1 >> 8);
    *(undefined1 *)(iVar2 + 0x2e7403b) = 1;
  }
  iVar1 = param_1[3];
  if (iVar1 < 1) {
    *(undefined4 *)(iVar2 + 0x2e74050) = 0;
    *(undefined1 *)(iVar2 + 0x2e7403c) = 0;
  }
  else {
    *(uint *)(iVar2 + 0x2e74050) = (uVar3 >> 0xd | uVar3 << 0x13) ^ (iVar1 << 0x18 | iVar1 >> 8);
    *(undefined1 *)(iVar2 + 0x2e7403c) = 1;
  }
  iVar1 = param_1[4];
  if (iVar1 < 1) {
    *(undefined4 *)(iVar2 + 0x2e74054) = 0;
    *(undefined1 *)(iVar2 + 0x2e7403d) = 0;
  }
  else {
    *(uint *)(iVar2 + 0x2e74054) = (uVar3 >> 0xc | uVar3 << 0x14) ^ (iVar1 << 0x18 | iVar1 >> 8);
    *(undefined1 *)(iVar2 + 0x2e7403d) = 1;
  }
  iVar1 = param_1[5];
  if (0 < iVar1) {
    *(uint *)(iVar2 + 0x2e74058) = (uVar3 >> 0xb | uVar3 << 0x15) ^ (iVar1 << 0x18 | iVar1 >> 8);
    *(undefined1 *)(iVar2 + 0x2e7403e) = 1;
    return;
  }
  *(undefined4 *)(iVar2 + 0x2e74058) = 0;
  *(undefined1 *)(iVar2 + 0x2e7403e) = 0;
  return;
}

