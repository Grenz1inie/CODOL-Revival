// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.auth
// Analyst label: 128 字节认证票据字段读取
// VA: 0x00a678c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_806f8b8a073991ad1b8b2ed6e34540407266a15ab204346b21850a5fbc77728d
// BEGIN PSEUDOCODE

void FUN_00a678c0(undefined4 param_1)

{
  bool bVar1;
  char cVar2;
  undefined4 *in_ECX;
  undefined4 local_30;
  undefined4 local_2c;
  undefined1 local_25;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 local_14;
  undefined4 local_10;
  undefined4 local_c;
  uint local_8;
  
  local_8 = DAT_00cc7c80 ^ (uint)&stack0xfffffffc;
  local_24 = 0;
  cVar2 = FUN_00a3a9d0(param_1,0x80,0,&local_24,&local_2c,4);
  if (cVar2 != '\0') {
    *in_ECX = local_2c;
    cVar2 = FUN_00a3a9d0(param_1,0x80,local_24,&local_24,&local_25,1);
    if (cVar2 != '\0') {
      *(undefined1 *)(in_ECX + 1) = local_25;
      cVar2 = FUN_00a3a9d0(param_1,0x80,local_24,&local_24,&local_2c,4);
      if (cVar2 != '\0') {
        in_ECX[2] = local_2c;
        cVar2 = FUN_00a3a9d0(param_1,0x80,local_24,&local_24,&local_2c,4);
        if (cVar2 != '\0') {
          in_ECX[3] = local_2c;
          cVar2 = FUN_00a3a9d0(param_1,0x80,local_24,&local_24,&local_2c,4);
          if (cVar2 != '\0') {
            in_ECX[4] = local_2c;
            cVar2 = FUN_00a3a9d0(param_1,0x80,local_24,&local_24,&local_30,8);
            if (cVar2 != '\0') {
              in_ECX[6] = local_30;
              in_ECX[7] = local_2c;
              cVar2 = FUN_00a3a9d0(param_1,0x80,local_24,&local_24,&local_30,8);
              if (cVar2 != '\0') {
                in_ECX[8] = local_30;
                in_ECX[9] = local_2c;
                cVar2 = FUN_00a3a9d0(param_1,0x80,local_24,&local_24,in_ECX + 10,0x40);
                if (cVar2 != '\0') {
                  cVar2 = FUN_00a3a9d0(param_1,0x80,local_24,&local_24,&local_20,0x18);
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
  FUN_00a676f0(&local_20,1);
  local_20 = 0;
  local_1c = 0;
  local_18 = 0;
  local_14 = 0;
  local_10 = 0;
  local_c = 0;
  if (bVar1) {
    cVar2 = FUN_00a3a9d0(param_1,0x80,local_24,&local_24,in_ECX + 0x20,3);
    if (cVar2 != '\0') {
      FUN_00a3a9d0(param_1,0x80,local_24,&local_24,(int)in_ECX + 0x83,4);
    }
  }
  __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
  return;
}

