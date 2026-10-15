// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.catalog
// Analyst label: 产品内物品与数量读取
// VA: 0x00706f10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_bec090c815cb4906c564a1b80c86db903d79de430a8ceb5365d116326aba222f
// BEGIN PSEUDOCODE

int FUN_00706f10(void)

{
  int iVar1;
  byte bVar2;
  ushort uVar3;
  int *in_EAX;
  ushort in_CX;
  int iVar4;
  
  *in_EAX = 0;
  if ((((in_CX != 0) && (in_CX < DAT_02dbb284)) &&
      (uVar3 = *(ushort *)(DAT_02dbb280 + (uint)in_CX * 2), uVar3 != 0)) &&
     ((uVar3 < DAT_02dbb274 && (iVar1 = DAT_02dbb270 + (uint)uVar3 * 0x18, iVar1 != 0)))) {
    bVar2 = *(byte *)(iVar1 + 10);
    iVar4 = 0;
    if (bVar2 != 0) {
      do {
        if (*in_EAX < 1000) {
          in_EAX[*in_EAX + 1] = (uint)*(ushort *)(*(int *)(iVar1 + 0xc) + iVar4 * 4);
          *in_EAX = *in_EAX + 1;
        }
        iVar4 = iVar4 + 1;
      } while (iVar4 < (int)(uint)bVar2);
    }
    return *in_EAX;
  }
  return 0;
}

