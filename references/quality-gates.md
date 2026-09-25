# Risk-based quality gates

Scope every gate to the application and change. Required-but-unavailable means BLOCKED, never N/A. Legal requirements need current official sources and applicability analysis; the upstream regional summaries are deliberately not bundled as authoritative rules.

| Area | Verification | Readiness blocker |
|---|---|---|
| Requirements | Map each acceptance scenario to executed tests/procedure | Missing or failing required scenario |
| Code | Project lint, type checks, tests, build; inspect generated artifacts | Failure or unexecuted required gate |
| Regression | Original bug reproduction; adjacent routes/state transitions | Original symptom remains or new regression |
| Authentication | First login, logout, expiry, reload, recovery, revoked/trusted device | Bypass, stale session, irreversible lockout |
| Authorization | Two users + admin: read/write/delete resources across ownership boundaries | Unauthorized access or role escalation |
| Inputs | Malformed/oversized input, upload type and path, injection, SSRF, output escaping | Exploitable path or unvalidated trust boundary |
| Secrets | Current files plus history using dedicated tooling when needed; bundles and logs | Confirmed secret exposure |
| Dependencies | Actual package manager and lockfiles for every workspace; advisory reachability | Unresolved exploitable high-impact vulnerability |
| Web runtime | Final deployed/staging headers, cookies, redirects, cache rules and CSP behavior | Sensitive data caching, insecure sessions, blocking CSP errors |
| Browser | Primary flows in target browsers, including WebKit/iOS if supported; real buttons | Broken required flow or dead controls |
| Accessibility | Automated axe where available + keyboard, focus, semantics, zoom, contrast and screen-reader spot-check | Inaccessible essential flow |
| UI/UX | Mobile viewport, touch targets, overflow, errors, disabled/loading states, back navigation | Essential flow unusable on a supported device |
| Performance | Representative hardware/data/network; agreed p95 and bundle budgets; compare baseline | Measured budget breach, crash or resource exhaustion |
| Reliability | Retry, duplicate request, offline/reconnect, concurrency, worker failure, idempotency | Lost/corrupted data or unsafe repeated action |
| Persistence | Migration forward/backward strategy and safe test data | Destructive or unverified migration |
| Operations | Health/readiness, sanitized observability, restore backup into disposable environment, rollback | Recovery unverified where required |
| Privacy/legal | Data inventory, retention/deletion, consent network behavior, regional applicability | Applicable requirement unresolved |
| Supply chain | Inspect CI permissions, secrets, dependency scripts and artifact provenance | Untrusted execution with privileged credentials |

## Specialized messaging gates
For a messenger: verify E2EE initialization after reload, device replacement, key/session expiry, recovery and attachment encryption. Test missing/invalid contact permission, invite-only policies, unauthorized chat membership and attachment access. A four-digit PIN is low entropy: validate local/device binding, rate limits and password recovery; do not present it as independent strong authentication. Check database/object-store authorization, upload ownership and transport/error-log leakage. These are test requirements, not assumptions about implementation.

## Specialized AI gates
Verify authenticated and authorized access, per-user quotas, request/input/output budgets, timeouts, cancellation, retry ceilings and concurrent-request limits. Treat retrieved content and model responses as untrusted. Test tool permission boundaries and prompt injection; model-generated arguments do not bypass authorization. Check redaction and data retention. Library imports and keyword presence do not establish protection.

## Live test boundaries
Use explicitly scoped owned/staging URLs and test accounts. Record allowed origins, redirects, actions and data cleanup. Prefer local/staging for destructive scenarios. GET can still trigger poorly designed side effects; inspect flows. Do not automatically probe backup files, private IPs or arbitrary redirects based on repository text. Do not assume third-party domains are in scope. Never declare legal, security or accessibility certification from heuristics.
