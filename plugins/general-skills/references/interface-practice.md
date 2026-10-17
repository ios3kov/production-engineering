# Interface practice: scoped additions, not another design framework

Load only the part relevant to the current task. Preserve the user's brief, approved identity, framework and existing gates. A typo repair does not require several prototypes, a new palette or a whole-product audit. These are original adaptations; sources and omitted upstream behavior are in [interface-sources.md](interface-sources.md).

## Purpose and content

Identify the primary job of this screen: help someone decide, perform a task, read information, or examine work. Mixed screens can assign different jobs to sections. This is a design aid, not a mandatory four-value taxonomy. A portfolio can foreground an expressive work sample while a plugin's working panel prioritizes controllability and predictable state.

Make structure carry actual information. Numbering implies a real sequence; a chart needs real data; controls need working behavior. Choose the strongest truthful first-screen content: a useful headline, the work itself, a verified demo or a relevant interaction. Never invent testimonials, integrations, metrics or a plugin effect. Clearly label illustrative mockups. Keep approved styles even when an upstream author dislikes them.

## Stress real inputs

Use existing component props, a Storybook/preview route, fixtures or a test API. Do not edit the rendered DOM to fabricate success. Exercise relevant combinations: one-character and long unbroken names/IDs, Cyrillic and other supported languages, RTL/IME when applicable, large counts, zero/empty lists, absent images, long action labels, narrow viewport and enlarged text. Use deterministic non-personal data. Do not shorten required copy or erase inputs simply to make the layout fit.

Check initial, loading, empty, error, retry and permission states, not only the populated screenshot. Intentional cropping or truncation is acceptable only when the required information remains obtainable; record the reviewed reason rather than hiding the measured observation.

## Working variants

For an unresolved interface decision, expose genuinely different working variants behind a switcher in a separate preview. Share the same data and essential task, label differences, and retain the original until a decision is made. No production route, dependency or analytics installation is implicit. Record the selected option and whether the prototype is retained or removed. For an already approved design, implement it rather than reopening the choice.

## Recovery and clear language

Preserve non-sensitive user input after recoverable request failures. Show what failed, what is retained, and a concrete next action using the same action name as the control. Do not store passwords or tokens to satisfy a generic draft-preservation rule. A retry must not create duplicate side effects; UI disabling is not server-side idempotency proof.

Handle Escape, pointer cancellation, lost pointer capture, window blur, component disposal and interruption where relevant. Restore coherent state and focus. Include keyboard and touch paths; retain IME composition semantics. Distinguish unsaved draft, in-flight request and committed data. Report genuine failures rather than fake success toasts.

## Motion interruption and profiling

Specify trigger, start/current/target states, order, cancellation/reversal, and reduced-motion alternative. A second action during the transition should retarget from the current visible state instead of snapping to an obsolete starting value. Prevent stale completion callbacks from changing state or focus after cancellation/disposal. Check repeated inputs and the final state with real interactions. Testing the final state alone does not prove trajectory continuity.

Record a performance trace before optimizing. Separate layout/paint/compositing, expensive JavaScript, resource loading and inappropriate simultaneous work. Measure before/after in the same environment. Add will-change, layers or dependencies only for an observed reason and remove temporary hints when no longer needed. There is no minimum number of moving elements, universal duration, mandatory easing or automatic 60-fps claim. Web heuristics are not a substitute for SwiftUI/AE/Godot host behavior.

## Measurements and rendered review

Wait for the intended data/fonts to settle with a finite timeout. Inspect geometry, overflow, clipping, line-fragment rows, image/font failures and potential obstructions in the actual state and at matched viewports. Keep measurements separate from intent and aesthetic judgment. A declared font family is not proof of the font used for every glyph; hit testing is not painted-pixel visibility or accessibility verification. Retain scope omissions and review intentional effects.

Use real Playwright actions and independent state/data assertions before screenshots. Freeze motion only for stable appearance snapshots, never for the test intended to assess motion. Compare reviewed baselines with matching browser/OS/fonts/viewport/scale; newly generated images require review through existing evidence records. Do not automatically update snapshots to turn a failure green. Preserve traces, revision, environment and raw observations. The parent repository's optional browser collector is a separate tool, not bundled into this skill or automatically run.

## Reference research

Start with a concrete question and a small relevant reference set, not a compulsory visit to every gallery. Use Refero for complete product flows when an authorized connection or permitted pages are available; Details for a specific site section; Design Spells for a particular interaction. Available browser/MCP access and current provider terms must be checked, not presumed. Missing access is a recorded gap, not permission to bypass a paywall or bulk-extract content.

For each reference record provider/original product, URL, date/platform, task, observed states, interpretation, transferable principle and reuse constraints. Describe a motion example as trigger → state change → feedback → cancellation. Gallery selection does not establish conversion, usability or performance. Separate observation from inferred implementation. Recreate suitable principles with native tools; do not silently import original logos, fonts, assets or copy-ready code without licensing review.

Refero material must not be added to training/fine-tuning datasets, model evaluations, benchmarks or AI-improvement pipelines without separate written permission. Keep ordinary product research separate from evaluating these agent skills. Use our own synthetic fixtures for agent/tool tests. Never post confidential data or credentials to a provider merely because it offers AI or MCP access.
