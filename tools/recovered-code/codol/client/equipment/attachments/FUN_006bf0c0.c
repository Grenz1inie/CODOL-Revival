// REA/Ghidra pseudocode; not original or directly buildable source.
// Package: codol.client.equipment.attachments
// Analyst label: 读取所选武器与配件到编辑缓存
// VA: 0x006bf0c0; binary SHA256: e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b
// Evidence: evidence/focused/round2-inventory-equipment.json
// BEGIN PSEUDOCODE

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_006bf0c0(void)

{
  int in_EAX;
  
  if (in_EAX == -1) {
    FUN_007051e0();
  }
  _DAT_077ea4ec = 0;
  _DAT_077ea4fc = 0;
  _DAT_077ea500 = 0;
  _DAT_077ea504 = 0;
  _DAT_077ea508 = 0;
  _DAT_077ea50c = 0;
  _DAT_077ea510 = 0;
  func_0x005945b0(&DAT_077ea4ec);
  return;
}

