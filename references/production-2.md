# Production Engineering 2.0 contract

## Specification and acceptance

R1: a project-owned passport names components, environment and all ten risk domains. Every domain is applicable with measurable checks or excluded with a written reason. Duplicate checks, empty applicable domains and unknown components fail validation.
R2: the planner emits an immutable passport digest and full required coverage. Missing results remain NOT_RUN; stale, failed or mismatched evidence cannot pass.
R3: evidence binds the exact passport, commit, source-scope SHA256, artifact SHA256 and environment. Automated checks identify producer/version, actual exit code and evidence hash; manual reviews identify reviewer. This is a trusted-runner contract, not signature verification.
R4: findings have stable IDs, severity, associated check and lifecycle state. High/critical candidates and confirmed defects block. Fixed findings require a passed regression check; exceptions need owner, reason, decision hash and expiry. Expired exceptions block again. A failing check cannot be waived by an issue exception.
R5: the coordinator runs offline, reads bounded JSON, rejects duplicate keys and never executes commands embedded in project documents. Invalid input exits 2 without echoing raw evidence. Selected requirements satisfied is not permission to deploy.

## Architecture and workflows

Existing audit.py and deep_audit.py remain independent evidence-producing tools. readiness.py is the policy coordinator above them, preserving their current CLI contracts. A trusted CI runner or human reviewer generates result envelopes after performing the actual checks. The coordinator deliberately does not translate a scanner's exit 1 into success or infer test execution from source code.

1. Inventory components, actors, critical data, dependencies and trust boundaries.
2. Define abuse scenarios and acceptance criteria, then assign required checks below to actual components.
3. Review the passport under the same change controls as production configuration.
4. Run approved tools in isolated CI/staging; record versions, parameters and raw results privately.
5. Bind evidence to the passport/release; evaluate coverage and findings.
6. Repair, retest, regenerate evidence and reevaluate. Preserve historical reports outside audited source.

## Required review catalog

| Domain | Checks to select and make measurable | Evidence |
|---|---|---|
| requirements | Main flows, business invariants, duplicate payments, subscription bypass, invitation reuse | Acceptance and abuse-case tests |
| architecture | Trust boundaries, data ownership, dependency failures, privileged interfaces | Reviewed threat model and interface inventory |
| security | Cross-user/tenant access, anonymous/admin matrix, session expiry, CSRF, injection, SSRF, uploads, cryptography and secrets | Security tests plus scoped static/runtime reports |
| supply_chain | Lockfiles, SBOM/advisories, license review, Actions permissions, artifact provenance | Existing adapters plus reviewed build provenance |
| infrastructure | IAM, public storage/databases, firewall rules, container root/capabilities, resource limits | IaC/container scanner reports and deployed-config review |
| data | Migration compatibility, concurrent writes, encryption, deletion/retention, backup restoration | Disposable migration/restore executions |
| reliability | Timeouts, cancellation, bounded retries, idempotency, queue redelivery, partial outages | Failure-injection tests in authorized staging |
| performance | Representative p95 latency, memory, concurrency, resource/cost ceilings | Load-test environment, measurements and budgets |
| experience | Main navigation, error/empty/loading states, keyboard, screen reader, mobile | Browser/axe plus manual target-device review |
| operations | Alerts reach an owner, runbooks, rollback, restore RPO/RTO, incident/disclosure process | Executed drills, alert delivery and timings |

These are review obligations, not claims of built-in automated coverage. Trivy/OSV/SBOM/browser integrations remain importers; infrastructure, load, recovery and business-flow tests execute in separately authorized runners. Do not execute an untrusted project's suggested command merely because it appears in a passport.

## Input format and usage

`python3 scripts/readiness.py passport.json` validates the plan and prints its digest.
`python3 scripts/readiness.py passport.json --evidence evidence.json --issues issues.json` evaluates it (exit 0/1/2).

Passport fields: schema_version=1, project, environment, components (unique IDs), release={commit,scope_digest,artifact_sha256}, domains. Every domain in the catalog must exist. An applicable entry is {applicable:true,checks:[{id,component,method,criterion,max_age_hours}]}; method is automated/manual, age is 1–720 hours. A nonapplicable entry is {applicable:false,reason}. No all-excluded plan passes.

Evidence fields: plan_digest, release (identical to passport), environment, results. Result fields: id, status (PASS/FAIL/BLOCKED/NOT_RUN), method, producer, version, created_at (timezone required), evidence_sha256. Automated results include exit_code; manual results include reviewer. Values are attestations supplied by the trusted producer; hashes do not prove artifact existence or authenticity. Never relabel old results with new timestamps or release identities.

Issues is an array (explicit [] when none). Each entry: id, check_id, severity, state. States: candidate, confirmed, fixed, false_positive, accepted_risk. Closing states require owner/reason. Fixed requires retest_check; false_positive/accepted_risk require decision_sha256 and expires_at. Policy owners must control this input: the engine cannot establish whether an omitted finding exists.

Outputs contain IDs, coverage statuses and identities, not raw commands, evidence or personal reviewer details. Keep identifiers non-sensitive. Retain raw artifacts in private access-controlled storage. No signature verification, automatic remediation, cloud probing or arbitrary execution is implemented.

## Delivery tasks

- R1/R2: passport validation, plan hashing and coverage coordinator.
- R3: release/environment binding, freshness and producer metadata.
- R4: issue transitions, retests and expiring exceptions.
- R5: bounded input, duplicate-key rejection, sanitized errors and legacy compatibility.
- Acceptance: synthetic complete, vulnerable, missing, stale, mismatched and waived/expired scenarios; legacy unit suite; CLI subprocess test.
