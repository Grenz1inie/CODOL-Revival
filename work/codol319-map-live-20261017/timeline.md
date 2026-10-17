# Timeline (append-only)

## 2026-10-17T20:41:39.5993807+08:00 | lead | init
- action: case-init
- command_or_ref: skills/scripts/case-init.ps1
- result_summary: case directory created; scope ready_for_act=true
- artifacts: [scope.md, workitems.md]
- evidence_ids: []
- decision_delta: [case_initialized]
- carry_forward_refs: [scope.md]
- next: open PRIMARY SKILL.md and ACT within scope
## 2026-10-17 20:43 Asia/Shanghai | prepare
- carry_forward_refs: ../codol319-map-load/rea-map-consumer.analysis.json, 1dc9fc3
- decision_delta: previous processes ended; verified hashes, started fresh loopback capture and fixed A experiment
- evidence: preparation.json, session.pcapng
- next: user Ready, then validate real first-frame consumption and visible map

## 2026-10-17 | map visible
- evidence: user screenshot, map-visible.pcapng complete-block prefix, wire-summary.json, mapents-comparison.json
- decision_delta: native client acknowledged baseline and continuous world frames; loaded mp_nuked entity text matches original zone bytes
- carry_forward_refs: prior REA consumer bytes and 3.19 hash binding
- result: map display accepted; movement, weapons, minimap, teammate models and AI remain
