// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 公开或私有 DDL 版本头初始化
// VA: 0x006d7ce0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_7d8cc19d471049d1a3ff1531d2d7ad1c114afe76de7bce5db1ab31474a9e3db0
// BEGIN PSEUDOCODE

void FUN_006d7ce0(void)

{
  undefined4 *puVar1;
  int iVar2;
  char *pcVar3;
  int unaff_EDI;
  
  pcVar3 = "mp/playerdata.def";
  if (*(int *)(unaff_EDI + 0x6c) != 1) {
    pcVar3 = "mp/playersecuredata.def";
  }
  iVar2 = FUN_0049e7d0(0x27,pcVar3,1);
  puVar1 = *(undefined4 **)(iVar2 + 8);
  if (0x7ffc < (uint)puVar1[0xc]) {
    FUN_00597d20(2,"943 %s %d %d",pcVar3,puVar1[0xc],0x7ffc);
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

