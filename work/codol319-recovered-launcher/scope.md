# Case Scope

## meta
- case_id: codol319-recovered-launcher
- created: 2026-10-16T18:18:50.3399679+08:00
- operator: local
- project_root: E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival
- primary_skill: dotnet-reverse/SKILL.md
- primary_id: R5
- lead_role: lead
- specialist_roles: []
- hint: .NET C# recovered launcher source verify local PE
- preset: offline-sample

## auth
- status: granted
- basis: own_system
- evidence_of_auth: User supplied recovered launcher source as part of the authorized local CODOL319 startup migration; inspect only
- MUST NOT proceed if status != granted

## in_scope
- assets:
  - E:\Games\3.19.26.22\CODOL_FINAL\CODOL319-TestBuild\CODOL 3.19 Launcher.exe
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