# Production Engineering — specification v1

## Goal and users
A reusable agent workflow plus a local Python 3.11+ audit CLI for project owners and coding agents. Preserve Spec Kit requirements → plan → tasks → implementation → verification. Integrate selected web-audit and vibe-audit checks as untrusted heuristic signals, with stricter execution and reporting.

## Scenarios and acceptance
- FR-001: Run local audit offline without executing project code or modifying its files. Explicit output only.
- FR-002: Scan documentation, examples and test fixtures for provider-shaped secrets too; never emit secret values or source snippets.
- FR-003: Normalize findings into rule, severity, confidence, location, fingerprint, remediation and source. A regex is not proof of exploitability.
- FR-004: Each check records completed/error/skipped/not_applicable; crashes, malformed output, empty scope and truncated input cannot yield a clean result.
- FR-005: JSON, Markdown and SARIF agree on findings and exit code. Codes: 0 scanned with no findings; 1 findings; 2 incomplete/error. None means production-ready.
- FR-006: Follow no source symlinks; bound file size, total bytes and external-process time. Exclude generated/dependency directories by explicit policy.
- FR-007: Supply workflow gates for authz, UX, browser, accessibility, performance, dependency vulnerabilities, operations and legal applicability. Missing evidence blocks release.
- FR-008: Supply selective Spec Kit templates, provenance and original MIT notices; no wholesale fork or unverified legal rules.
- FR-009: Add opt-in npm audit on sanitized lockfile snapshots; network failure, missing tool, malformed JSON must remain incomplete. Find nested npm projects.
- FR-010: Audit GitHub Actions for privileged pull-request triggers, broad write permissions, mutable action references and retained checkout credentials without executing workflow code.
- FR-011: Bind reports and imported evidence to the source digest plus Git commit and dirty state. A mismatch is incomplete, never a pass.
- FR-012: Preserve versioned security-standard identifiers on normalized findings when an exact mapping is verified; do not infer compliance from mappings.
- FR-013: Strictly import CycloneDX SBOM, OSV, Trivy and explicit authorization-matrix evidence. Empty, malformed, failed or mismatched evidence cannot pass.

## Architecture and domain
Inventory → isolated text snapshot → first-party secret and supply-chain rules + vendor/static evidence adapters → normalized report bound to source identity → output renderers. Check status is independent of finding severity. Static pass is independent of release readiness. Workflow documents own spec/task/evidence/fix cycles.

## Constraints and risks
Only stdlib for CLI. No browser or network by default. No automatic changes to audited project. Regex checks have false positives/negatives; no claim of taint analysis, full WCAG, legal certification, history scanning or penetration testing. Snapshot is containment for file reads, not an OS sandbox for malicious scanner code. Project must not mutate during scan. Runtime and infrastructure checks are agent-run with recorded evidence. External npm only when explicitly requested.

## Tickets
T1 provenance and source review; T2 bounded inventory and secret tests; T3 static adapters/status/report contract; T4 workflow and reference gates; T5 regression suite and independent forward test; T6 install and verify persistence.
