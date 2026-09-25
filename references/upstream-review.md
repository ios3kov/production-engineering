# Source review and integration

Pinned source revisions and URLs: upstream.json. Original MIT licenses preserved under upstream/<project>/LICENSE. Selected Spec Kit templates are copied; the workflow extends their requirements → plan → tasks model without pretending to install or fork the whole CLI. No upstream AGENTS instructions are imported into user projects.

## Confirmed source observations

| Source location | Observation | Integration decision |
|---|---|---|
| web-audit/scripts/run_all.py main JSON branch | Returns 0 before aggregating fail statuses | Replace runner; one exit policy for all formats |
| web-audit/scripts/run_all.py subprocess handling | Empty stdout becomes empty findings; malformed output becomes info | Require valid structure; record errors explicitly |
| web-audit/scripts/scan_secrets.py literal message | Includes an unmasked source line up to 80 characters | Do not execute this scanner; implement credential detection without emitting values |
| web-audit/scripts/_common.py iter_files | File symlinks can be read through | Run selected static modules on a bounded symlink-free snapshot |
| web-audit/scripts/check_deps.py | Empty/failed outputs can be interpreted as empty vulnerability results; pip audit may target host environment | Exclude adapter; implement explicit npm evidence and separate project-specific dependency gates |
| vibe-audit/scripts/audit.py SECRET_OK_FILES | Docs/examples/tests bypass secret detection | Core detector scans them without blanket exemptions |
| vibe-audit/scripts/audit.py check_client_exposure | Path hints classify app/pages as client; public KEY/TOKEN names can be legitimate | Exclude this check; sensitive-name detector plus actual boundary review |
| vibe-audit/scripts/audit.py check_rate_limit_and_ai | Global library presence and nearby keywords stand in for route protection | Retain only as heuristic hints; mandatory runtime abuse/authorization gates |
| vibe-audit/scripts/audit.py check_platform_configs | docker-compose naming misses compose.yaml | Add core support for modern Compose names |
| vibe-audit/scripts/audit.py main | Check exceptions become informational findings | Adapter records errors separately and runner fails incomplete |

## Additional defects fixed during forward testing
- Static `<img alt = "...">` produced a false missing-alt result: static HTML attributes are now parsed structurally.
- Checkboxes/radios were excluded from label checks; counting unrelated labels could hide missing labels. Static controls now use associated or wrapping labels and accessible-name attributes. Template rendering still requires browser evidence.
- First-party adapter trimming lost a line-number helper; a debug configuration fixture reproduced this and a regression test now requires completed status.
- npm rejects the same empty config path used for both user and global settings. The runner now creates distinct empty files, with a regression test.

## What is reused
- Spec Kit: original feature/plan/task templates, adaptable requirement-driven process.
- web-audit: five static modules and their shared helper; not the original runner, credential or dependency modules, or unverified compliance summaries.
- vibe-audit: selected config, platform, authz and AI/rate-limit heuristic functions through an isolated adapter; original CLI, secret, client-exposure, dependency and live probes are never invoked by the entry point.

## What is added
Bounded inventory and isolated snapshot, safe reporting, strict machine statuses, common JSON/Markdown/SARIF contract, Python AST query rule, secret scanning in examples/docs/tests, modern Compose rule, npm lockfile workspace inspection, regression suite, risk-based release gates, requirement-to-evidence traceability, authorized fix/retest cycle and compact session handoff.

## Deliberate limits
This is a working engineering skill and static audit toolkit, not a security certification or an autonomous penetration-testing service. No claim of exhaustive static analysis or universal framework support. A production-readiness assessment still needs the actual project, runnable environment, test accounts and operations evidence. No project was audited or deployed by merely installing this skill.

## Production Auditor integration (1.1)

Reviewed the shared Production Auditor 0.1.0 source archive. Retained the HTML parser with its MIT notice and rewrote the integration boundary. Replaced the history stream timeout with bounded subprocess reads, preserved separate Set-Cookie fields, pinned validated HTTP destinations and rejected cross-origin redirects. Required checks cannot pass with skipped/error states. Specialist parsers reject missing/error payloads and discard raw credential/snippet values. Import scope/time checks do not authenticate external reports. Browser collection remains external; live specialist-engine execution is unverified here. See deep-audit.md for the executable scope and limitations.
