// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.persistence
// Analyst label: DDL 资源边界和字段路径检查及写入包装
// VA: 0x005926d0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment-tail.json
// BEGIN PSEUDOCODE

void FUN_005926d0(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
                 int param_5)

{
  char cVar1;
  int in_EAX;
  int iVar2;
  undefined *puVar3;
  uint uVar4;
  
  if ((char)param_5 == '\0') {
    iVar2 = func_0x0049e7d0(0x27,&UNK_00c604a0,1);
    uVar4 = *(uint *)(*(int *)(iVar2 + 8) + 0x30);
    if (uVar4 < 0x7ffd) goto LAB_00592741;
    puVar3 = &UNK_00c604a0;
  }
  else {
    iVar2 = func_0x0049e7d0(0x27,&UNK_00c60488,1);
    uVar4 = *(uint *)(*(int *)(iVar2 + 8) + 0x30);
    if (uVar4 < 0x7ffd) goto LAB_00592741;
    puVar3 = &UNK_00c60488;
  }
  func_0x00597d20(2,&UNK_00c75ed0,puVar3,uVar4,0x7ffc);
LAB_00592741:
  cVar1 = func_0x00630940(param_1);
  if (cVar1 == '\0') {
    func_0x00597d20(2,&UNK_00c5e4e4);
    return;
  }
  if (param_5 != in_EAX) {
    func_0x00597d20(2,&UNK_00c5e4f0);
    return;
  }
  iVar2 = func_0x00592470(param_3,param_4);
  if ((iVar2 != 0) && (iVar2 != 1)) {
    func_0x00597d20(2,&UNK_00c6c1dc,*(undefined4 *)(iVar2 * 4 + 0xcda318));
  }
  return;
}

