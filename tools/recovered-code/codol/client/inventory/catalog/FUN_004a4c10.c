// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.inventory.catalog
// Analyst label: 转生和等级阈值解释
// VA: 0x004a4c10; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: ev_8cee2742af9e42fa32d9ec48864924683c55e58148a5b55dee7e3e79a979264c
// BEGIN PSEUDOCODE

void FUN_004a4c10(int param_1,int *param_2,int *param_3)

{
  char cVar1;
  char cVar2;
  char *in_EAX;
  char *pcVar3;
  int iVar4;
  
  if (((in_EAX == (char *)0x0) || (*in_EAX == '\0')) || (param_1 < 1)) {
LAB_004a4c83:
    *param_2 = -1;
    *param_3 = -1;
    return;
  }
  pcVar3 = "uf_prestige_rank";
  iVar4 = 0x10;
  do {
    cVar1 = (in_EAX + -0xc65d68)[(int)pcVar3];
    cVar2 = *pcVar3;
    pcVar3 = pcVar3 + 1;
    if (iVar4 == 0) break;
    if (cVar1 != cVar2) {
      if ((char)((cVar2 <= cVar1) * '\x02') != '\x01') goto LAB_004a4c83;
      break;
    }
    iVar4 = iVar4 + -1;
  } while (cVar1 != '\0');
  *param_2 = param_1 / 100;
  *param_3 = param_1 % 100;
  return;
}

