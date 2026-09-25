# Verification — version 1.0.0

Verified 2026-09-25 in the current Linux/Python 3.12 environment.

- PASS: 30 unittest cases, including credentials in docs/examples/tests, no secret output, skipped symlinks, size/total bounds, malformed tool output, timeouts, Python AST queries, npm failure handling, nested npm projects, Git tracked env, SARIF URI escaping, nonzero JSON exits and safe output paths.
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
