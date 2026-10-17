# REA: optional Reference Audit integration

Use for an explicitly selected shipped artifact, native function or external product contract. Do not load REA for ordinary source-repository development. Existing AS/AE Reference Audit, target authorization, local-tool admission, Evidence and release gates remain authoritative.

## Current decision — 2026-10-17

**Stock rea-agents 6.5.0 JS analysis remains quarantined.** The release can lose CommonJS exports when a Webpack module receiver is renamed and invent exports from a shadowed receiver ([issue 3551](https://github.com/morluto/rea/issues/3551)). The earlier toy smoke did not establish correctness at that boundary.

A separate source-built runtime, **`rea-6.5.0-patch3552.1`**, is now qualified for the five static operations below. It is **not an official upstream release**. It applies one inspected production-file correction from [PR 3552](https://github.com/morluto/rea/pull/3552) to the fixed 6.5.0 release. Neither a pending PR nor a version label was accepted as proof: the actual baseline defect, corrected exports and derived workflows were executed and checked.

`adapter.py` retains its conservative stock-package quarantine. `qualified.py` is a separate executable entrypoint: it verifies all 7,501 files/links in the externally pinned runtime manifest before invoking one allowed operation. A mismatching, modified or stock installation is refused. It never installs software or edits client configuration. This is file-integrity checking, not an OS sandbox or producer authentication.

## Six selected groups and executed scope

| Group | Actual interface and checks | Remaining boundary |
| --- | --- | --- |
| Packages/dependencies | Real `inspect-artifact` ZIP; macOS `.app` and mounted DMG; `trace-dylib-resolution` resolved the owned library | Not arbitrary package/signature acceptance or proof of runtime loading |
| Native/Ghidra | Real Ghidra 12.1.4 + Java 21: named ELF function, callers, assembly, decompilation and xrefs | Linux x64 fixture; other binary formats/ABIs and Windows need task-specific checks |
| Static JS/Electron | Corrected CLI recovered ten expected Webpack/CommonJS export cases, including renamed/default/shadowed/empty/default exports | Static bundle fixture, not a running Electron app or AE panel |
| Feature investigation | Real positive and no-match feature traces; semantic trace preserving exact seed and source identity | Reachability and inferred relations are not observed execution |
| Version comparison | Real comparison detected the deliberately changed module and retained both artifact identities | Application graph comparison only; generic/function comparison modes are not claimed qualified |
| Focused retrieval | Real summary from complete parent Evidence, preserving parent and subject identity | Summary delivery does not prove smaller analysis cost or complete application coverage |

Corrected Linux checks: [run 39031000276](https://github.com/ios3kov/production-engineering/actions/runs/39031000276), commit `ffec5d4bb53e1b4b80633f55d23b1170f64bb9e7`. Eight real CLI cases include ten binding variants. The baseline's wrong result is a successful **defect reproduction**, not approval of baseline behavior. The corrected fixture's target-execution sentinel remained absent.

Native/macOS checks: [run 39030583850](https://github.com/ios3kov/production-engineering/actions/runs/39030583850), commit `022af1495ecfa3cab43ef8080faf09f1d3bf8950`. Three Ghidra and three macOS checks passed. These separate unaffected lanes used the published 6.5.0 package: Linux x64 Node 22.19.0; macOS arm64 Node 22.23.2. The JS patch's presence is not inferred for those installations.

## Immutable corrected runtime

The machine-readable identities and exact archive reference are in [profile.json](profile.json):

- Release source: `3b79af28e80785afce9f5998d8f03289402a1847`.
- Reviewed correction: `dakjdakd/rea@20643d4a47b0562aa794f0a15903630c62912c80`, only `src/domain/javascript/javascriptAstFingerprint.ts`; original blob `1dee83fa054b881409f9c321e74830e3b75239a2`, corrected blob `cf3f9aca413a00ebf5a5b8e4a5c94999776506ce`.
- Manifest SHA-256: `b3ba3f9f4806d7decaa8df1187b8c519d2ae1f37d29d7c652b60429aa6789c11`.
- Runtime tarball SHA-256: `0b08bf4babb85ad43bd8607d0d2cf890bcf82cd443e806f47069f0c7a96f0529`.
- Linux x64, Node `v22.19.0`; pinned image `node:22.19.0-bookworm@sha256:afff6d8c97964a438d2e6a9c96509367e45d8bf93f790ad561a1eaea926303d9`.

The [qualified artifact](https://github.com/ios3kov/production-engineering/actions/runs/39031000276/artifacts/12100024122) contains the runtime tarball, manifest, patch, notices, dependency identities and raw regression results. GitHub retention ends **2026-11-16**; preserve the verified archive in an approved local evidence/runtime store before relying on it long-term. Expiry is not permission to download `latest` or accept an unverified rebuild. The source recipe is retained in `.github/workflows/rea-corrected-qualification.yml`; a different resulting manifest requires requalification and a reviewed pin update.

Acquisition disables lifecycle scripts. Build and qualification run without network in distinct limited containers; development and optional dependencies are pruned before the actual qualified runtime is tested and packaged. Upstream MIT and separate third-party notices remain in the runtime. No upstream implementation is vendored into these repository instructions.

## Use the corrected static entrypoint

After reviewing and obtaining the exact archive, verify its ZIP/tarball/manifest hashes from `profile.json`, then extract into a new owned directory. Do not execute it during extraction. Use the pinned Linux container with runtime and inputs mounted read-only, network disabled, no host credentials/home, dropped capabilities and bounded memory/CPU/PIDs, following `.github/workflows/rea-runner-qualification.yml`.

Inside that prepared environment:

```sh
python3 /integration/qualified.py verify --runtime-root /runtime --manifest /manifest.json
python3 /integration/qualified.py run --runtime-root /runtime --manifest /manifest.json --operation javascript --input /inputs/app --output /out/new-analysis
```

Allowed operations are `javascript`, `view`, `feature-trace`, `semantic-trace` and `compare-applications`. The last four take an explicit JSON request with **complete newly collected corrected-runtime Evidence**, not a stale summary or a retained ID from another CLI process. Do not relabel old 6.5.0 observations as corrected. The runner does not infer the authenticity of embedded Evidence; its provenance remains an existing reviewed Evidence requirement.

Outputs are complete `stdout.json`, `stderr.txt` and `receipt.json` under a new directory. Files are not overwritten. A process timeout or nonzero exit is incomplete. An exit-zero receipt says **NEEDS_REVIEW**, never application PASS: inspect subject identity, coverage, contradictions, unknowns, inferred relationships and cleanup failures. Larger-than-profile requests must use a separately reviewed bounded workflow, not truncate facts to obtain success.

The runner does not provide network isolation itself. Changing Node, dependencies, runtime bytes or host conditions can invalidate qualification. File checks cannot stop concurrent mutation; keep the admitted runtime immutable/read-only throughout execution.

## Native and package lane

For a separately admitted published CLI, the existing offline planner remains available:

```sh
python3 integrations/rea/adapter.py plan inventory /absolute/input.zip --catalog /absolute/catalog.json
python3 integrations/rea/adapter.py plan native-function /absolute/plugin --selector RenderMain --catalog /absolute/catalog.json
```

The catalog lists commands observed in the actual installation, e.g. `{"commands":["inspect-artifact","function"]}`; it is not an automatic capability probe. The planner emits argv and checks, not execution authorization. Follow the admitted real CLI contracts, including explicit `--provider ghidra` for native queries. macOS dependency analysis also has a CLI: `rea trace-dylib-resolution /absolute/Sample.app --json`.

Ghidra distribution 12.1.4 was verified against SHA-256 `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db` before extraction into disposable storage. Compatible Java and actual target-format checks remain necessary on each host. No engine is silently installed on the user's machine.

## Boundaries and activation

The six groups now have executable integration or real CLI qualification at the stated fixture/host boundaries. This does **not** prove a user's application, AE plugin, physical iPhone, Windows installation or live Electron session works. Those are separate target-specific checks.

Runtime/browser capture, traffic analysis, Frida, debugger consoles, device management and arbitrary shell/MCP commands remain deferred. Neither runner nor a passing smoke authorizes those operations. Large or sensitive output stays in the approved local store; never upload proprietary targets, secrets or personal captures to these public hosted jobs. Only generated fixtures are used here.

Repository publication is not installation or activation in Work/Codex. These workflows build and execute on isolated CI hosts, not the user's computer. A real supported client connection must be verified separately; MCP annotations are descriptions, not access controls. General Skills, Product Intelligence and existing application release gates are unchanged.

## Maintenance and provenance

Retain exact run/revision/environment, raw output, archive hashes, patch and license. Offline tests in `scripts/tests/test_rea_adapter.py` and `test_rea_qualified.py` check admission logic and negative cases, not actual model behavior. The three named qualification workflows perform real tool checks; their status must be read for the exact candidate.

Sources: [REA release](https://github.com/morluto/rea/releases/tag/rea-agents-6.5.0), [reviewed correction](https://github.com/dakjdakd/rea/blob/20643d4a47b0562aa794f0a15903630c62912c80/src/domain/javascript/javascriptAstFingerprint.ts), [CLI contracts](https://github.com/morluto/rea/blob/3b79af28e80785afce9f5998d8f03289402a1847/docs/cli.md), [Apple package contracts](https://github.com/morluto/rea/blob/3b79af28e80785afce9f5998d8f03289402a1847/docs/apple-application-analysis.md), [Ghidra distribution](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build). Recheck changed dependencies and target-specific facts before adopting updates; do not substitute current main for a reviewed runtime.
