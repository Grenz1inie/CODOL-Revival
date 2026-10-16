// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.auth
// Analyst label: 128 字节认证票据字段读取
// VA: 0x00a678c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_00a678c0(undefined4 param_1)

{
  bool bVar1;
  char cVar2;
  undefined4 *in_ECX;
  undefined4 uStack_30;
  undefined4 uStack_2c;
  undefined1 uStack_25;
  undefined4 uStack_24;
  undefined4 uStack_20;
  undefined4 uStack_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  undefined4 uStack_10;
  undefined4 uStack_c;
  uint uStack_8;
  
  uStack_8 = _DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  uStack_24 = 0;
  cVar2 = func_0x00a3a9d0(param_1,0x80,0,&uStack_24,&uStack_2c,4);
  if (cVar2 != '\0') {
    *in_ECX = uStack_2c;
    cVar2 = func_0x00a3a9d0(param_1,0x80,uStack_24,&uStack_24,&uStack_25,1);
    if (cVar2 != '\0') {
      *(undefined1 *)(in_ECX + 1) = uStack_25;
      cVar2 = func_0x00a3a9d0(param_1,0x80,uStack_24,&uStack_24,&uStack_2c,4);
      if (cVar2 != '\0') {
        in_ECX[2] = uStack_2c;
        cVar2 = func_0x00a3a9d0(param_1,0x80,uStack_24,&uStack_24,&uStack_2c,4);
        if (cVar2 != '\0') {
          in_ECX[3] = uStack_2c;
          cVar2 = func_0x00a3a9d0(param_1,0x80,uStack_24,&uStack_24,&uStack_2c,4);
          if (cVar2 != '\0') {
            in_ECX[4] = uStack_2c;
            cVar2 = func_0x00a3a9d0(param_1,0x80,uStack_24,&uStack_24,&uStack_30,8);
            if (cVar2 != '\0') {
              in_ECX[6] = uStack_30;
              in_ECX[7] = uStack_2c;
              cVar2 = func_0x00a3a9d0(param_1,0x80,uStack_24,&uStack_24,&uStack_30,8);
              if (cVar2 != '\0') {
                in_ECX[8] = uStack_30;
                in_ECX[9] = uStack_2c;
                cVar2 = func_0x00a3a9d0(param_1,0x80,uStack_24,&uStack_24,in_ECX + 10,0x40);
                if (cVar2 != '\0') {
                  cVar2 = func_0x00a3a9d0(param_1,0x80,uStack_24,&uStack_24,&uStack_20,0x18);
                  if (cVar2 != '\0') {
                    bVar1 = true;
                    goto LAB_00a67a4c;
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  bVar1 = false;
LAB_00a67a4c:
  FUN_00a676f0(&uStack_20,1);
  uStack_20 = 0;
  uStack_1c = 0;
  uStack_18 = 0;
  uStack_14 = 0;
  uStack_10 = 0;
  uStack_c = 0;
  if (bVar1) {
    cVar2 = func_0x00a3a9d0(param_1,0x80,uStack_24,&uStack_24,in_ECX + 0x20,3);
    if (cVar2 != '\0') {
      func_0x00a3a9d0(param_1,0x80,uStack_24,&uStack_24,(int)in_ECX + 0x83,4);
    }
  }
  func_0x00af6b2f();
  return;
}

