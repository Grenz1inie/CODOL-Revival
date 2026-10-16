# Case Scope

## meta
- case_id: codol319-nuketown
- created: 2026-10-16T22:46:29.3201315+08:00
- operator: local
- project_root: E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival
- primary_skill: ghidra-reverse/SKILL.md
- primary_id: R22
- lead_role: lead
- specialist_roles: []
- hint: Windows x86 CODOL 3.19 Ghidra REA static decompile room protocol
- preset: offline-sample

## auth
- status: granted
- basis: own_system
- evidence_of_auth: User requested 3.19 Nuketown 9v9 Rust server, isolated local instance, passive capture and bounded read-only extraction; no original game or save modification
- MUST NOT proceed if status != granted

## in_scope
- assets:
  - E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival\runtime\instances\codol-3.19.26.22-911c42a0027c\game\codoMP_client_shipRetail.exe
  - 127.0.0.1:31900
  - 127.0.0.1:31901
  - 127.0.0.1:28970
- surfaces: []
- activities: []

## out_of_scope
- assets: []
- activities: [dos, phishing_real_users, unrestricted_exfil]

## network_profile
- mode: lab_only
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