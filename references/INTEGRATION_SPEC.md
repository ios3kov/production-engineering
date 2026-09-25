# Deep audit integration 1.1

Objective: extend the existing Spec Kit workflow with executable history and HTTP checks, browser evidence import, validated specialist-tool results and a strict CI gate. Keep one normalized report and preserve fast offline scanning.

Requirements:
- D1: scan every reachable Git blob, including deleted files and merged/branch content; enforce whole-operation time and byte/object bounds; shallow/incomplete history is ERROR, not pass. Never print credential values.
- D2: only explicitly selected HTTP(S) pages; pin validated resolved IP, verify TLS, disallow cross-origin redirect, no credentials/query input; private destinations rejected except explicit loopback test flag. Preserve separate Set-Cookie headers. Limit response bytes and request duration. No arbitrary crawling.
- D3: integrate browser + axe, Lighthouse, Semgrep and ZAP evidence. Reject empty/malformed reports, tool errors and stale/mismatched source scope. Tools absent/not run cannot pass. Never leak raw console text, cookie values or tool snippets.
- D4: browser collection remains an external runner responsibility. Import sanitized explicit-page evidence; blocked requests mark coverage incomplete. No bundled browser launcher in 1.1.
- D5: CI policy lists mandatory checks. Any missing, error or skipped mandatory check blocks; FAIL findings meeting policy threshold block. Report distinguishes static audit from selected gate completion. Manual evidence is explicit owner attestation, not automatic verification.
- D6: regression tests: deleted Git secret, shallow Git, cross-origin redirect, private target, repeated cookies, body truncation, tool schema/error handling, gate skipped/missing/stale/failed inputs. Real local HTTP fixture and Git repositories; browser and specialist live runs only where available.

Architecture: existing audit.py → deep_audit.py coordinator → history.py + live_http.py + external_reports.py → normalized existing JSON/Markdown/SARIF; an external authorized browser runner produces browser evidence; release gate consumes the unified report and policy. No source mutation by scan. All network/deep actions explicit opt-in.

Tasks: T1 review source and licenses; T2 failing behavior tests; T3 implement history/HTTP/tools/gate; T4 verify local end-to-end plus independent review; T5 documentation, installed skill and prepared Git repository sync.

Risks: regex secret coverage finite; binary blobs are scanned for ASCII provider tokens, not decrypted/decompressed; dynamic browser assessment depends on a browser installation and actual app. Externally supplied reports/attestations cannot be cryptographically authenticated by a local tool; hashes bind bytes, not truth. CI protects report generation and policy ownership.
