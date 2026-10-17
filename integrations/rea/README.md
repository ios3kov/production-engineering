# REA: optional Reference Audit integration

Use for an authorized shipped-artifact investigation, not ordinary source development.
Existing project permissions, Reference Audit, local-tool admission, Evidence and release gates still apply.

## Corrected source, not an invented release

The runnable integration uses `dakjdakd/rea` commit **20643d4a47b0562aa794f0a15903630c62912c80**, the reviewed repair in [upstream PR 3552](https://github.com/morluto/rea/pull/3552). This is a **pinned custom source build**, not a newer official npm release. The upstream package version remains 6.5.0; version alone must never select this build.

**Stock npm rea-agents 6.5.0 remains quarantined for JS-derived facts.** [Issue 3551](https://github.com/morluto/rea/issues/3551) demonstrates exports lost after Webpack factory parameters are renamed, despite complete/exact labels. The old offline `adapter.py` deliberately retains that quarantine. Do not bypass it or relabel old reports. Use the separately qualified `runtime.py` installer/launcher below.

## The six implemented paths

| Area | Executable path | Qualification performed by the installer |
| --- | --- | --- |
| Packages and dependencies | `inventory`; macOS `dependencies` | ZIP membership/digest; macOS DMG inventory plus a compiled dylib resolved through `@rpath` |
| Native investigation | `native-overview`, `native-function` | Real Ghidra 12.1.4 on a source-owned C binary; function body, pseudocode, assembly and callers |
| Static JavaScript | `javascript` | Real CLI and stdio MCP; renamed/defaulted/shadowed/positional export bindings; target has an execution-failure guard |
| Feature tracing | `feature-trace` | Actual cross-module trace with matched seeds and edges |
| Version comparison | `compare-applications` | Actual added module and distinct, correctly linked input identities |
| Focused views | `view` | Real summary generated from complete parent Evidence; parent digest retained |

These qualify **generated fixtures**, not arbitrary product behavior, full security, every bundler or compatibility with all AE/iPhone applications. Linux x64 and macOS arm64 are the hosted qualification lanes. Native Windows is not claimed. Additional semantic tracing variants, native comparison commands, browser/Electron runtime actions, traffic capture, Frida and debugger consoles are not enabled by this wrapper.

## Install and use

Prerequisites: Python 3.11+, **Node 24.18.0**, npm, a compatible full JDK (tested: Temurin 21.0.8), Git, C/C++ build tools, `nm` and `unzip`. The installer does not change system Node/Java, Homebrew or Xcode. On macOS, Ghidra's native tools are compiled through its supplied Gradle wrapper.

Run from this repository, choosing a **new absolute prefix** whose parent already exists:

```sh
python3 integrations/rea/runtime.py install "$HOME/rea-20643"
python3 integrations/rea/runtime.py install "$HOME/rea-20643" --apply
```

The first command only shows a plan. The second fetches the exact source commit, installs locked dependencies with lifecycle scripts disabled, compiles REA, downloads checksum-verified Ghidra, builds platform-native components when needed, then runs the actual CLI/MCP and six-path tests. It never overwrites an existing prefix. A failure retains diagnostics and does not create a qualified manifest. Original licenses and third-party notices stay in the installation.

After successful qualification:

```sh
python3 integrations/rea/runtime.py verify "$HOME/rea-20643"
python3 integrations/rea/runtime.py run "$HOME/rea-20643" inventory /absolute/input.zip --output /absolute/new-report
python3 integrations/rea/runtime.py run "$HOME/rea-20643" native-function /absolute/plugin --selector EXACT_SYMBOL --output /absolute/new-native-report
```

`javascript` takes an application directory/ASAR; `feature-trace`, `compare-applications` and `view` take an upstream-schema JSON request file containing complete Evidence. Use actual catalog schemas, not guessed request shapes. Paths must be canonical, absolute and not symlink aliases. macOS C symbols may carry an underscore; select the observed symbol/address.

The launcher verifies installed source/dependency/engine trees, Node bytes and qualification-report hashes before executing a permitted command. Complete stdout/stderr, exit code and hashes are kept in the new output directory. A successful analysis receipt remains **NEEDS_REVIEW**, never product PASS. Review actual subject identity, coverage, limitations and unknowns before mapping observations to the project's existing records.

## Client connection

Installation creates `codex-fragment.toml` in the chosen prefix. `runtime.py config PREFIX` prints the same reviewed static-tool allowlist without editing any client configuration. The fragment starts the verified source build through `runtime.py mcp PREFIX`; it does not point to `@latest` or stock npm 6.5.0.

Merge the fragment only in an authorized supported Codex configuration, preserving other entries and approval settings. `enabled_tools` is a **client-side filter**, not a server-side security boundary. Starting the raw upstream server without that filter exposes additional tools. Work/client activation is confirmed only when the tools actually appear in that user's session; a hosted MCP handshake or GitHub merge does not install them on the user's computer.

## Evidence and security boundary

- `REA repaired-source qualification` exercises the real installer and launcher on disposable Linux/macOS runners, using **only generated inputs**. These runs are not represented as network-disabled containers; acquisition and macOS native compilation need network access.
- `repair-report.json`, `capability-report.json`, complete command output and `runtime.json` are retained with the exact workflow run for 30 days. Archive reviewed records in the established evidence store before their remote expiry.
- The manifest detects changes relative to the local qualification. It is not independent attestation, a guarantee of dependency safety, or an operating-system sandbox. Use an authorized isolated host for untrusted binaries; keep private apps and user data out of public CI.
- The installer uses a private HOME and does not inherit credential or Node injection variables. Do not publish raw reports containing secrets, licensed code, private paths or personal data. Sending a result to a cloud agent is still data transfer.
- No runtime capture, automatic client registration, billing change, release, device installation or physical AE/iPhone acceptance is authorized by this integration.

## Sources

[Fixed source](https://github.com/dakjdakd/rea/tree/20643d4a47b0562aa794f0a15903630c62912c80), [upstream defect](https://github.com/morluto/rea/issues/3551), [Ghidra native-build instructions](https://github.com/NationalSecurityAgency/ghidra/blob/Ghidra_12.1.4_build/GhidraDocs/GettingStarted.md#building-native-components), [Codex MCP configuration](https://developers.openai.com/codex/mcp).

Historical source review: upstream main f85a932d71279415dd95cc30083137d1161f83b8; npm 6.5.0 release source 3b79af28e80785afce9f5998d8f03289402a1847. The earlier simple npm ZIP/JS/summary smoke did not cover issue 3551 and remains narrow historical evidence only.
