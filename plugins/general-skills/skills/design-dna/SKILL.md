---
name: design-dna
description: Extract a measurable design system, visual style and effects from screenshots, websites, or design references, then apply or compare it. Use for brand direction, presentation design, product UI, websites, or any visual-reference analysis.
---

# Design DNA

Turn visual inspiration into an explicit, reusable design specification. This applies to websites, mobile apps, documents, slides and brand assets—not only code.

## Process

1. **Identify references and medium.** Determine which reference is the source of truth and what must be produced. Distinguish an image, live website, existing project, or verbal style brief.
2. **Measure before inferring.** For screenshots, use pixel inspection or a reproducible color-analysis tool if available. Record measured colors separately from estimated colors. For a live site, inspect styles and computed values only when the environment permits. Never claim a guessed hexadecimal code is exact.
3. **Extract three layers.**
   - **Design system:** palette and roles, typography, scales, grid, spacing, corner radii, elevation, component hierarchy, breakpoints, motion tokens and accessibility requirements.
   - **Design style:** mood, imagery, density, visual hierarchy, tone, composition, distinctive features and explicitly unwanted clichés.
   - **Visual effects:** Canvas/WebGL, shading, 3D, scrolling, transitions, cursor and particle effects, if present.
4. **Record confidence.** Mark tokens as measured, directly observed, or inferred. For screenshots, font names and exact dimensions may be uncertain.
5. **Generate a compact specification.** Use readable Markdown by default; emit structured JSON when it will be consumed by code or another tool.
6. **Apply and visually verify.** If a preview or rendered output is available, compare it against the reference at equal dimensions. Check colors, proportions, typography and critical states. Revise measurable mismatches.

## Deliverables

A concise design profile with: reference/source; palette with confidence; typography; layout/spacing; elements; motion/effects; accessibility; do/don't rules; open questions; and the next practical step.

Do not treat copying a reference as permission to copy protected assets or branding. If the user wants an original design, extract principles, not identity. Do not install or execute any reference site's scripts unless required and authorized.

## Source

Adapted workflow based on [zanwei/design-dna](https://github.com/zanwei/design-dna). Its pixel-measurement and visual-verification scripts are separate upstream tools; they are **not** bundled or claimed to have run here.
