# Lightweight QA and launch supplements

Use only where the project's own requirements/QA/release profile does not already cover the same case. These are optional research ideas, not a parallel mandatory workflow.

## QA cases worth keeping
- For each core flow: ordinary success, invalid input, long/multilingual input, double submit, concurrent sessions, lost network, permission denial, stale session, time zone/DST and cancellation/retry.
- Check isolation with a second account and evidence of exactly one final write for a double-submit action.
- Always record source/build/commit/platform, prerequisites, expected result, actual result and evidence file. An observed screenshot is not proof of backend state.
- Severity: data loss/security/payments/core-flow block = critical; broken feature without workaround = high. Do not invent reproduced bugs.

## Product and launch
- Distinguish feature equivalence from differentiation, using source-linked user pain.
- Research 2-3 competitor prices with capture date, pricing model, and meaningful limitations; label a proposed price as a hypothesis.
- Avoid fake reviews, ratings, endorsements, ranking claims and unsupported comparisons. Keep brand/name/assets original.
- Before store preparation, retrieve current official store requirements. Use listing.py as a limited field/length linter, not policy or trademark clearance.
- sweep.py scans names, domains, listed brand colours and paths. Binary media are only enumerated; review image/audio/video assets and fonts separately.
- Public release remains subject to the user's explicit authorization and the project's existing gates.

## Source
Adapted from the QA, entrepreneur, brand and launch ideas in https://github.com/Jakeschincariol/replica-skill; MIT license in replica-skill-LICENSE.
