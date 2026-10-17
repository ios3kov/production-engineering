# Optional browser QA and extraction pilot

This extends the existing Browser/UI/Reliability gates; it does not create a second readiness system. General Skills contains only prose and links. The collector is opt-in and independent of the static scanner. No browser, account, MCP server or dependency is installed by importing `collector.py`.

## Use with an existing authorized browser

`measure_ui(page, selectors, max_elements=1000, timeout_ms=5000)` accepts an already opened synchronous Playwright Page. It waits for font loading to stop and reads the current document. Pass existing selectors or fixture-specific `data-ui-qa` markers; do not rewrite a real application's DOM just to obtain a passing measurement.

```python
from collector import measure_ui  # from this directory in the approved runner
page.get_by_role('button', name='Save changes').click()
expect(page.get_by_role('status')).to_have_text('Changes saved')
report = measure_ui(page, ['main', 'header', '[role=status]'])
```

TypeScript Playwright can use the same original `measure.js` function source:

```ts
const measure = readFileSync(approvedHelperPath, 'utf8');
await page.waitForFunction(() => !document.fonts || document.fonts.status !== 'loading');
const report = await page.evaluate(measure, { selectors: ['main'], maxElements: 1000 });
```

Only use trusted helper paths/test selectors. The output records selected scope, geometry, line-fragment rows, declared fonts, font/image errors, horizontal overflow, clipping and sampled hit-test obstructions. It does not collect text snippets or resource URLs. It does not traverse frames/shadow roots or certify painted visibility, glyph fallback, aesthetics, WCAG or product readiness. Treat all candidates as reviewable observations; intentional cropping may be appropriate. Missing/empty/truncated scope is INCOMPLETE, not success; font timeouts and failed browser evaluation propagate.

Use the existing project Evidence format to bind the raw report, SHA-256, revision, browser/OS/viewport/fonts, scenario and review. This report is not automatically valid input to other evidence importers and never becomes release PASS by itself. Screenshots/traces may contain sensitive material on real targets; retain them only in the approved private store.

## Real fixture qualification

`test_browser.py` contains six independent tests per browser: real API-fed long text/large counts/empty state and variant switcher; deliberately broken geometry/fonts/images; missing/truncated scopes; error/draft/retry; repeated transition inputs/reduced motion; and cancelled drag/keyboard focus. It drives actual browser inputs and the fixture's normal handlers, not DOM substitutions for state. It does not prove animation trajectory continuity, server idempotency, accessibility compliance or any user's app.

The separate `Design QA qualification` workflow runs Chromium, Firefox and WebKit in a disposable official Playwright environment. Acquisition and network-disabled execution are distinct; code/inputs/dependencies are read-only, outputs go to a fresh directory, host credentials/home are absent, and CPU/memory/PIDs are limited. Only our source-owned loopback fixtures are used. Dependency versions and the resolved image identity are retained for each run. Network/browser policies in another environment must not be disabled to reproduce a test.

```sh
# Only inside a prepared authorized environment with matching installed browsers:
UI_QA_BROWSER=chromium UI_QA_OUTPUT=/absolute/new-output python3 integrations/browser-qa/test_browser.py
```

Use required target browsers; an unavailable one is BLOCKED, not skipped as PASS. Fixture screenshots are inspection artifacts, not approved golden files. For application snapshots: perform actions, assert the expected state, then use the project's screenshot matcher against an explicitly reviewed baseline. Keep browser/OS/fonts/viewport/scale identical. Disable animations only for final-appearance snapshots, not motion tests. Never auto-accept generated snapshots or raise tolerances to hide a bug.

## Obscura: experiment only

`obscura_pilot.py` tests extraction on three owned pages (static, DOM-generated and asynchronous data), three trials per mode. It compares exact title and ordered field values, not title presence or HTML length. Cold Obscura and cold Chromium include startup/teardown; reused Chromium is separately labeled and excludes browser launch. All failed attempts remain visible. Memory and persistent Obscura/CDP are NOT_MEASURED; this is not a general performance benchmark.

Candidate: v0.2.4 Linux x64, **no-render and no-stealth**. Archive `obscura-x86_64-linux-no-render.tar.gz`, SHA-256 `48ec360d75333e204e5eb5be4ce30fe4a1e57f2ca30fe985247eadf50a0c89d7`. The binary is downloaded/verified without execution, then run only inside the network-disabled container against its own loopback server. The per-process private-network flag permits that fixture server; it does not authorize browsing arbitrary private targets. No real logins, paid services, public scraping, proxies, anti-bot bypass, model provider or external MCP registration is involved.

Pilot `execution_status=COMPLETED` means the observation loop finished. It is **not** a candidate PASS; `candidate_admission` remains **NOT_ADMITTED**. Infrastructure failures are errors. Inspect the correctness totals and raw failures before considering a separately authorized real-source trial. Do not replace Chromium/WebKit/Firefox visual or behavior QA with Obscura. The CLI's bare --eval contract is used: adding --selector changes its output to page content in this version.

## Verification record and maintenance

See [the adoption record](../../docs/DESIGN_ADOPTION_2026-10-17.md). CI retains revision, source snapshot, environment, screenshots/traces, raw metrics and pilot data for 30 days. Preserve needed records in the existing evidence store before expiry. Requalify changed helper/runtime bytes; do not refresh source-policy dates unrelated to this change. Nothing in this integration updates an installed Work/Codex plugin, changes AS/AE rules, or validates physical iPhone/AE behavior.
