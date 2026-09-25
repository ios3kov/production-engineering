# Verification — version 1.2.1

Current run: macOS, Python unittest discovery — 57 tests PASS (exit 0); compileall and git diff --check PASS. Live Trivy/OSV/SBOM collectors were not run. No overall release certification is claimed.

1.2.1 regression scope: failed dependency-tool exits, incomplete package/component/target records, duplicate authorization cases, missing policy cases and complete policy coverage. Earlier verification entries below describe the 1.2.0 baseline, not newly executed specialist tools.

Originally verified 2026-09-25 on Linux/Python 3.12. Version 1.2.0 was verified on macOS/Python 3.14 against base revision `8c4297aad5a57c5385a3878fe59ba910e955149b` plus the documented working-tree changes.

- PASS: 55 unittest cases, including credentials in docs/examples/tests, bounded inputs, malformed tool output, Git identity/failure handling, GitHub Actions findings, versioned ASVS metadata, strict SBOM/OSV/Trivy/authz adapters, SARIF URI escaping, nonzero JSON exits and safe output paths.
- PASS: skill structure validator.
- PASS: compilation of all Python sources. No separate lint/type-check configuration or packaging build is defined; these are not claimed executed.
- PASS: real npm audit invocation using a disposable valid empty lockfile; tool completed. This proves invocation/configuration, not advisory detection against a production dependency tree. Positive advisory parsing has a controlled regression test.
- PASS: independent forward test on a disposable HTML + Python API project. The workflow kept release status unassessed/incomplete without a real server and reproduced SQL injection in an in-memory database.
- PASS: recheck after fixing discovered static accessibility defects: valid spaced alt attribute no longer flagged; unlabeled checkbox now flagged. Both fixture profiles complete without tool errors.
- Fixed before save: inherited a11y detection defects; missing adapter helper during pruning; npm duplicate config-path failure.

## Limitations
No real user application, browser session, production environment, Git history, restore drill or regional legal compliance was audited. Static detection remains heuristic. Other OS/Python combinations are not validated in this session. Running the skill on an actual project must produce its own revision-specific evidence ledger.

## Handoff
The skill contains the unified workflow, static runner, selected vendored checks, original Spec Kit templates, licenses and pinned upstream revisions. Next use: invoke production-engineering for a concrete project, inspect its current spec/architecture and run scoped checks. Do not treat this toolkit validation as validation of that project.
