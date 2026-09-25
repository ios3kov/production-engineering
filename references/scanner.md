# Scanner contract v1

Run `python3 scripts/audit.py ROOT --profile web|code --format json|markdown|sarif` from this skill's directory, or use an absolute script path. Output goes to stdout unless `--out NEW_PATH` is given. Existing output paths are rejected to prevent overwriting project files. Store reports outside the scanned source tree to avoid scanning old reports.

Python 3.11+; no third-party packages for the scanner. Offline by default. The `code` profile runs credential rules, Python AST interpolated-query checks, modern Compose default-password detection, Git index inspection and selected vibe checks. `web` adds static accessibility, SEO, consent, configured headers and legal-page discovery from web-audit. Legal pages are signals to review, not legal requirements inferred from a generic website.

`--npm-audit` explicitly enables dependency metadata transfer to the public npm registry. Runs npm against temporary copies of nested package-lock.json files with an inert package.json, empty npm config, fresh cache and lifecycle scripts disabled. Does not install or fix dependencies. Missing lockfiles/tools, registry failures and malformed audit output produce INCOMPLETE. pnpm/yarn/Python/Go/Rust/Ruby/PHP dependency auditing is an agent-run gate using the actual project's tools, not implemented in this scanner. Never substitute a host environment audit for project dependencies.

## Execution and output

- 0: no findings in completed selected checks; NOT a release approval.
- 1: findings to inspect (including informational review items).
- 2: incomplete selected checks/input, tool error, invalid root or output failure.

All formats share this exit policy. SARIF executionSuccessful=false when selected checks are incomplete. JSON includes schema_version, tool_version, time_utc, profile, checks, inventory, findings, verdict, exit_code, not_assessed, and release_readiness=not_assessed. Findings include rule, relative path, line, severity, confidence, source, remediation, evidence metadata and fingerprint. Credentials and source snippets are not output. Fingerprints use rule/path/line; line changes change fingerprints. They are for identical-location deduplication, not semantic cross-revision suppression.

## Coverage and boundaries

Inventory copies supported UTF-8 text into a private temporary directory. Files are limited to 2 MiB each, 64 MiB total and 10,000 files. Symlinks and nonregular files are not followed. Candidate omissions, encoding failures and exhausted budgets make the result incomplete. Generated/dependency directories are excluded by named policy; unsupported file types are counted. Excluded build outputs need separate bundle inspection. Source directory must be trusted and stable during scanning: this is not an OS sandbox or a defense against concurrent hostile ancestor-directory replacement. Text scanning does not prove absence of binary/encoded secrets.

Vendor processes have timeouts and file-backed captured output, parsed with a 4 MiB JSON limit. Vendor code is pinned and reviewed; no audited project code is executed. Git hooks/fsmonitor are disabled for index inspection. Git history is not scanned. No live requests are performed by the default profiles. Browser, performance, operating environment and compliance must be verified through the evidence workflow.

Docs, examples and tests are included in credential scanning. Local untracked .env files may contain legitimate secrets; treat findings as candidates and use context when triaging. Provider-shaped strings are not verified against a service. Publishable environment names without sensitive tokens are not automatically treated as secrets. Runtime routing/authentication cannot be established by static patterns.

The web adapter intentionally discards upstream free-form messages, details and fixes because they may contain source text; rule names and source locations remain. Consult vendor rule implementations locally for interpretation. Core checks and the workflow supply remediation guidance. Cross-engine overlapping findings require contextual triage.

## Verification

Run `python3 -m unittest discover -s scripts/tests -v`. Keep generated caches outside the saved skill. Add regression fixtures before changing scanner behavior. Re-run source review and tests after updating vendor versions. Source revisions and license notices are in references/upstream.json and references/upstream/.
