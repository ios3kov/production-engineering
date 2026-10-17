# Workflow contracts

## 1. Intake and routing
Record objective, actor and job-to-be-done, current vs desired behavior, constraints, exclusions, dependencies, unknowns, risk and measurable success. Inspect existing tests, module boundaries and operations before proposing a change. When the approach is questionable, state the concrete concern and test the hypothesis. Do not manufacture questions that the code or context answers.

For large ambiguous work, keep a map: unknown → evidence required → dependency → next decision. Distinguish prototype from production: the former answers one question and carries explicit disposal/reuse criteria.

For an explicitly selected shipped artifact or external product contract, the [optional REA integration](../integrations/rea/README.md) supplies pinned static-analysis workflows and raw-result receipts. Use existing Reference Audit and local-tool admission; do not run REA for ordinary source-repository work, install engines implicitly, or treat static analysis as product/runtime acceptance.

## 2. Specification and design
Use specs/<feature>/spec.md, plan.md, tasks.md if established; preserve identifiers.

| Field | Required content |
|---|---|
| REQ-ID | Unique requirement, actor, behavior and rationale |
| Acceptance | Given/When/Then with observable result |
| UX states | Initial, loading, ready, empty, error, retry, offline and denied as applicable |
| Data | Entities, identifiers, owners, retention, migration and invariants |
| Architecture | Existing modules, responsibility, interfaces and trust boundaries |
| Constraints | Supported platforms, performance budgets, security and compatibility |
| Edge cases | Invalid input, concurrency, expiry, retries, duplication and partial failures |
| Evidence | Test/procedure that will establish acceptance |

Use a data/state diagram only when it clarifies meaningful complexity. Define one term per concept. Reject abstraction or reorganization without a concrete current benefit. Keep architectural decisions with rationale and alternatives considered.

## 3. Tickets
Each task: ID, linked requirements, dependencies, files/modules, intended behavior, non-goals, test and definition of done. Do not create tasks that say only “improve quality”. Sequence data/interface changes before consumers; keep changes small enough to review. For agent handoff include necessary facts and explicit boundaries, not hidden assumptions.

## 4. Implementation
Reproduce bugs before editing. Use TDD for risky behavior: failing test for the intended behavior → minimal correct implementation → passing test → refactor. For low-risk changes, targeted verification may be enough. Preserve project conventions and user changes. Handle errors completely; no mock buttons, fake backend success, unfinished UX or unexplained placeholders. Resolve merge conflicts by preserving both sides' intent and verifying the result.

Remove imports, variables or functions made unused by the current change only after checking dependencies, public entry points, registrations, callbacks and loading by name. No direct callers is not proof of dead code. Leave pre-existing or uncertain dead code outside the patch; report relevant findings separately rather than deleting without authorization. This does not require a separate cleanup phase or document.

## 5. Evidence ledger
Place verification.md next to the spec, or use the project's established system.

| Gate / REQ-ID | Scope / revision | Command or procedure | Environment / time | Result | Evidence / issue |
|---|---|---|---|---|---|

Allowed results: PASS, FAIL, BLOCKED, NOT_RUN, NOT_APPLICABLE. NOT_APPLICABLE requires a rationale. Record exact exit codes for commands; do not publish logs containing secrets. A test name without execution evidence is NOT_RUN. A failing tool must not be hidden by a shell pipeline. Document absent tools and network restrictions. A stale run against a different revision does not verify changed code.

Issue record: ID, deduplicated sources, affected REQ, severity, confidence, location, reproduction, impact, root cause, fix, regression evidence and disposition. Dispositions: candidate, confirmed, fixed, false-positive, accepted-risk. False-positive needs evidence; accepted-risk needs owner, rationale and expiry. Never fabricate an owner approval.

## 6. Review and convergence
Compare implementation to requirements and inspect actual diffs. Review authn/authz separately; examine error paths, transactions, idempotency, concurrency, secret handling, injection, dependencies and UX. Fix findings, then rerun tests affected by the fix. Escalate the scope only when there is evidence of systemic risk. Stop optional checking when acceptance and applicable gates pass.

During this diff review, justify each changed block by a requirement, root-cause fix, necessary test, documentation update or dependency cleanup caused by the change. Exclude unrelated formatting, renaming and adjacent refactors introduced by this patch; never revert pre-existing user changes. Minimal means the smallest sufficient fix, not the fewest lines or files: include necessary cross-module changes and retain security and input validation. Use the existing review, not a per-line report or a new gate.

Release verdict: READY only if every applicable required gate passes (or is explicitly justified N/A), no unresolved blockers remain, and evidence matches the candidate revision. Otherwise NOT_READY or INCOMPLETE with specific next action. A static scanner never emits READY.

### Counterexample: a green test that misses the defect

Example-only contract: scores decrease; tied ASCII names increase alphabetically. Both `[("Ada", 100), ("Zoe", 100), ("Miro", 80)]` and the wrong tie order `[("Zoe", 100), ("Ada", 100), ("Miro", 80)]` satisfy a score-only check against `[100, 100, 80]`. Checking those scores cannot establish the required tie order, however often the test runs.

Verify the full expected identities/order/scores, using an expectation independent of the implementation. The [executable counterexample](../scripts/tests/test_workflow_counterexample.py) demonstrates the weak check accepting both results and the contract check rejecting wrong ties and damaged rows. The tie rule must come from the accepted requirement: alphabetical order is not implied by “fix sorting”; preserving input order can be a different valid contract. This synthetic example is not evidence of a reproduced application bug or measured agent improvement, and adds no mandatory mutation-testing framework.

These two clarifications and the counterexample are original formulations informed by the review of [Karpathy-inspired guidelines and examples](https://github.com/multica-ai/andrej-karpathy-skills/tree/2c606141936f1eeef17fa3043a72095b4765b9c2); no upstream instructions or code are bundled.

## 7. Handoff
Record: objective; current revision/branch; changes; decisions and constraints; key files; completed checks and artifact paths; unresolved issues; exact next action. Do not include secrets. Keep the report useful for an agent without prior chat. Update existing documents rather than generating contradictory versions.
