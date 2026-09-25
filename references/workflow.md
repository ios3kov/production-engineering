# Workflow contracts

## 1. Intake and routing
Record objective, actor and job-to-be-done, current vs desired behavior, constraints, exclusions, dependencies, unknowns, risk and measurable success. Inspect existing tests, module boundaries and operations before proposing a change. When the approach is questionable, state the concrete concern and test the hypothesis. Do not manufacture questions that the code or context answers.

For large ambiguous work, keep a map: unknown → evidence required → dependency → next decision. Distinguish prototype from production: the former answers one question and carries explicit disposal/reuse criteria.

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

## 5. Evidence ledger
Place verification.md next to the spec, or use the project's established system.

| Gate / REQ-ID | Scope / revision | Command or procedure | Environment / time | Result | Evidence / issue |
|---|---|---|---|---|---|

Allowed results: PASS, FAIL, BLOCKED, NOT_RUN, NOT_APPLICABLE. NOT_APPLICABLE requires a rationale. Record exact exit codes for commands; do not publish logs containing secrets. A test name without execution evidence is NOT_RUN. A failing tool must not be hidden by a shell pipeline. Document absent tools and network restrictions. A stale run against a different revision does not verify changed code.

Issue record: ID, deduplicated sources, affected REQ, severity, confidence, location, reproduction, impact, root cause, fix, regression evidence and disposition. Dispositions: candidate, confirmed, fixed, false-positive, accepted-risk. False-positive needs evidence; accepted-risk needs owner, rationale and expiry. Never fabricate an owner approval.

## 6. Review and convergence
Compare implementation to requirements and inspect actual diffs. Review authn/authz separately; examine error paths, transactions, idempotency, concurrency, secret handling, injection, dependencies and UX. Fix findings, then rerun tests affected by the fix. Escalate the scope only when there is evidence of systemic risk. Stop optional checking when acceptance and applicable gates pass.

Release verdict: READY only if every applicable required gate passes (or is explicitly justified N/A), no unresolved blockers remain, and evidence matches the candidate revision. Otherwise NOT_READY or INCOMPLETE with specific next action. A static scanner never emits READY.

## 7. Handoff
Record: objective; current revision/branch; changes; decisions and constraints; key files; completed checks and artifact paths; unresolved issues; exact next action. Do not include secrets. Keep the report useful for an agent without prior chat. Update existing documents rather than generating contradictory versions.
