# Nine-source design adoption — 2026-10-17

User-approved scope: adapt the selected practices to existing skills and browser QA, keep reference providers optional, and run an isolated Obscura extraction pilot. Do not install nine competing plugins. Base: `77bfb0224ce482ccc6df6448d330cc81964d3c93`.

## Applied mapping

| Source | Accepted change | Destination |
| --- | --- | --- |
| Emil Kowalski | Real-input stress, separate working variants, interruption-aware motion, profile before optimizing | Genjutsu, Motion Design, shared interface-practice.md, owned browser fixtures |
| Impeccable | Screen purpose, draft-preserving recovery, cancellation and actionable copy | Genjutsu and shared practice; no binary/hooks/remote direction API |
| Taste Skill | Font/geometry/wrapping/overflow/clipping/obstruction observations | Original browser collector; no taste or motion-count score |
| Playwright | Actions and independent behavioral assertions before screenshots; matched environment and reviewed baselines | Browser QA supplement and real Chromium/Firefox/WebKit qualification |
| Refero | Authorized full-flow research, source/uncertainty tracking and no-dataset boundaries | Design DNA and Competitor Recon; no paid-content ingestion or MCP activation |
| Details | Section-specific site references | Design DNA and shared reference research |
| Design Spells | Trigger/state/feedback/cancellation descriptions | Motion Design; not a code exporter |
| Anthropic Frontend Design | Content-led structure and truthful demonstrations | Genjutsu/shared practice; not another complete skill |
| Obscura | Small exact-field extraction pilot with cold/reused timing distinctions | Separate optional experiment; NOT_ADMITTED to production/visual QA |

Primary sources and explicit exclusions: [nine-source register](../plugins/general-skills/references/interface-sources.md). Implementation and use boundaries: [browser integration](../integrations/browser-qa/README.md).

General Skills is 1.2.0; only genjutsu, motion-design and design-dna changed. Product Intelligence is 1.0.1; only competitor-recon guidance changed, not its four Python helpers or other two skills. Existing TrueSpace guidance, other skills, marketplace permissions, REA, AS/AE repositories and application release gates remain unchanged.

## Executed verification

- First real browser run: [39036052571](https://github.com/ios3kov/production-engineering/actions/runs/39036052571), source `10392e1d1d3131904257aeeb90053744db549caf`. Chromium, Firefox and WebKit fixture lane completed. Browser archive 12101993708 SHA-256 `c9a7e5d71a0473e449f1a041c5a78c0d090507363cf55c0a0a69c2e995e3fa41` was downloaded and verified. Reviewed the Chromium draft/retry and WebKit deliberate-defect screenshots; the fixture's intentional clipping, overlay and overflow are not a production design.
- Corrected pilot and browser rerun: [39036870734](https://github.com/ios3kov/production-engineering/actions/runs/39036870734), source `0cdc85b4baafe95c3b36d3b9054726bf995e993a`. Obscura archive 12102416663 SHA-256 `f1baa26d0eae5a029e9b3a347855e773d6b09cfc2f2a75220ae09fb8d4d2295e` was downloaded, verified and its raw report inspected.
- Corrected pilot: Obscura 0.2.4 no-render/no-stealth, Chromium 143.0.7499.4. Each of cold Obscura, cold Chromium and reused Chromium returned the exact expected fields in 9/9 attempts (three owned static/DOM/async pages, three trials each). Illustrative median wall time: 17.092 / 156.533 / 68.609 ms respectively. These tiny loopback fixtures and different startup modes do not establish general speed, memory efficiency, browser compatibility or public-site reliability. No memory measurement was made.
- The initial pilot incorrectly combined --selector and --eval, so it received page HTML rather than the documented bare-eval value. That harness result is superseded, not evidence of an Obscura engine defect. The rerun corrected the invocation rather than weakening the expected fields.
- Seven new offline contract tests passed locally; existing General Skills (2), visual supplement (8), and Product Intelligence (18) targeted tests also passed after the version updates. A local whole-suite attempt hit its execution time limit and is not recorded as a pass. Final full-suite results must be read from the exact PR head's CI run, not inferred from these focused checks.

The browser suite has six tests per engine, including real long-text/data inputs, intentional defect detection, incomplete scope, save failure/retry, repeated transitions/reduced motion and cancelled drag/keyboard focus. It is fixture/tool qualification, not application or model acceptance. Screenshots are inspection artifacts, not automatically approved golden images. Final state assertions do not establish continuous animation trajectories or server-side idempotency.

## Boundaries and handoff

All browser and candidate execution occurs in a separate network-disabled, resource-limited CI container, on owned loopback fixtures with no account data or third-party gallery content. Versioned acquisition is separate and the resolved image identity/dependencies are retained. Existing environment network/browser safeguards are not disabled to reproduce tests. The measurement collector itself supplies no OS sandbox.

Obscura remains PILOT_ONLY / NOT_ADMITTED for production and visual QA. Reference provider access, live agent evaluation, real application/AE/iPhone acceptance and installed Work/Codex-copy refresh are NOT_RUN, not implied by repository publication. No account permissions, subscriptions, provider connections, model training data or external hooks were changed.

Review actual PR diff and exact full CI before merging. Preserve needed evidence before the 30-day GitHub artifact expiry. Requalify changed runtime/helper bytes and keep original source attribution; do not automatically update unrelated dependencies or reopen approved designs.
