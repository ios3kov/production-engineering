---
name: motion-design
description: "Plan, create and critique intentional motion for UI, typography, presentations, videos and animation assets: hierarchy, easing, timing, choreography, user feedback, accessibility and performance."
---

# Motion Design

Design animation to communicate state, hierarchy, personality or story, not to fill empty space.

## Workflow

1. **Purpose.** State what the viewer must notice, understand or feel; determine where animation adds value and where stillness wins.
2. **Hierarchy.** Specify the primary action, supporting motion and optional ambient motion. Avoid simultaneous competing focal points.
3. **Motion language.** Choose position, scale, opacity, rotation, path, speed, anticipation, follow-through and easing to match the medium and meaning. Prefer consistent patterns for recurring interactions.
4. **Choreography.** Order events with explicit dependencies; use restrained stagger and avoid making routine actions feel slow. Entry and exit motion should communicate origin and destination.
5. **Implementation.** Pick native capabilities for the target: AE keyframes, SVG/Lottie where supported, GSAP on appropriate web stacks, SwiftUI animation for Apple UI, or static alternatives. Do not assume interchangeability or promise lossless export.
6. **Verify.** Preview at actual playback speed. Check clarity, contrast, device performance, motion sensitivity and an appropriate reduced-motion or static alternative.

## Interruption and profiling

For interactive transitions, consult [motion interruption and profiling](../../references/interface-practice.md#motion-interruption-and-profiling). Repeated actions, reversal, cancellation, lost pointer capture and reduced motion must leave a coherent final state. Inspect the actual performance trace before changing rendering strategy; never add a motion quota or blanket will-change. [Design Spells](https://designspells.com/) is an optional reference for interaction mechanics, not a ready-made exporter. Sources: [adoption register](../../references/interface-sources.md).

## Heuristics, not hard rules

- Ease-in / ease-out usually reads more naturally for spatial motion than constant speed. Linear is appropriate for constant-rate rotation, progress, and intentionally mechanical movement.
- Keep interface feedback fast enough not to block tasks; reserve long sequences for intentional storytelling.
- Animate transforms and opacity where possible on the web; avoid unnecessary layout reflows.
- For accessibility, do not convey critical meaning solely through motion or color.
- Quantitative thresholds from a reference guide are starting points, not universal pass/fail conditions.

## Output

Provide a compact motion brief, ordered cues, recommended easing and approximate timing, platform-specific execution notes and a verification checklist.

## Source

Adapted from [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill). This skill provides motion principles; it does **not** include an automatic Lottie exporter.
