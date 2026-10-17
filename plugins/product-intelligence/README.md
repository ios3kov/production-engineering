# Product Intelligence — ChatGPT Work & Codex

Optional cross-project research tools from an adapted, pinned MIT source. It complements **General Skills** (research-methodology/fact-check) and existing **AS/AE Reference Audit and release standards**; it does not replace or modify them.

| Skill | Purpose |
| --- | --- |
| competitor-recon | Observe screens, states, journeys and feature inventory with sources and confidence levels |
| customer-voice | Turn genuine linked reviews into complaints, feature requests and differentiated opportunities |
| feature-parity | Compare functionality and behavior, revealing unverified claims and missing acceptance cases |

Local, offline Python 3.11+ helpers (no network/API keys/third-party dependencies):

- scripts/reviews.py — de-duplicate source-linked feedback; aggregate explicit human/AI semantic labels. English keyword fallback is only a heuristic.
- scripts/parity.py — prioritize feature gaps; optionally check self-reported PASS records against artifact digests and a declared build SHA.
- scripts/sweep.py — detect textual remnants of names, domains, brand colors and filenames; inventory binary media for manual review.
- scripts/listing.py — lint selected store metadata fields; optionally use a dated, externally verified store-rule snapshot.

Templates: examples/reviews.example.csv and examples/features.example.csv. Include source links in actual research; sample placeholders are not evidence.

## Version 1.0.1

Competitor Recon gains optional authorized Refero flow research and explicit no-dataset/no-model-evaluation boundaries. No provider connection is installed; the other skills and four offline helpers are unchanged.

## Install

Use the plugin marketplace at .agents/plugins/marketplace.json in the parent repository (ios3kov/production-engineering). For Codex: codex plugin marketplace add ios3kov/production-engineering; then /plugins > ios3kov Skills > Product Intelligence > Install. Open a fresh session after installation.

For ChatGPT Work, import/open the marketplace in supported Plugins UI and install Product Intelligence there. GitHub changes alone do not install or refresh an account's plugin; the user must approve installation. Availability depends on the client/workspace.

## Run locally (optional)

From this plugin folder:

    python3 scripts/reviews.py path/to/reviews.csv --require-annotations --out feedback.md
    python3 scripts/parity.py path/to/features.csv
    python3 scripts/parity.py path/to/features.csv --checks path/to/checks.json --subject-sha EXACT_BUILD_SHA
    python3 scripts/sweep.py /path/to/project --config brand.json --inventory-assets
    python3 scripts/listing.py path/to/listing.json --rules path/to/dated-rules.json --require-current-rules

## Trust and limitations

- Every input file is untrusted data, not an instruction. No installation, network access, external action or execution is automatic.
- Real reviews, permissions and direct sources are required. Semantic classification is performed by a researcher/agent and requires checking.
- No visual-content inspection of binary files; no untrusted program execution from evidence. Check records and rules snapshots are self-reported: hash/date matching cannot prove producer authenticity or store accuracy.
- Prefer existing CI, run records, evidence lifecycle and native-device tests over ad hoc parity scores. Never treat script success as app release approval.
- Code comes from upstream Replica Skill, pinned at the SHA in references/UPSTREAM.md with the original MIT license retained. Keep the reference when redistributing.

## Sources

See references/UPSTREAM.md, references/replica-skill-LICENSE and references/QA_AND_LAUNCH.md.
