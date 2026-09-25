# Changelog

## 2.0.0

Added a whole-product readiness coordinator with ten-domain passports, deterministic coverage plans, source/artifact/environment binding, evidence expiry, manual versus automated provenance, issue retests and expiring exceptions. Bounded offline JSON input rejects duplicate keys; no project commands execute. Existing scanner CLI contracts remain available. Runtime collectors remain external and evidence authenticity is the trusted runner's responsibility.

## 1.2.1

Reject failed and structurally incomplete dependency reports. Trivy imports require exit 0 (configure the producer accordingly); OSV exit 1 requires findings; SBOM generation requires exit 0. Authorization evidence rejects duplicate cases, binds its target, and requires a policy-owned list of mandatory cases. Missing coverage cannot pass.

## 1.2.0 — 2026-09-25

Added offline GitHub Actions supply-chain checks, Git commit/dirty-state report binding, versioned ASVS references, and strict CycloneDX, OSV, Trivy and authorization-matrix evidence adapters. Evidence schema v2 now requires matching source identity. Added regression coverage for the new contracts; 55 tests pass.

## 1.1.0 — 2026-09-25

Added bounded Git-history secret scanning, explicit live HTTP checks, strict imports for browser/axe, Lighthouse, Semgrep and ZAP, and a required-check policy gate. Added source-scope and evidence-age validation. Browser collection remains external; optional engine live execution is not verified. 51 regression tests pass, including graceful handling of a failed Git index command.

## 1.0.0 — 2026-09-25

Initial standalone repository: Spec Kit-derived workflow, hardened static audit adapters, JSON/Markdown/SARIF output, regression tests and verification documentation.
