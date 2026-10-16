// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.loadout
// Analyst label: 武器装备写入路径
// VA: 0x006c1e70; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/profile-write.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006c1e70(int param_1)

{
  byte bVar1;
  char cVar2;
  int iVar3;
  int iVar4;
  uint in_ECX;
  byte *pbVar5;
  bool bVar6;
  undefined1 auStack_84 [4];
  int iStack_80;
  byte *pbStack_7c;
  undefined4 uStack_24;
  undefined4 uStack_20;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  undefined4 uStack_10;
  uint uStack_c;
  
  uStack_c = _DAT_00cc7c80 ^ (uint)auStack_84;
  func_0x007051e0();
  func_0x006bf0c0();
  if ((_DAT_077ea4ec == 0) && (iVar3 = func_0x006c33c0(0xffffffff), 9 < iVar3)) goto LAB_006c1fd0;
  iVar3 = func_0x007051e0();
  if (iVar3 == -1) {
    func_0x007051e0();
  }
  if (param_1 == 0) {
LAB_006c1f2c:
    if (((in_ECX == 0) && (cVar2 = func_0x006c2800(), cVar2 != '\0')) &&
       (func_0x00707c40(), 0 < iStack_80)) {
      pbVar5 = &UNK_00c7c87c;
      do {
        bVar1 = *pbStack_7c;
        bVar6 = bVar1 < *pbVar5;
        if (bVar1 != *pbVar5) {
LAB_006c1f80:
          iVar4 = (1 - (uint)bVar6) - (uint)(bVar6 != 0);
          goto LAB_006c1f85;
        }
        if (bVar1 == 0) break;
        bVar1 = pbStack_7c[1];
        bVar6 = bVar1 < pbVar5[1];
        if (bVar1 != pbVar5[1]) goto LAB_006c1f80;
        pbStack_7c = pbStack_7c + 2;
        pbVar5 = pbVar5 + 2;
      } while (bVar1 != 0);
      iVar4 = 0;
LAB_006c1f85:
      if (iVar4 == 0) {
        func_0x00706740();
        func_0x006c29e0(iVar3);
      }
    }
  }
  else {
    iVar4 = func_0x005845b0();
    if (iVar4 == 0) goto LAB_006c1fd0;
    iVar4 = func_0x005845b0();
    if (iVar4 == 0) {
      bVar1 = 10;
    }
    else {
      bVar1 = *(byte *)(iVar4 + 6);
    }
    if (5 < bVar1 == in_ECX) goto LAB_006c1f2c;
    if ((in_ECX != 1) || (cVar2 = func_0x006c2800(), cVar2 == '\0')) goto LAB_006c1fd0;
  }
  uStack_24 = 0;
  uStack_20 = 0;
  uStack_1c = 0;
  uStack_18 = 0;
  uStack_14 = 0;
  uStack_10 = 0;
  func_0x005946c0(&uStack_24);
  func_0x005948f0();
LAB_006c1fd0:
  func_0x00af6b2f();
  return;
}

