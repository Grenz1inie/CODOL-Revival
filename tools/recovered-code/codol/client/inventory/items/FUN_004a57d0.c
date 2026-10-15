// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.items
// Analyst label: 库存结果消费路径
// VA: 0x004a57d0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_62b6c641a80115cc8af23d1b718afabc77d48612d9993ac6e356b27bcfd074a4
// BEGIN PSEUDOCODE

void FUN_004a57d0(void)

{
  int iVar1;
  undefined1 *puVar2;
  int unaff_ESI;
  int unaff_EDI;
  
  if (unaff_EDI == 0) {
    iVar1 = 0;
  }
  else {
    iVar1 = *(int *)(*(int *)(unaff_EDI + 4) + 4) + 4 + unaff_EDI;
  }
  FUN_00864fb0(iVar1);
  if (unaff_EDI == 0) {
    iVar1 = 0;
  }
  else {
    iVar1 = unaff_EDI + 8;
  }
  if (iVar1 != 0) {
    iVar1 = *(int *)(*(int *)(iVar1 + 4) + 4) + 4 + iVar1;
  }
  FUN_00864fb0(iVar1);
  FUN_00a45750(unaff_EDI + 0x10);
  *(undefined4 *)(unaff_ESI + 0x30) = *(undefined4 *)(unaff_EDI + 0x30);
  *(undefined4 *)(unaff_ESI + 0x34) = *(undefined4 *)(unaff_EDI + 0x34);
  *(undefined4 *)(unaff_ESI + 0x38) = *(undefined4 *)(unaff_EDI + 0x38);
  puVar2 = (undefined1 *)(unaff_ESI + 0x3c);
  iVar1 = 0x40;
  do {
    *puVar2 = puVar2[unaff_EDI - unaff_ESI];
    puVar2 = puVar2 + 1;
    iVar1 = iVar1 + -1;
  } while (iVar1 != 0);
  *(undefined1 *)(unaff_ESI + 0x7c) = *(undefined1 *)(unaff_EDI + 0x7c);
  *(undefined4 *)(unaff_ESI + 0x80) = *(undefined4 *)(unaff_EDI + 0x80);
  *(undefined4 *)(unaff_ESI + 0x88) = *(undefined4 *)(unaff_EDI + 0x88);
  *(undefined4 *)(unaff_ESI + 0x8c) = *(undefined4 *)(unaff_EDI + 0x8c);
  *(undefined2 *)(unaff_ESI + 0x90) = *(undefined2 *)(unaff_EDI + 0x90);
  *(undefined4 *)(unaff_ESI + 0x94) = *(undefined4 *)(unaff_EDI + 0x94);
  *(undefined1 *)(unaff_ESI + 0x98) = *(undefined1 *)(unaff_EDI + 0x98);
  return;
}

