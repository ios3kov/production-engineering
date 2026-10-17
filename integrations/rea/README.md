# REA: optional Reference Audit integration

## Admission correction — 2026-10-17

**REA 6.5.0 JavaScript analysis is QUARANTINED**, based on the upstream
[reproduction of missing CommonJS exports](https://github.com/morluto/rea/issues/3551).
Renamed Webpack factory parameters can lose exports while the result reports
exact/complete coverage. Our simple fixture smoke did not cover this defect.
Do not admit 6.5.0 JS/export facts as authoritative, even with exit zero or
complete coverage. The planner now returns BLOCKED for JavaScript analysis,
feature/semantic traces, application comparisons, generic retained views and
Evidence comparisons (which can inherit JS facts). This conservatively blocks
mixed/unknown-origin workflows rather than claiming a reliable bundle detector.
No bypass switch is provided. Package inventory is not JS export recovery;
that lane and explicit native/Ghidra plans retain their existing separate checks.

To reopen the lane, select a corrected immutable package, review its exact
bytes and run a real regression covering renamed module/export parameters and
shadowed bindings through the installed interface. A pending upstream patch or
an unchanged version label is not sufficient. Earlier ZIP/JS/summary smoke
results remain historical narrow fixture observations, not production admission.
The original capability shortlist below is retained as planned scope, not a
claim that all listed operations are currently admitted.

Use only for an explicitly selected shipped artifact, package, native function,
or observed external product contract. Ordinary source development does not
load or run REA. The existing AS/AE Reference Audit, ownership rules, local
executable admission, Evidence lifecycle and release gates remain authoritative.

## Scope and version

Use the official `morluto/rea` project and **rea-agents 6.5.0**, never `@latest`
in a persistent registration or CI. The reviewed main source was
`f85a932d71279415dd95cc30083137d1161f83b8`; the 6.5.0 GitHub release points at
`3b79af28e80785afce9f5998d8f03289402a1847`. These are distinct identities.
The qualification workflow records actual registry `gitHead`, tarball integrity,
dependency lock, package entry digest and container image ID. A version string
alone is not a complete executable-package pin or proof of source equivalence.

First integration is **CLI-first**, with no automatic client configuration,
new general-purpose skill, full MCP registration, engine installation or global
package update. Runtime qualification is separate from repository integration.
The local `adapter.py` is an offline planner/receipt helper, not a REA substitute,
a command runner, or a security sandbox.

## Selected capabilities

| Block | Selected REA interface | Qualification boundary |
| --- | --- | --- |
| Packages/dependencies | `inspect-artifact`; MCP `trace_dylib_resolution` after explicit artifact selection | ZIP smoke; real macOS DMG mounting and dylib resolution need macOS checks |
| Native analysis | `analyze`, `function`, `decompile`, `xrefs`, explicitly `--provider ghidra` | Requires compatible Java/Ghidra and actual target-format tests; no automatic Windows/Mac portability claim |
| JS/Electron static | `analyze-javascript-application` on a supplied tree or ASAR | Owned JS fixture; Electron runtime and AE panel compatibility are separate |
| Feature investigation | `trace-application-feature`, `trace-javascript-semantics` on full saved Evidence requests | Discover installed schema; static reachability is not execution |
| Version comparison | `compare`, `compare-application-versions`; MCP `compare_artifacts`/`compare_functions` when advertised | Keep both source digests, engine identities and unknowns; not regression certification |
| Focused result retrieval | `inspect-analysis-view` and original full Evidence | Summary smoke; preserve full parent, coverage, limitations and unsupported fields |

Browser/Electron/native runtime captures and saved traffic analysis are deferred.
No Frida, debugger console, generic process launch, device management, extraction,
setup/update, arbitrary shell or network-capture command is in the planner.
MCP-specific operations above remain manual, task-scoped candidates; the planner
does not pretend to implement or test them.

## Practical use

1. Review exact package bytes and dependencies through the existing local-tool
   admission process. Use a private, owned installation or isolated image.
   Preserve upstream MIT and third-party notices in that installation; this
   integration does not redistribute the upstream code. No `curl | sh` or
   automatic native helper/engine installation is required.
2. Probe the **actual installed CLI** with `rea --version` and relevant command
   `--help`; probe Ghidra only for a native task. Record the supported commands
   in a reviewed `catalog.json`, e.g. `{"commands":["inspect-artifact"]}`.
   That handoff file is a declaration, not automatic proof of a capability.
3. Generate a bounded task plan with an explicit local input:

   ```sh
   python3 integrations/rea/adapter.py plan inventory /absolute/input.zip --catalog /absolute/catalog.json
   python3 integrations/rea/adapter.py plan native-function /absolute/plugin --selector RenderMain --catalog /absolute/catalog.json
   ```

   `argv` is a list, not a shell command. The planner never executes it. Without
   a matching advertised command it returns BLOCKED and exit 2. Even a supported
   command still requires host/package/target authorization and appropriate
   isolation. Do not turn the planner's allowlist into a claim of enforcement
   against direct REA calls.
4. Run only the reviewed operation in the already authorized environment.
   Retain complete stdout, stderr, exit status, build/tool identity and target
   digest. For a directory, use REA's recorded artifact digest and verify its
   inventory; do not invent a directory hash by hashing its path.
5. Attach an integrity receipt without rewriting the original result:

   ```sh
   python3 integrations/rea/adapter.py receipt /absolute/raw.json --exit-code 0 --subject-sha256 ACTUAL_SHA256 --package-version 6.5.0
   ```

   This returns NEEDS_REVIEW, **never PASS/product-ready**. Review the actual REA
   schema, subject identity, partial coverage, contradictions, inferred facts,
   unknowns and cleanup failures; map only justified facts into the existing
   reference observations/check records. Nonzero execution remains incomplete.
   Hash matching cannot authenticate a producer or self-reported PASS.

Large result files stay local; use the upstream full-record-to-summary workflow
rather than sending a complete app or sensitive source to an AI provider.
Do not upload licensed/proprietary targets, secrets or personal captures to
GitHub Actions. This repository's hosted test uses generated fixtures only.

## Qualification and activation

- `scripts/tests/test_rea_adapter.py`: offline planner/receipt regression tests.
- `REA reference qualification`: installs exact npm 6.5.0 with lifecycle scripts
  disabled and optional dependencies omitted **in a disposable acquisition
  container**. It then runs the real upstream CLI against an owned ZIP and JS
  tree in a **different network-disabled/read-only container**, with read-only
  inputs, no host home/credentials, memory/CPU/PID limits and only an output mount.
- The image tag is resolved once to its content ID per run and that same ID is
  retained and used for acquisition/execution. Registry metadata and the resolved
  dependency lock are retained. This is an isolated candidate qualification,
  not independent full-package admission for production use.
- Raw records and the final result are attached to the exact CI run for 30 days.
  Expiry ends that remote retention; archive reviewed records in the project's
  existing evidence store before relying on them long-term.
- A passing synthetic smoke establishes only those operations on that package,
  image and fixture. It does not validate native Ghidra, Mac DMG mounting,
  application behavior, physical iPhone/AE runtime, or all six blocks.
- No installed Work/Codex copy or client configuration is changed by this repo.
  Actual tools must appear in that client's session before claiming activation.
  Later MCP activation requires reviewed tool filtering and host isolation;
  upstream `readOnlyHint`/`destructiveHint` are descriptions, not access controls.

## Sources

[REA 6.5.0 release](https://github.com/morluto/rea/releases/tag/rea-agents-6.5.0),
[reviewed CLI](https://github.com/morluto/rea/blob/f85a932d71279415dd95cc30083137d1161f83b8/docs/cli.md),
[installation boundaries](https://github.com/morluto/rea/blob/f85a932d71279415dd95cc30083137d1161f83b8/docs/installation.md),
[JS workflow contracts](https://github.com/morluto/rea/blob/f85a932d71279415dd95cc30083137d1161f83b8/docs/javascript-application-workflows.md).
Original adapter/docs/tests; no copied upstream implementation or new AS/AE policy.
