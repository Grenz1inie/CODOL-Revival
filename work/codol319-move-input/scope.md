# Case Scope

## meta
- case_id: codol319-move-input
- created: 2026-10-17T21:16:05.3709209+08:00
- operator: local
- project_root: E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival
- primary_skill: protocol-reverse/SKILL.md
- primary_id: R21
- lead_role: lead
- specialist_roles: []
- hint: CODOL 3.19 Nuketown: decode real client move/usercmd packets from loopback pcapng against native REA evidence, implement minimal movement loop in repo Rust match-server
- preset: offline-sample

## auth
- status: granted
- basis: own_system
- evidence_of_auth: AGENTS.md 2026-10-14/15/16/17 user authorizations: local repo development + staged local commits (no push), read-only CODOL client extraction, fixed A-drive isolated experiment, loopback captures
- MUST NOT proceed if status != granted

## in_scope
- assets:
  - E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival\work\codol319-map-live-20261017\session.pcapng
- surfaces: []
- activities: []

## out_of_scope
- assets: []
- activities: [dos, phishing_real_users, unrestricted_exfil]

## network_profile
- mode: offline
- notes: |
    offline | lab_only | authorized_target_only | unrestricted_lab
    Change mode only after auth.status = granted.

## deliverables
- report: true
- field_journal: true
- diagrams: true
- timeline: true

## constraints
- timebox: {}
- stealth: low
- data_handling: anonymize

## signoff
- ready_for_act: true
- checklist:
  - [x] auth.status = granted
  - [x] in_scope.assets non-empty OR offline sample path set
  - [x] network_profile.mode chosen
  - [ ] out_of_scope reviewed
  - [ ] roles assigned (see skills/ops/role-map.md)

## ops_refs
- skills/ops/scope-contract.md
- skills/ops/evidence-finding-path.md
- skills/ops/role-map.md
- skills/ops/timeline-workitem.md
- skills/ops/IDENTITY.md