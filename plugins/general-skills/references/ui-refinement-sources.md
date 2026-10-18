# UI refinement source register

Reviewed 2026-10-18 against the five skills shown in the supplied video. Links below pin the inspected source revisions. This is a supplement to the earlier [nine-source register](interface-sources.md), whose review scope and date remain unchanged. A source pin records the material reviewed; it is not an installed dependency or a claim about a later version.

| Source | What is adopted | Destination and limits |
|---|---|---|
| [Pick UI Library — Emil Kowalski](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/skills/pick-ui-library/SKILL.md) | Start from the existing stack and consult a capability-based catalog when a dependency decision is needed. | Optional lookup in [typography and UI polish](ui-typography-and-polish.md). Selected web candidates only; no automatic installation, migration or assumption of current compatibility. |
| [Animate — Emil Kowalski](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/skills/animate/SKILL.md) | Purpose-led origin, state feedback, moving indicators and gesture continuity. | [UI motion recipes](../skills/motion-design/references/ui-motion-recipes.md). Reuse the existing interruption/profiling guidance instead of duplicating it. |
| [Sasha — mishanaer](https://github.com/mishanaer/deslop/blob/c38287513d3d1e4b04be0d349380633c1a9d49f2/sasha/SKILL.md) | Clear Russian interface actions and states, truthful recovery wording and preservation of localization structure. | New [Write Russian UI](../skills/write-russian-ui/SKILL.md), restricted to interface strings. Ordinary conversation, marketing and documents are outside its trigger. |
| [Better Typography — Jakub Krehel](https://github.com/jakubkrehel/skills/blob/4c66b1fa86e9ab70187b43d7da9b6fdb29f2ef63/skills/better-typography/SKILL.md) | Check actual font use, roles, weights, wrapping and changing numbers in the rendered interface. | Optional checks in [typography and UI polish](ui-typography-and-polish.md). Preserve typography tokens; numeric preferences are not universal requirements. |
| [Better UI — Jakub Krehel](https://github.com/jakubkrehel/skills/blob/4c66b1fa86e9ab70187b43d7da9b6fdb29f2ef63/skills/better-ui/SKILL.md) | Inspect nested corners, optical alignment, surface hierarchy and interaction refinement after behavior is understood. | The same Genjutsu supplement. Its aesthetic checks do not replace the project's accessibility gates. |

## Deliberate adaptations

- Keep the existing design and product contract authoritative. Do not turn a local polish request into a redesign, a dependency migration or new behavior.
- Keep author-specific sizes, corner cutoffs, timings, easing preferences, animation-frequency limits and button scales as contextual examples. No mandatory quota, score, blur treatment or palette is added.
- Sasha informs an independently written, narrower UI-copy skill. Do not carry over a fixed number of alternatives, universal punctuation or «ё» substitutions, or the upstream scripts. Keys, interpolation, tags and ICU structures remain intact during copy edits.
- The reviewed Better UI source delegates accessibility to a separate skill. The video's tap-area claim is not treated as evidence that Better UI itself supplies a complete accessibility audit. Existing keyboard, focus, hit-area, contrast and reduced-motion checks remain applicable.
- Do not adopt a welcome-only response, mandatory remote rereading or an unverified performance claim. Read only the local supplement needed for the current task; consult current primary technical documentation when implementing a version-sensitive API.

All added guidance and examples are independently written. No upstream skill files, code, scripts, fonts or media are bundled. No reuse license for the original Sasha material is asserted.
