# Case Scope

## meta
- case_id: codol319-console
- created: 2026-10-16T19:30:30.0131475+08:00
- operator: local
- project_root: E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival
- primary_skill: ghidra-reverse/SKILL.md
- primary_id: R22
- lead_role: lead
- specialist_roles: []
- hint: Windows x86 PE Ghidra REA native client profile inventory consumers for CODOL 3.19.26.22
- preset: offline-sample

## auth
- status: granted
- basis: own_system
- evidence_of_auth: User requested 3.19 console feature implementation and current-version reverse analysis; original files remain read-only.
- MUST NOT proceed if status != granted

## in_scope
- assets:
  - E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival\runtime\instances\codol-3.19.26.22-911c42a0027c\game\codoMP_client_shipRetail.exe
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