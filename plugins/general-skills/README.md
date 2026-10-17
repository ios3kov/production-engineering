# General Skills for ChatGPT Work and Codex

An optional, cross-project set of eight **independent** Agent Skills. No changes to the existing `production-engineering` skill or the AE/AS project rules are required.

## Version 1.1.0

`brainstorming` gains an optional visual-mechanism library. `genjutsu` gains a scoped production brief, identity/product-truth checks and cause-specific visual repair. Details, acceptance scope and verification limits are in the [changelog](CHANGELOG.md). The other six skills, including `design-dna`, are unchanged. Publishing an update here does not prove that an already installed copy has refreshed; check its version in the supported client.

| Skill | Use when |
|---|---|
| `design-dna` | Extracting and applying a design system from visual references |
| `genjutsu` | Art direction, polish, visual QA and accessibility |
| `motion-design` | Motion principles, timing, choreography and critique |
| `gsap` | GSAP / ScrollTrigger web animation |
| `threejs` | Three.js / browser 3D |
| `brainstorming` | Finding non-obvious, genuinely different ideas |
| `research-methodology` | Source-grounded deep research |
| `fact-check` | Checking factual claims in a separate review pass |

These are **host-neutral original adaptations** informed by the credited upstream projects in each `SKILL.md`. They are not copies of the original projects; upstream scripts and optional dependencies are not included. Skills are activated only when task-relevant, not permanently injected into every prompt.

## Install for Codex

```bash
codex plugin marketplace add ios3kov/production-engineering
codex
```

In Codex, use `/plugins`, select marketplace **ios3kov Skills**, then install **General Skills**. Start a fresh session. The Codex CLI plugin marketplace commands require a version that supports plugin marketplaces.

## Install for ChatGPT Work

The marketplace lives at `.agents/plugins/marketplace.json`. In ChatGPT desktop/Work, register or open this repository as a local marketplace (as supported by your client), then install **General Skills** from Plugins and start a new conversation. If your workspace supports GitHub marketplace import, an admin can import this repository via Admin > Plugins > Import marketplace; selecting this repository does **not** automatically install it.

See official [OpenAI plugin packaging/marketplaces docs](https://developers.openai.com/plugins/build/plugins). Installation and permissions depend on product, account and workspace settings. **Publishing to GitHub is not installation in your ChatGPT or Codex account.**

## Design choices

- Host-neutral: no Claude-only directives, implicit shell access, or mandatory external packages.
- Least privilege: no scripts, hooks, MCP tools, shell commands or background jobs are bundled.
- Independent: `production-engineering` remains a separately maintained and separately installed skill.
- Research accuracy: no claim of measurement, runtime validation, external evidence or accessibility compliance without performing the relevant check.
- For up-to-date third-party APIs (GSAP, Three.js, SwiftUI) consult the current upstream docs before code changes.
