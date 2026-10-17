---
name: competitor-recon
description: "Inventory a named app's publicly observable screens, states, flows, features and product constraints; ground each claim in a source and keep uncertain internals unknown."
---

# Competitor Recon

Use this for an explicitly named competing product or concrete UI/behavior reference. This is an optional research method, NOT a substitute for the project's existing AS/AE Reference Audit, implementation plan or release gate.

## Source and authorization
1. Fix scope (platform, target version/date, one feature or full product) and user goal. For a small request, limit the work to that area.
2. Examine public help docs, pricing, changelog, store listing, authentic walkthroughs and public API docs, then the user's authorized account when permitted. Record URL, date, version and evidence strength.
3. Inspect only permitted material. Never bypass login or paywall, harvest private content, copy proprietary code/assets or inspect private endpoints. Observe the behavior rather than infer internals.

## Evidence-first inventory
4. Inventory screens as S01... with route, components and all applicable states: empty, loaded, error, offline, permissions, long text, narrow viewport.
5. Inventory user goals as F01...; record screen sequence, number of actions, errors, recovery, persistence, account/permission boundaries, imports/exports and integrations.
6. Inventory entities/relationships only when supported. Mark each substantive claim PROVEN, OBSERVED, INFERRED or UNKNOWN, with direct links or artifact IDs. Never promote inferred schema to fact.
7. Make a feature matrix with columns: feature,area,priority,original,clone,check_id,notes. Use must/should/could; original yes/no; clone yes/partial/no/skip. Leave clone unverified until tested.
8. List legal/product exclusions explicitly: licensed datasets, network effects, private integrations, brand marks, partnership rights and data. Measure complexity and the smallest useful differentiated product.

## Optional UI-flow reference source

When relevant, [Refero](https://refero.design/mcp) can supplement public product documentation with a complete registration, payment, settings or recovery flow. Use only an actually available authorized connection or permitted pages; this skill does not bundle that service. Capture sequence, states, platform/date, source and uncertainty, then verify important claims against the named product. Keep the analysis inside the inventory above, not a parallel audit.

Check the [current provider terms](https://doc.refero.design/legal/terms-of-use) before using its material. Keep Refero content out of AI training, fine-tuning, model evaluation, benchmarks and datasets without separate written permission. Ordinary product design does not authorize bulk extraction, redistribution or bypassing a paywall. Without access, use authorized product documentation or user-supplied references and record the gap.

## Outputs
Write in the user's chosen destination, default research/competitors/<slug>/recon.md and features.csv. Briefly give scope, screen and flow counts, what is evidenced, hard constraints, and priority gaps. Use existing project acceptance/evidence contracts rather than establishing a second gate.

## Source
Adapted from Jake Schincariol's replica-recon: https://github.com/Jakeschincariol/replica-skill (MIT; exact pin in ../../references/UPSTREAM.md).
