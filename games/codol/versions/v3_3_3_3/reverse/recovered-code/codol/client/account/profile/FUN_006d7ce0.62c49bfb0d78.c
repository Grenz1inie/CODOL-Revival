// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 公开或私有 DDL 版本头初始化
// VA: 0x006d7ce0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

void FUN_006d7ce0(void)

{
  undefined4 *puVar1;
  int iVar2;
  undefined *puVar3;
  int unaff_EDI;
  
  puVar3 = &UNK_00c604a0;
  if (*(int *)(unaff_EDI + 0x6c) != 1) {
    puVar3 = &UNK_00c60488;
  }
  iVar2 = func_0x0049e7d0(0x27,puVar3,1);
  puVar1 = *(undefined4 **)(iVar2 + 8);
  if (0x7ffc < (uint)puVar1[0xc]) {
    func_0x00597d20(2,&UNK_00c75ed0,puVar3,puVar1[0xc],0x7ffc);
  }
  *(undefined1 *)(unaff_EDI + 0x80) = *(undefined1 *)puVar1;
  *(char *)(unaff_EDI + 0x81) = (char)((uint)*puVar1 >> 8);
  *(undefined1 *)(unaff_EDI + 0x82) = *(undefined1 *)((int)puVar1 + 2);
  *(undefined1 *)(unaff_EDI + 0x83) = *(undefined1 *)((int)puVar1 + 3);
  *(undefined1 *)(unaff_EDI + 0x84) = *(undefined1 *)(puVar1 + 1);
  *(undefined1 *)(unaff_EDI + 0x85) = *(undefined1 *)((int)puVar1 + 5);
  *(undefined1 *)(unaff_EDI + 0x86) = *(undefined1 *)((int)puVar1 + 6);
  *(undefined1 *)(unaff_EDI + 0x87) = *(undefined1 *)((int)puVar1 + 7);
  return;
}

