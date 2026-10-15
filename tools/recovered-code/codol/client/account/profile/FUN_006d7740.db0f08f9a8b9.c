// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案反序列化与 DDL 扩展字段读取
// VA: 0x006d7740; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby.json
// BEGIN PSEUDOCODE

/* WARNING: Removing unreachable block (ram,0x006d785c) */
/* WARNING: Removing unreachable block (ram,0x006d7880) */
/* WARNING: Removing unreachable block (ram,0x006d7887) */
/* WARNING: Removing unreachable block (ram,0x006d7890) */
/* WARNING: Removing unreachable block (ram,0x006d789a) */
/* WARNING: Removing unreachable block (ram,0x006d78a2) */
/* WARNING: Removing unreachable block (ram,0x006d78a7) */
/* WARNING: Removing unreachable block (ram,0x006d7949) */
/* WARNING: Removing unreachable block (ram,0x006d7957) */
/* WARNING: Removing unreachable block (ram,0x006d79ea) */
/* WARNING: Removing unreachable block (ram,0x006d79f6) */
/* WARNING: Removing unreachable block (ram,0x006d7a15) */
/* WARNING: Removing unreachable block (ram,0x006d7a19) */
/* WARNING: Removing unreachable block (ram,0x006d7a38) */
/* WARNING: Removing unreachable block (ram,0x006d7a2a) */
/* WARNING: Removing unreachable block (ram,0x006d7a88) */
/* WARNING: Removing unreachable block (ram,0x006d7a8c) */
/* WARNING: Removing unreachable block (ram,0x006d7a73) */
/* WARNING: Removing unreachable block (ram,0x006d7a77) */
/* WARNING: Removing unreachable block (ram,0x006d7a46) */
/* WARNING: Removing unreachable block (ram,0x006d7a4a) */
/* WARNING: Removing unreachable block (ram,0x006d7a67) */
/* WARNING: Removing unreachable block (ram,0x006d7a5b) */
/* WARNING: Removing unreachable block (ram,0x006d79fd) */
/* WARNING: Removing unreachable block (ram,0x006d7a05) */
/* WARNING: Removing unreachable block (ram,0x006d7a97) */
/* WARNING: Removing unreachable block (ram,0x006d7a9b) */
/* WARNING: Removing unreachable block (ram,0x006d7a9f) */
/* WARNING: Removing unreachable block (ram,0x006d7aa1) */
/* WARNING: Removing unreachable block (ram,0x006d7910) */
/* WARNING: Removing unreachable block (ram,0x006d7916) */
/* WARNING: Removing unreachable block (ram,0x006d7991) */
/* WARNING: Removing unreachable block (ram,0x006d79b2) */
/* WARNING: Removing unreachable block (ram,0x006d79cb) */
/* WARNING: Removing unreachable block (ram,0x006d79d5) */
/* WARNING: Removing unreachable block (ram,0x006d79e0) */
/* WARNING: Removing unreachable block (ram,0x006d77bc) */
/* WARNING: Removing unreachable block (ram,0x006d78c5) */
/* WARNING: Removing unreachable block (ram,0x006d78c9) */
/* WARNING: Removing unreachable block (ram,0x006d791a) */
/* WARNING: Removing unreachable block (ram,0x006d78d9) */
/* WARNING: Removing unreachable block (ram,0x006d7ab4) */
/* WARNING: Removing unreachable block (ram,0x006d7ac2) */
/* WARNING: Removing unreachable block (ram,0x006d7ac9) */
/* WARNING: Removing unreachable block (ram,0x006d795e) */
/* WARNING: Recovered jumptable eliminated as dead code */
/* WARNING: Removing unreachable block (ram,0x006d7987) */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006d7740(void)

{
  bool bVar1;
  char cVar2;
  int iVar3;
  int extraout_ECX;
  
  func_0x00afd6f0();
  iVar3 = func_0x0049e7d0();
  if (0x7ffc < *(uint *)(*(int *)(iVar3 + 8) + 0x30)) {
    func_0x00597d20();
  }
  cVar2 = func_0x00a5a370();
  if ((cVar2 == '\0') || (cVar2 = func_0x00a38a60(), cVar2 == '\0')) {
    bVar1 = false;
  }
  else {
    bVar1 = true;
  }
  if (((bVar1) && (cVar2 = func_0x00a38a60(), cVar2 != '\0')) &&
     (cVar2 = func_0x00a38a60(), cVar2 != '\0')) {
    bVar1 = true;
  }
  else {
    bVar1 = false;
  }
  if ((bVar1) && (cVar2 = func_0x00a392b0(), cVar2 != '\0')) {
    bVar1 = true;
  }
  else {
    bVar1 = false;
  }
  func_0x00af7221();
  if (bVar1) {
    func_0x006d7d80();
  }
  else if (*(int *)(extraout_ECX + 0x6c) == 1) {
    *(undefined1 *)(extraout_ECX + 0x9090) = 1;
    FUN_006d7c70();
    FUN_006d7ce0();
    *(undefined4 *)(extraout_ECX + 0x807c) = 0x7ffffff;
    func_0x00af6b2f();
    return;
  }
  func_0x00af6b2f();
  return;
}

