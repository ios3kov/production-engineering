# Typography and UI polish

Use only the subsection relevant to the requested interface change. Keep the established visual language, typography roles, component contracts and platform conventions. This supplements [interface practice](interface-practice.md); it does not reopen approved design decisions. The independently adapted ideas and exclusions are recorded in [the source register](ui-refinement-sources.md).

## Typography in the actual interface

Start from the project's font assets and role tokens. Determine whether the defect comes from font loading, the layout, the content or an inconsistent token before changing the font or size.

| Inspect | Practical check |
|---|---|
| Font and glyph coverage | After fonts settle, inspect the face actually used for relevant text, including Cyrillic and required symbols. A declared family does not establish glyph coverage. Investigate a fallback or missing weight before substituting the brand font. |
| Roles and weights | Compare equivalent labels, body text, captions and headings against existing tokens. Confirm the requested weight exists or has an intended variable-font value; preserve intentional hierarchy. |
| Line height and spacing | Inspect clipped glyphs, awkward multiline controls and inconsistent baselines at real sizes. Adjust the affected role or container; do not apply a universal minimum size, line length or tracking value. |
| Wrapping and truncation | Exercise representative long labels, names and values at the smallest supported layout and enlarged text. Keep required information obtainable through a real supported path. A tooltip alone may not serve touch and keyboard users. |
| Changing numbers | When counters, prices or timers cause visible width jitter, consider the existing font's tabular figures and suitable alignment. Verify the feature is supported and useful for that component. Static prose does not need it by default. |
| Localization | Retain meaningful text, units, placeholders and the product's conventions. Test supported scripts and direction where relevant. Do not shorten required wording or add nonbreaking spaces everywhere just to make one screenshot fit. |

Inspect rendered changes with the intended data and fonts. Source-code inspection can identify a likely issue; it does not establish legibility, clipping, actual glyph selection or device behavior. If rendering is unavailable, return a proposed correction and the unverified checks.

## Component refinement

- **Nested corners:** for an intentional, evenly inset rounded surface, an inner radius near `max(0, outer radius - visible inset)` can be a useful starting point. Account for borders, clipping and the actual shape, then inspect the result. Keep approved corner tokens when they already produce the intended relationship; the formula is not a global lint rule.
- **Optical alignment:** compare the apparent icon or glyph with its label as well as its geometric box. Adjust only the visible alignment when needed. Preserve the control's semantic meaning, accessible name and interaction bounds.
- **Edges and elevation:** use existing border, background and shadow roles to make boundaries and hierarchy readable. Inspect contrast and adjacent surfaces. Do not add blur, outlines or shadows to every component.
- **Interaction states:** inspect the affected default, focus, pressed, selected, disabled and pending states where applicable. Keep their real meanings distinct. On the web, hover-only decoration should be gated for hover-capable input; essential feedback must also work with keyboard and touch.
- **Overlays and scrolling:** where scrolling an open panel accidentally moves the page behind it, inspect the platform's overlay and scroll-containment behavior. Preserve intended inner scrolling, dismissal and focus return. A CSS declaration or screenshot alone does not prove those interactions work.

Use [Motion Design](../skills/motion-design/SKILL.md) only if motion is part of the refinement. A fixed press scale, duration or easing from a reference is an example to evaluate against the product's tokens, not a required correction.

Visual polish does not replace applicable accessibility checks. Keep the project's keyboard, focus, hit-area, contrast, accessible-name and reduced-motion gates. Report their actual coverage separately from an aesthetic judgment.

## Optional web-library lookup

Use this section only when a web component needs a capability that the current stack does not already provide adequately. Inspect the project's manifests, lockfile and existing component patterns first. For native UI, start with that platform's controls and APIs instead.

The reviewed author catalog offers possible candidates to investigate:

| Needed capability | Candidate from the catalog |
|---|---|
| Low-level React UI primitives | Base UI |
| Command menu | cmdk |
| Toast notifications | Sonner |
| One-time-code input | input-otp |
| Animated number display | NumberFlow |

Before recommending a new dependency, consult its current primary documentation for the project's version and platform. Compare the existing solution with the candidate on required behavior, accessibility support, styling fit, maintenance, license and practical integration cost. These names are a lookup aid, not evidence of compatibility or a reason to replace working components. Installing or migrating a dependency must fit the actual task's authorization.

For a decision, state the missing capability, preferred option and material tradeoff. A small refinement that existing CSS, components or native APIs can handle does not need a library-selection exercise.
