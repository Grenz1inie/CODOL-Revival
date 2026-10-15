// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案序列化与扩展字段写入
// VA: 0x006d7500; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006d7500(int param_1,int param_2,uint param_3)

{
  uint uVar1;
  char cVar2;
  int iVar3;
  int extraout_ECX;
  undefined4 *puVar4;
  undefined *puVar5;
  uint uVar6;
  bool bVar7;
  int unaff_retaddr;
  undefined4 uStack_8;
  int iVar8;
  
  func_0x00afd6f0();
  puVar5 = &UNK_00c604a0;
  if (*(int *)(extraout_ECX + 100) != 1) {
    puVar5 = &UNK_00c60488;
  }
  iVar3 = func_0x0049e7d0(0x27,puVar5,1);
  param_2 = *(int *)(iVar3 + 8);
  if (0x7ffc < *(uint *)(param_2 + 0x30)) {
    func_0x00597d20(2,&UNK_00c75ed0,puVar5,*(uint *)(param_2 + 0x30),0x7ffc);
  }
  param_1 = func_0x006d7d80();
  iVar3 = func_0x006d7340(extraout_ECX + -8);
  bVar7 = iVar3 != 0;
  if (bVar7) {
    iVar8 = 0x77f3148;
  }
  else {
    iVar8 = extraout_ECX + 0x74;
    iVar3 = 0x8000;
  }
  cVar2 = func_0x007d0550(uStack_8);
  if ((((cVar2 == '\0') || (cVar2 = func_0x00a38f30(bVar7), cVar2 == '\0')) ||
      (cVar2 = func_0x00a38f30(1), cVar2 == '\0')) ||
     ((cVar2 = func_0x00a38f30(iVar8), cVar2 == '\0' ||
      (cVar2 = func_0x00a39020(uStack_8,iVar3), cVar2 == '\0')))) {
    func_0x00af6b2f();
    return;
  }
  param_1 = extraout_ECX + 0x78;
  uVar6 = 0;
  param_2 = 0x7ffc;
  param_3 = 0;
  uVar1 = *(uint *)(unaff_retaddr + 0x28);
  bVar7 = true;
  if (uVar1 < 10) {
    func_0x00630750(unaff_retaddr,(uint *)(unaff_retaddr + 0x28),0,0,&param_1,&param_3,uVar1);
  }
  puVar4 = (undefined4 *)&stack0x00000058;
  do {
    if (param_3 <= uVar6) break;
    switch(puVar4[-2]) {
    case 0:
      if (bVar7) {
        cVar2 = func_0x00a38ee0(*(undefined4 *)*puVar4);
code_r0x006d76e2:
        if (cVar2 != '\0') {
          bVar7 = true;
          goto LAB_006d76ec;
        }
      }
      break;
    case 1:
      if (bVar7) {
        cVar2 = func_0x00a38ee0(*(undefined1 *)*puVar4);
        goto code_r0x006d76e2;
      }
      break;
    default:
      goto LAB_006d76ec;
    case 3:
      if (bVar7) {
        cVar2 = func_0x00a38f80(*puVar4,puVar4[1]);
        goto code_r0x006d76e2;
      }
      break;
    case 8:
      if (bVar7) {
        cVar2 = func_0x00a38a00(*(undefined4 *)*puVar4);
        goto code_r0x006d76e2;
      }
      break;
    case 9:
      if (bVar7) {
        cVar2 = func_0x00a38ee0((int)*(short *)*puVar4);
        goto code_r0x006d76e2;
      }
    }
    bVar7 = false;
LAB_006d76ec:
    uVar6 = uVar6 + 1;
    puVar4 = puVar4 + 0x14;
  } while (bVar7);
  func_0x00af6b2f();
  return;
}

