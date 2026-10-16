// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.progression
// Analyst label: 库存信息提取（含经验）
// VA: 0x00695a80; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_a4a7a10329de9081bbf0ab2c0f7ecf42ccfe51f00f8e65ac7853147d38429de4
// BEGIN PSEUDOCODE

void FUN_00695a80(uint *param_1,char *param_2)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  
  if (((DAT_0783f860 == 0) || (param_2 == (char *)0x0)) || (*param_2 == '\0')) {
    uVar3 = 0;
  }
  else {
    uVar3 = (*(uint *)(param_2 + 4) ^ DAT_00cdc27c) << 8 |
            (*(uint *)(param_2 + 4) ^ DAT_00cdc27c) >> 0x18;
  }
  *(undefined2 *)(param_1 + 1) = 0;
  param_1[2] = 0;
  param_1[4] = 0;
  param_1[5] = 0;
  param_1[6] = 0;
  param_1[7] = 0;
  *param_1 = uVar3;
  iVar1 = FUN_005845b0();
  if (iVar1 != 0) {
    uVar2 = 0;
    if (DAT_0c8031d8 != 0) {
      do {
        if (uVar3 == *(uint *)(DAT_0c8031d0 + uVar2 * 4)) {
          return;
        }
        uVar2 = uVar2 + 1;
      } while (uVar2 < DAT_0c8031d8);
    }
    *(undefined1 *)(param_1 + 1) = 1;
    param_1[2] = *(uint *)(param_2 + 0xc);
    param_1[4] = *(uint *)(param_2 + 0x10);
    param_1[5] = *(uint *)(param_2 + 0x14);
    param_1[6] = *(uint *)(param_2 + 8);
    param_1[7] = *(uint *)(param_2 + 0x18);
    param_1[10] = *(uint *)(param_2 + 0x1c);
    if (((uVar3 != 0) && (iVar1 = FUN_005845b0(), iVar1 != 0)) &&
       ((*(byte *)(iVar1 + 0x20) & 2) != 0)) {
      *(undefined1 *)((int)param_1 + 5) = 0;
      param_1[9] = 0;
      param_1[5] = 0;
      param_1[4] = 0xffffffff;
      param_1[2] = 0xffffffff;
      param_1[8] = 0xffffffff;
      return;
    }
    if ((*(int *)(param_2 + 0xc) != 0) && (*(int *)(param_2 + 0xc) != -1)) {
      uVar3 = FUN_006fc940();
      uVar2 = *(uint *)(param_2 + 0xc) - uVar3;
      uVar3 = -(uint)(*(uint *)(param_2 + 0xc) < uVar3);
      param_1[8] = uVar2;
      param_1[9] = uVar3;
      if (((int)uVar3 < 1) && (((int)uVar3 < 0 || (uVar2 == 0)))) {
        *(undefined1 *)((int)param_1 + 5) = 1;
        return;
      }
      *(undefined1 *)((int)param_1 + 5) = 0;
      return;
    }
    *(undefined1 *)((int)param_1 + 5) = 0;
    param_1[9] = 0;
    param_1[5] = 0;
    param_1[4] = 0xffffffff;
    param_1[2] = 0xffffffff;
    param_1[8] = 0xffffffff;
  }
  return;
}

