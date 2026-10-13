---
name: gsap
description: "Implement, inspect or optimize GreenSock GSAP timeline animations, text reveals, React integration and ScrollTrigger on web projects where GSAP is present or explicitly requested."
---

# GSAP

Only activate for web animation tasks using GSAP or requests explicitly asking for GSAP. Do not inject GSAP into unrelated outputs.

## Implementation protocol

1. Inspect the project, GSAP version, existing plugins, framework, scroll setup, and reduced-motion strategy. Prefer the project's current animation stack; don't install or migrate packages without an actual need and authorization.
2. Sketch a timeline: target, trigger, start/end states, duration, ease, stagger and cleanup ownership.
3. Implement with GSAP timelines rather than many unrelated delayed tweens when actions form one sequence. Use GSAP's documented lifecycle patterns for the host framework.
4. Prefer transforms and opacity instead of layout properties for moving elements. Avoid interleaving DOM measurements and writes; use gsap.quickTo for frequently updated mouse/drag targets.
5. For ScrollTrigger, be deliberate about pin, scrub, refresh timing, nested scrolling and when content/layout changes. Do not refresh on every animation frame.
6. Clean up tweens, timelines, triggers and listeners on unmount/disposal; stop inactive/offscreen animation when appropriate.
7. Honor prefers-reduced-motion; provide nonanimated functional states where necessary.
8. Verify in a real browser at relevant viewport sizes and under representative load. A code review is not an FPS measurement.

## Do not

No unconditional force3D or will-change on everything; no hundreds of simultaneous tweens by default; no auto-registration of unused plugins; no assumptions about paid/licensed availability without checking current licensing.

## Source

Adapted from the [official greensock/gsap-skills](https://github.com/greensock/gsap-skills), especially performance and timeline guidance. See [GSAP documentation](https://gsap.com/docs/v3/) for version-specific APIs.
