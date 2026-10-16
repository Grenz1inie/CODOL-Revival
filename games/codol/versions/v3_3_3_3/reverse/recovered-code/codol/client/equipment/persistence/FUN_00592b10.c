// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.persistence
// Analyst label: 武器与配件缓存按 weaponClasses 路径写入档案
// VA: 0x00592b10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment-tail.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00592b10(void)

{
  int iVar1;
  int iVar2;
  uint in_ECX;
  uint uVar3;
  undefined *puVar4;
  uint *puVar5;
  bool bVar6;
  undefined1 auStack_bc [4];
  int iStack_b8;
  int iStack_b4;
  int aiStack_ac [3];
  undefined *puStack_a0;
  undefined1 *puStack_9c;
  undefined1 *puStack_98;
  undefined1 *puStack_94;
  undefined1 auStack_90 [32];
  undefined1 auStack_70 [32];
  undefined1 auStack_50 [32];
  undefined1 auStack_30 [36];
  uint uStack_c;
  
  uStack_c = _DAT_00cc7c80 ^ (uint)auStack_bc;
  iVar1 = func_0x006da140();
  if (iVar1 + 0x90 != 0) {
    uVar3 = in_ECX & 0x80000001;
    bVar6 = uVar3 == 0;
    aiStack_ac[1] = 0x7ffc;
    if ((int)uVar3 < 0) {
      bVar6 = (uVar3 - 1 | 0xfffffffe) == 0xffffffff;
    }
    puVar4 = &UNK_00c5d7c4;
    if (!bVar6) {
      puVar4 = &UNK_00c6b8ac;
    }
    puStack_a0 = &UNK_00c6c218;
    aiStack_ac[0] = iVar1 + 0x90;
    func_0x00637be0(auStack_70,5,&UNK_00c5dde0,(int)in_ECX / 2);
    puStack_98 = auStack_50;
    puStack_9c = auStack_70;
    func_0x00637be0(puStack_98,0x20,&UNK_00c6c228,puVar4);
    if (*(char *)(in_ECX * 0x28 + 0x2e74038) == '\0') {
      uVar3 = 0;
    }
    else {
      uVar3 = *(uint *)(in_ECX * 0x28 + 0x2e74040) ^ _DAT_00cdd280;
      uVar3 = uVar3 << 8 | uVar3 >> 0x18;
    }
    iVar1 = func_0x006da140();
    if (*(char *)(iVar1 + 0x9128) != '\0') {
      uVar3 = (uVar3 << 0x18 | (int)uVar3 >> 8) ^ *(uint *)(iVar1 + 0x9124);
    }
    func_0x00637be0(auStack_90,0x20,&UNK_00c5dde0,uVar3);
    FUN_005926d0(&puStack_a0,auStack_90,aiStack_ac,0,0);
    puStack_94 = auStack_30;
    func_0x00637be0(auStack_50,0x20,&UNK_00c6c230,puVar4);
    aiStack_ac[2] = in_ECX * 0x28 + 0x2e74029;
    iVar1 = 0;
    puVar5 = (uint *)(in_ECX * 0x28 + 0x2e74044);
    do {
      func_0x00637be0(auStack_30,5,&UNK_00c5dde0,iVar1);
      if (*(char *)(aiStack_ac[2] + 0x10 + iVar1) == '\0') {
        uVar3 = 0;
      }
      else {
        uVar3 = (_DAT_00cdd280 >> (0x10U - (char)iVar1 & 0x1f) |
                _DAT_00cdd280 << ((char)iVar1 + 0x10U & 0x1f)) ^ *puVar5;
        uVar3 = uVar3 << 8 | uVar3 >> 0x18;
      }
      if ((_DAT_00cd7000 == 4) || (_DAT_00cd7000 == 6)) {
        if ((_DAT_078b08bc != 0) || (_DAT_078b08c8 != 0)) {
          iVar2 = func_0x00a59520();
          iStack_b8 = *(int *)(iVar2 + 0x20);
          iStack_b4 = *(int *)(iVar2 + 0x24);
        }
        if ((_DAT_0c95bd80 != iStack_b8) || (_DAT_0c95bd84 != iStack_b4)) {
          func_0x006d9da0(0,&iStack_b8);
        }
      }
      if (DAT_0c964ea8 != '\0') {
        uVar3 = (uVar3 << 0x18 | (int)uVar3 >> 8) ^ _DAT_0c964ea4;
      }
      func_0x00637be0(auStack_90,0x20,&UNK_00c5dde0,uVar3);
      FUN_005926d0(&puStack_a0,auStack_90,aiStack_ac,0,0);
      iVar1 = iVar1 + 1;
      puVar5 = puVar5 + 1;
    } while (iVar1 < 6);
  }
  func_0x00af6b2f();
  return;
}

