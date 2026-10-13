---
name: fact-check
description: "Run a separate claim-by-claim verification pass on reports, drafts, analyses or generated answers, with grounded sources and explicit correction of false or unsupported assertions."
---

# Fact Check

Verify substantive claims **after** a draft or analysis exists, not while improvising the same claims.

## Process

1. Extract checkable statements: names, dates, numbers, comparison claims, quotes, causal assertions, capability claims, version and licensing details.
2. Classify each as verifiable fact, attribution, inference, opinion, or prediction. Focus on material facts and high-impact errors.
3. Seek primary source evidence and independent corroboration where appropriate. Follow the exact source link; do not treat search results, summaries or model memory as confirmation.
4. Compare exact wording, scope, conditions and dates. For statistics check denominator, timeframe and collection method. For quoted words verify exact attribution and context.
5. Assign status to each material claim: VERIFIED, PARTLY SUPPORTED, CONTRADICTED, UNVERIFIED or OUTDATED.
6. Fix false claims in the draft, qualify unsupported statements, and retain citations. Recheck any important correction.
7. Return a concise corrected version and a short audit of remaining unknowns or disputed facts, if useful.

## Constraints

An additional self-review without external evidence is not independent verification. No source access = NOT VERIFIED, not 'probably true'. A clean-looking citation is not proof unless it supports the claim. Do not manufacture checks or imply that every claim was reviewed if some were intentionally skipped.

## Source

Adapted from [jwynia/agent-skills fact-check](https://github.com/jwynia/agent-skills/tree/main/skills/general/research/verification/fact-check).
