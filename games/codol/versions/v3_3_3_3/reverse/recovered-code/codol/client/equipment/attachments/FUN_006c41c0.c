// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: 配件兼容性子规则组合判断
// VA: 0x006c41c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment-tail.json
// BEGIN PSEUDOCODE

undefined4 FUN_006c41c0(undefined4 param_1)

{
  char cVar1;
  int in_EAX;
  int iVar2;
  
  if (in_EAX == 0) {
    return 1;
  }
  iVar2 = func_0x005845b0();
  if ((((iVar2 != 0) && (cVar1 = func_0x00709510(), cVar1 != '\0')) &&
      (cVar1 = func_0x00709480(param_1), cVar1 != '\0')) &&
     (cVar1 = func_0x00709570(), cVar1 != '\0')) {
    iVar2 = func_0x007095d0(param_1);
    if ((iVar2 != 8) && (cVar1 = func_0x006c2800(), cVar1 == '\0')) {
      return 0;
    }
    return 1;
  }
  return 0;
}

