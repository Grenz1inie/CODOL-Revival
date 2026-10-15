// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.account.profile
// Analyst label: 档案下载完成后的标志与缓存处理
// VA: 0x006d7e60; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-account-lobby-tail.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006d7e60(undefined4 param_1)

{
  int iVar1;
  int unaff_ESI;
  undefined4 uStack_10;
  undefined4 uStack_c;
  
  if ((char)param_1 != '\0') {
    *(undefined4 *)(unaff_ESI + 0x910c) = 0;
    *(undefined4 *)(unaff_ESI + 0x807c) = 0x7ffffff;
  }
  *(undefined4 *)(unaff_ESI + 0x8080) = 0;
  *(undefined2 *)(unaff_ESI + 0x9084) = 0;
  func_0x00afd440(unaff_ESI + 0x8084,0,0x1000);
  *(undefined4 *)(unaff_ESI + 0x74) = 0;
  if (((*(int *)(unaff_ESI + 0x70) == 1) && (*(int *)(unaff_ESI + 0x6c) == 1)) &&
     ((char)param_1 != '\0')) {
    func_0x005904a0();
    *(undefined1 *)(unaff_ESI + 0x9118) = 1;
    func_0x006d90c0();
  }
  if (0 < *(int *)(unaff_ESI + 0x58)) {
    if (_DAT_0788c760 == 0) {
      _DAT_03749354 = timeGetTime();
      QueryPerformanceCounter(&uStack_10);
      _DAT_03749468 = uStack_10;
      _DAT_0374946c = uStack_c;
      _DAT_0788c760 = 1;
    }
    iVar1 = timeGetTime();
    *(int *)(unaff_ESI + 0x9098) = iVar1 - _DAT_03749354;
    if ((*(int *)(unaff_ESI + 0x70) == 1) && (*(int *)(unaff_ESI + 0x6c) == 2)) {
      func_0x005b53c0(*(undefined4 *)(unaff_ESI + 0x60),*(undefined4 *)(unaff_ESI + 100),param_1);
    }
  }
  return;
}

