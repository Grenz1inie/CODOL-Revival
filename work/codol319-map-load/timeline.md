# Timeline (append-only)

## 2026-10-17T11:18:54.6218864+08:00 | lead | init
- action: case-init
- command_or_ref: skills/scripts/case-init.ps1
- result_summary: case directory created; scope ready_for_act=true
- artifacts: [scope.md, workitems.md]
- evidence_ids: []
- decision_delta: [case_initialized]
- carry_forward_refs: [scope.md]
- next: open PRIMARY SKILL.md and ACT within scope
## 2026-10-17 | map loading and first frame
- carry_forward_refs: existing udp319 REA, current EXE hash, scope.md
- decision_delta: full-image REA timeout; r2 narrowed consumers, bounded REA bytes cross-check
- evidence: rea-map-consumer.evidence.json, client-crypto.json, udp-loading.json
- result: resource-derived spawn and Rust first/continuation frames implemented; focused tests passed
- live: PID58400 reached stage6 without snapshots; user reported loading
- next: PID64480 restarted in fixed A lab, real Ready and visible map pending
