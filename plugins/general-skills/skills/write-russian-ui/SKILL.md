---
name: write-russian-ui
description: "Create, review, or revise Russian interface strings: buttons, field labels, hints, validation, errors, and empty, loading, or permission states. Use for Russian UI copy in screen drafts or application localization files. Exclude ordinary conversation, correspondence, marketing copy, documentation, and translation unrelated to an interface."
---

# Write Russian UI

Make the next action and the current state understandable without changing the product's meaning.

## Establish the contract

- Read the supplied screen, current strings, surrounding flow, and relevant implementation or specification. Reuse known facts and the project's terminology.
- Identify what the user can actually do, what has already happened, and what the component knows. Treat confirmed behavior as a constraint on wording; style cannot override it.
- Separate a copy problem from missing behavior or a broken flow. Report a behavior issue when found; do not add retries, permissions, saving, navigation, or other logic merely to make the proposed text true.
- Follow the requested mode. In a review, propose changes without editing files. When edits are authorized, change the relevant strings within that scope. Do not turn either task into a redesign.
- If one missing fact changes the meaning or consequence, inspect the available source first. Ask only for that material fact when necessary; continue with strings that can already be resolved.

## Write the state and action

- Name controls by their actual action or destination. Keep field labels distinct from examples and hints; retain information needed to enter a valid value.
- For errors, explain what failed and offer a recovery action only when that action exists and can help. State a cause only when evidence supports it. Preserve meaningful distinctions such as expired access versus a rejected value.
- Distinguish an empty collection from no search results, loading, and a failed request. Do not imply that missing data was deleted.
- For loading, name the operation. Do not invent percentages, completion times, background processing, or cancellation support.
- For permission states, explain the relevant capability and available next step. Do not claim that access is granted, required, or recoverable through settings without checking the actual flow.
- Do not promise saved work, successful delivery, reversibility, retention, free access, or a deadline unless the contract establishes it. Make significant consequences explicit rather than softening them with reassuring wording.
- Preserve the product's voice and established names. Prefer one recommended version per string. Add alternatives only when the user requests them or an unresolved constraint makes the choice useful.

Read [state examples](references/state-examples.md) when a state distinction or localization edit needs a concrete model.

## Preserve localization and style

- Inspect the localization format and edit user-visible wording only. Preserve keys, IDs, variables, placeholder names, ICU plural/select structure and selectors, interpolation, tags, links, and required escaping. Do not alter embedded code or user-provided values.
- If clear wording would require a new placeholder, a changed ICU branch, or another contract change, identify that separately; do not silently perform it as copy editing.
- Follow the project's choices for quotes, «ё», percentage spacing, punctuation, and abbreviations. Do not apply global typographic substitutions. Treat nonbreaking spaces and text length as layout decisions to check on the smallest relevant screen.
- Keep visible copy and accessible names consistent in meaning. Preserve relevant accessible context when shortening text.

## Verify and return

- Check each proposed string against its actual state and available action. Compare modified localization structures with the originals; run the existing parser or relevant localization check when editing files.
- When the interface is available, inspect the affected strings with representative values, including longer names and plural forms, at the relevant sizes. Use the established UI verification workflow. Report visual checks as unverified when no rendered screen is available.
- For review, return the material issues and one proposed replacement for each; use a before/after table when it helps comparison. For edits, report the changed strings, checks performed, and any unresolved contract question. Keep small tasks small.
- Finish when the requested strings are covered, confirmed meaning is preserved, and the verification limits are explicit. Do not claim a copy change fixed behavior that was not changed and checked.

## Source

Conceptual reference: [Sasha by mishanaer](https://github.com/mishanaer/deslop/blob/c38287513d3d1e4b04be0d349380633c1a9d49f2/sasha/SKILL.md), reviewed 2026-10-18. This skill and its examples are independently written; no upstream files or scripts are included. No license grant for the upstream material is asserted.
