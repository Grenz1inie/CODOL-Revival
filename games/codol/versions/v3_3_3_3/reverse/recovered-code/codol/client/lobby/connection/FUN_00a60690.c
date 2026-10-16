// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.lobby.connection
// Analyst label: 连接建立轮询与发送队列推进
// VA: 0x00a60690; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby-tail.json
// BEGIN PSEUDOCODE

bool FUN_00a60690(void)

{
  char cVar1;
  int iVar2;
  undefined4 uVar3;
  int in_ECX;
  int extraout_EDX;
  float10 fVar4;
  float10 fVar5;
  int iStack_8;
  
  iStack_8 = in_ECX;
  if (*(undefined4 **)(in_ECX + 0x638) != (undefined4 *)0x0) {
    (**(code **)**(undefined4 **)(in_ECX + 0x638))();
  }
  func_0x00b2c1f0();
  if (*(int *)(in_ECX + 200) == 1) {
    iStack_8 = 1;
    cVar1 = func_0x00b2cbf0(&iStack_8);
    if (cVar1 == '\0') {
      if (iStack_8 == 1) {
        fVar4 = (float10)func_0x00a385a0();
        if ((float10)30.0 < fVar4) {
          func_0x00a53d80();
          func_0x00596bf0(0x15);
          func_0x00a613c0();
          return false;
        }
        return true;
      }
LAB_00a607dc:
      func_0x00a53d80(iStack_8);
      func_0x00596bf0(0x14);
      func_0x00a613c0();
      return false;
    }
    if (iStack_8 != 1) goto LAB_00a607dc;
    *(undefined4 *)(in_ECX + 200) = 2;
    func_0x00a61250(1);
  }
  iVar2 = *(int *)(in_ECX + 200);
  while( true ) {
    if ((iVar2 != 2) || (*(int *)(in_ECX + 0xc0) == 0)) {
      cVar1 = func_0x00a61400();
      if (cVar1 == '\0') {
        return false;
      }
      fVar4 = (float10)func_0x00a385a0();
      fVar5 = (float10)*(int *)(in_ECX + 0x10c);
      if (*(int *)(in_ECX + 0x10c) < 0) {
        fVar5 = fVar5 + (float10)4.2949673e+09;
      }
      if (fVar5 < fVar4) {
        func_0x00a53d80();
        func_0x00596bf0(0x1d);
        func_0x00a613c0();
      }
      return true;
    }
    func_0x0077dbd0();
    cVar1 = func_0x00b28cc0();
    iVar2 = extraout_EDX;
    if (cVar1 != '\0') break;
LAB_00a60756:
    if (iVar2 < 1) goto LAB_00a60877;
    uVar3 = func_0x00949cb0(iVar2);
    iVar2 = func_0x00b2cc10(uVar3);
    if (iVar2 < 1) goto LAB_00a6087c;
    func_0x00a38580();
    func_0x00a5f840(iVar2);
    func_0x00b2c2a0(iVar2 + 0x28);
    iVar2 = func_0x00a5fb70(iVar2);
    if ((iVar2 == 0) && (iVar2 = *(int *)(in_ECX + 0xb8), iVar2 != 0)) {
      *(undefined4 *)(in_ECX + 0xb8) = *(undefined4 *)(iVar2 + 0x18);
      if (iVar2 == *(int *)(in_ECX + 0xbc)) {
        *(undefined4 *)(in_ECX + 0xbc) = *(undefined4 *)(iVar2 + 0x1c);
      }
      else {
        *(undefined4 *)(*(int *)(iVar2 + 0x18) + 0x1c) = *(undefined4 *)(iVar2 + 0x1c);
      }
      func_0x00a5fe70();
      func_0x00a38040(iVar2);
      *(int *)(in_ECX + 0xc0) = *(int *)(in_ECX + 0xc0) + -1;
    }
    iVar2 = *(int *)(in_ECX + 200);
  }
  iVar2 = func_0x0077dbd0();
  iVar2 = func_0x00b2c280(iVar2 + 0x28);
  if (0 < iVar2) {
    iVar2 = iVar2 + -0x28;
    goto LAB_00a60756;
  }
LAB_00a60877:
  iVar2 = -2;
LAB_00a6087c:
  switch(iVar2) {
  case -0xb:
    func_0x00a53d80();
    uVar3 = 0x1b;
    break;
  case -10:
    func_0x00a53d80();
    uVar3 = 0x1a;
    break;
  default:
    func_0x00a53d80();
    uVar3 = 0x1c;
    break;
  case -7:
    func_0x00a53d80();
    uVar3 = 0x17;
    break;
  case -6:
  case -5:
    uVar3 = 0x19;
    break;
  case -4:
  case -2:
    goto code_r0x00a608d2;
  case -3:
    func_0x00a53d80();
    uVar3 = 0x16;
    break;
  case -1:
    func_0x00a53d80();
    uVar3 = 0x18;
  }
  func_0x00596bf0(uVar3);
  func_0x00a613c0();
code_r0x00a608d2:
  return *(int *)(in_ECX + 200) == 2;
}

