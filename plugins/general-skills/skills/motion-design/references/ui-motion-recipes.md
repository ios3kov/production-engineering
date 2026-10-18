# UI motion recipes

Choose a recipe only when it helps explain a state change in the requested interface. Reuse the project's motion tokens and the target platform's tools. These are optional implementation prompts, not a second design workflow. Sources and exclusions are in [the source register](../../../references/ui-refinement-sources.md).

## Match motion to the interaction

| Situation | Design and implementation prompt | Verify |
|---|---|---|
| A menu or popover opens from a control | Make the visual origin agree with its trigger and placement; for a web transform, check the transform origin against the actual anchored edge. Keep focus and visibility tied to the real open state. | Reopen or dismiss during entry, change placement near an edge, and check focus return. |
| An action is pending, succeeds or fails | Keep feedback tied to the actual operation. Use known progress only when it exists; transition to success only after confirmation. Preserve the action label and layout sufficiently to avoid an accidental second activation. | Slow response, failure, repeated input and cancellation where supported. Animation completion must not masquerade as operation completion. |
| A selected tab, segment or related element changes | If a moving indicator clarifies continuity, derive its destination from the selected element's current geometry. Keep stable identity and preserve the selected state independently of the transition. | Change selection again mid-transition; try longer labels, resized layout and the relevant input methods. |
| A sheet or panel follows a drag | Track the visible position during the gesture, then settle or dismiss according to the product's actual gesture contract. Consider release velocity and distance together where the platform supports it. | Slow drag, fast release, cancelled gesture, interrupted settling and the equivalent non-drag action. |

## Implement the smallest sufficient transition

- Use an existing capability first: a simple web state transition may need only CSS; a gesture or coordinated layout transition may justify the library already in the project. Do not add Motion, GSAP or another package merely because a recipe contains animation.
- Distinguish initial appearance from later state changes. Avoid replaying an introduction on every update or delaying a frequent control's useful response for decoration.
- Animate the properties needed for the purpose rather than `transition: all`. Choose timing and easing from existing tokens, then judge them at actual speed and with repeated use. A published duration, spring setting or press scale is a starting point, not a universal gate.
- Keep essential state and actions available with reduced motion. Use an immediate state change or a suitable low-motion alternative; removing motion must not remove the confirmation or recovery path.
- Apply [interruption and profiling](../../../references/interface-practice.md#motion-interruption-and-profiling) to retargeting, stale callbacks, pointer cancellation and measured performance. CSS, transforms or a particular library do not by themselves guarantee GPU execution or smooth device performance.

## Report only observed behavior

For implementation, preview the actual interaction and its relevant interruptions. Record the resulting state and any motion or device checks not run. For a plan or static reference, label timing and trajectory as proposals. Do not infer a passing animation, accessibility result or frame rate from a still image.
