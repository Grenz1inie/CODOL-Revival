# Case Scope

## meta
- case_id: codol319-rebuild
- created: 2026-10-17T09:24:25.6439220+08:00
- operator: local
- project_root: E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival
- primary_skill: ghidra-reverse/SKILL.md
- primary_id: R22
- lead_role: lead
- specialist_roles: []
- hint: Ghidra Windows x86 PE offline game fastfile resource reconstruction
- preset: offline-sample

## auth
- status: granted
- basis: own_system
- evidence_of_auth: User authorized original-game resource reconstruction, local source implementation and staged commits; original files and running services remain unchanged.
- MUST NOT proceed if status != granted

## in_scope
- assets:
  - E:\Games\3.19.26.22\CODOL_FINAL\CODOL_FINAL\使命召唤OL_final\使命召唤OL_final\codoMP_client_shipRetail.exe
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