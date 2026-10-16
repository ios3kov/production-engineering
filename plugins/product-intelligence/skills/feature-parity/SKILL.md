---
name: feature-parity
description: "Compare observable competitor functionality with a candidate product using a scoped feature matrix, source-linked behavior checks and optional artifact-hash-backed test records; expose unverified work explicitly."
---

# Feature Parity

Use after competitor-recon or when comparing a concrete product with a candidate implementation. A product can perform the same user job without copying look, brand or source code.

## Functional comparison
1. Read recon.md, features.csv and the project's own source-of-truth specification. Check that target version and comparison scope match.
2. Mark each feature yes/partial/no/skip with a reason; prioritize must/should/could. New advantages absent from the original are listed separately and are not included in similarity scores.
3. Run: python3 scripts/parity.py features.csv --markdown > parity.md. This is only a DECLARED score, not proof of implementation.
4. For evidence-backed comparison, use an existing trusted test runner to produce checks.json: {"subject_sha":"EXACT_BUILD_SHA","checks":[{"id":"F01-H1","status":"PASS","artifact_path":"qa/F01.json","sha256":"SHA256_OF_FILE"}]}. Set check_id in each feature row, then run: python3 scripts/parity.py features.csv --checks checks.json --subject-sha EXACT_BUILD_SHA --markdown > parity.md.
5. The helper checks artifact bytes/hashes and a declared subject identifier, but cannot authenticate who produced the PASS status. Trust comes from the project's established CI and Evidence authority. Do not call a row proven based only on this helper.

## Behavioral QA
6. Compare core end-to-end flows with exact expected outputs, not just visuals. Include failure recovery, offline/slow network, double submission, concurrency, permissions, locale/time zones, keyboard/accessibility and data isolation as applicable.
7. Create test cases F01-H1, F01-E1 and F01-N1 (happy, edge, negative). Only mark tests PASS when genuinely executed against the identified build. Record missing devices/services as NOT_RUN or BLOCKED.
8. Separate layout screenshot inspection from behavior parity. No image similarity score establishes UI correctness. Existing AS/AE reference render comparators remain authoritative for their specific products.

## Release and positioning helpers
9. For a separately branded product use python3 scripts/sweep.py . --config brand.json --inventory-assets; review binary assets manually. For store copy use python3 scripts/listing.py listing.json --rules store-rules.json --require-current-rules only after reviewing official current sources. Neither script certifies trademarks or store approval.
10. Use references/QA_AND_LAUNCH.md for optional QA/positioning considerations. Existing project release gates supersede this skill; do not create duplicate policy or auto-publish.

## Outputs
Default research/competitors/<slug>/parity.md with feature and flow gaps, declared vs checked scores, precise missing evidence, top five fixes and differentiation. Stop describing verified readiness if required checks or target device tests are missing.

## Source
Adapted from Jake Schincariol's replica-diff, replica-test and replica-launch: https://github.com/Jakeschincariol/replica-skill (MIT; exact pin in ../../references/UPSTREAM.md).
