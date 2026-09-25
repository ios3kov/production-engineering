# Deep audit 1.2

Run Python 3.11+ from the installed skill. Default static scanning stays offline.

```bash
python3 <skill>/scripts/deep_audit.py /project --history --profile code --format json
python3 <skill>/scripts/deep_audit.py /project --url https://example.com/ --policy /policy.json --format markdown
python3 <skill>/scripts/deep_audit.py /project --semgrep-rules /trusted/rules.yml --format sarif
python3 <skill>/scripts/deep_audit.py /project --evidence /evidence.json --url https://example.com/ --policy /policy.json --format json
```

Keep outputs outside the project being scanned. Existing output files are never overwritten. HTTP fetches only the supplied page and same-origin redirects, with TLS certificate verification and pinned validated IPs. Private targets are rejected; `--allow-loopback` permits local test servers only. Query strings, fragments and URL credentials are rejected. HTTP input is limited to 2 MiB and the coordinator bounds the subprocess to 45 seconds. No crawling, form actions or JavaScript execution occurs. Header/cookie checks are heuristic candidates, not legal findings.

History scans local reachable objects including deleted file content. Shallow history, budget exhaustion and process failures produce incomplete status. Default bounds: 60 seconds, 64 MiB blob data, 10,000 objects and 2 MiB per blob. Remote-only refs, unreachable objects, LFS payloads and encoded/compressed secrets are outside coverage. Values are omitted from findings; blob IDs identify evidence.

## Required policy

Create a project-owned JSON policy, for example:

```json
{"required":["static","supply_chain.github_actions","history","http","browser","axe","lighthouse","semgrep","sbom","osv","trivy","authz","zap"],"fail_on":"high"}
```

Select required checks based on actual project risk. Missing/error/skipped checks produce exit 2; findings at or above the threshold produce exit 1; complete selected checks below threshold produce exit 0. Errors in any selected check block even when absent from policy. Without a policy, exit 1 means any findings need review. `release_readiness` remains `not_assessed`. Manual review, operational readiness and deployment permission belong to the workflow evidence ledger; this CLI does not automatically attest them.

## Specialist evidence contract

Browser/axe, Lighthouse and ZAP are **import adapters**, not bundled execution engines. Run the tools in an authorized isolated runner and preserve raw output privately. Never automatically execute a scanner configuration or project code from an untrusted repository. For Semgrep, install it separately and use trusted local rules; the optional CLI runs against the admitted source snapshot. No optional tool is auto-installed.

Bundle freshly generated results as JSON (maximum 4 MiB):

```json
{
  "schema_version":2,
  "scope_digest":"<inventory.scope_digest from audit.py JSON for identical source>",
  "source_identity":{"commit":"<git commit>","dirty":false},
  "created_at":"<actual generation timestamp with timezone>",
  "target_url":"https://example.com/",
  "reports":[{"tool":"semgrep","returncode":0,"data":{"results":[],"errors":[],"paths":{"scanned":["app.py"]}}}]
}
```

`data` contains the actual tool output. Example structure is not evidence. Generate the bundle in the same trusted CI job as the tools; never relabel old results with a fresh date or digest. Scope digest covers admitted source files, while `source_identity` binds the commit and dirty state. Pin and verify deployment/build identity separately. Reports expire after 24 hours; more than 5 minutes into the future is rejected. Scope, Git identity, target and all runtime report origins must match; duplicate tools are rejected. This binding does not authenticate a report or prove its coverage.

Accepted tools:
- `semgrep`: JSON results, empty errors, nonempty paths.scanned, no skipped paths; exit 0 or 1 with findings.
- `lighthouse`: actual JSON with version, final URL, all four category scores and no runtimeError; exit 0. Default review budgets: performance .8, accessibility/SEO/best-practices .9. Set project performance gates separately.
- `zap`: passive JSON with nonempty site list, site @name, alerts arrays; baseline runner exit 0/1/2. Active scanning is not authorized by importing a report.
- `browser`: normalized collector JSON `{"pages":[{"url":"https://example.com/","status":200,"consoleErrorCount":0,"blockedRequests":0,"cookies":[],"trackerHosts":[],"axe":[]}]}`. Populate from real explicit-page navigation in a fresh context, without submitting forms. Cookies contain only boolean `secure`, `httpOnly`, `sessionLike`; axe violations contain `id` and `impact`. Omit console text, DOM snippets and cookie values. A failed axe run is not an empty violations list. Blocked requests make both browser and axe incomplete. This format requires an external collector; none is bundled.
- `trivy`: native JSON with a numeric `SchemaVersion`, nonempty `Results`, and validated vulnerability IDs and severities.
- `osv`: OSV-Scanner JSON with nonempty scanned package coverage. Vulnerability IDs and normalized severities are retained; package contents are not.
- `sbom`: CycloneDX JSON with nonempty components. Missing hashes, licenses and stable identifiers are review findings, not proof that an SBOM is unusable.
- `authz`: normalized cases `{"cases":[{"id":"user-read-other","actor":"user-a","action":"read","resource":"user-b/item","expected":"deny","actual":"deny"}]}` from an authorized test environment. Errors make coverage incomplete; expectation mismatches are high-severity findings.

The offline static profile also checks `.github/workflows` for `pull_request_target`, broad write permissions, mutable third-party action refs and retained checkout credentials. Findings are candidates for review because some release jobs legitimately require narrowly scoped write access.

Validation in this release: local Git and HTTP fixtures plus adapter/policy tests. Live execution of Playwright/axe, Lighthouse, Semgrep and ZAP has not been verified in this environment. Imported clean results never imply all pages or application states were covered.
