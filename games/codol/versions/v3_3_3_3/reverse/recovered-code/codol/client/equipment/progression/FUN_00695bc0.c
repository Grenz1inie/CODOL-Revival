// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.progression
// Analyst label: 按武器 ID 读取库存信息
// VA: 0x00695bc0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_718db7bd71d68e91b7c9cac3baa12f12b6a25b87d812f6b350fc50fb7ef92f4b
// BEGIN PSEUDOCODE

void FUN_00695bc0(int param_1,int *param_2)

{
  char cVar1;
  uint uVar2;
  int iVar3;
  
  uVar2 = 0;
  if (DAT_0c8031d8 != 0) {
    do {
      if (param_1 == *(int *)(DAT_0c8031d0 + uVar2 * 4)) {
        *param_2 = param_1;
        *(undefined2 *)(param_2 + 1) = 0;
        param_2[2] = 0;
        param_2[4] = 0;
        param_2[5] = 0;
        param_2[6] = 0;
        param_2[7] = 0;
        return;
      }
      uVar2 = uVar2 + 1;
    } while (uVar2 < DAT_0c8031d8);
  }
  if (DAT_0783f860 != 0) {
    iVar3 = FUN_004a7a50();
    if (iVar3 == 0) {
      cVar1 = FUN_00695a10();
      *param_2 = param_1;
      param_2[6] = 0;
      param_2[7] = 0;
      param_2[5] = 0;
      if (cVar1 == '\0') {
        *(undefined2 *)(param_2 + 1) = 0;
        param_2[2] = 0;
        param_2[4] = 0;
        return;
      }
      *(undefined2 *)(param_2 + 1) = 1;
      param_2[8] = -1;
      param_2[9] = 0;
      param_2[2] = -1;
      param_2[4] = -1;
      return;
    }
    FUN_00695a80(param_2,iVar3);
  }
  return;
}

