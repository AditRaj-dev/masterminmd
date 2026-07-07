# Impeccable — design quality bar (merged reference)

Condensed from the impeccable skill (v3.7.1, Apache 2.0): core design guidance + brand/product registers + production bar + audit rubric. Self-contained — no impeccable scripts or sub-commands required.

Designs and iterates production-grade frontend interfaces. Real working code, committed design choices, exceptional craft. Produce ready-to-ship code, not prototypes. Don't stop until arriving at a complete implementation (beautiful, responsive, fast, precise, bug-free, on brand).

**Pick the register first:** if the surface is marketing, a landing page, a campaign, long-form content, or a portfolio (design IS the product), use the **Brand register** below. If it's app UI, admin, a dashboard, or a tool (design SERVES the product), use the **Product register**.

## General rules

### Color

- **Verify contrast.** Body text ≥4.5:1 against its background; large text (≥18px or bold ≥14px) ≥3:1. Placeholder text needs the same 4.5:1. Most common failure: muted gray body text on tinted near-white. If contrast is close, bump body color toward the ink end of the ramp.
- Gray text on a colored background looks washed out. Use a darker shade of the background's own hue, or a transparency of the text color.

### Typography

- Cap body line length at 65–75ch.
- Don't pair fonts that are similar but not identical (two geometric sans-serifs). Pair on a contrast axis (serif + sans, geometric + humanist) or use one family in multiple weights.
- Hero heading ceiling: clamp() max ≤ 6rem (~96px). Display letter-spacing floor: ≥ -0.04em.
- `text-wrap: balance` on h1–h3; `text-wrap: pretty` on long prose.

### Layout

- Vary spacing for rhythm.
- Cards are the lazy answer. Use them only when truly the best affordance. Nested cards are always wrong.
- Flexbox for 1D, Grid for 2D. Responsive grids without breakpoints: `repeat(auto-fit, minmax(280px, 1fr))`.
- Semantic z-index scale (dropdown → sticky → modal-backdrop → modal → toast → tooltip). Never 999/9999.

### Motion

- Motion is intentional, part of the build, not an afterthought.
- Don't animate CSS layout properties unless truly needed. Ease out with exponential curves (ease-out-quart/quint/expo). No bounce, no elastic.
- Use libraries for advanced motion (motion, gsap, anime.js, lenis).
- Reduced motion is not optional: every animation needs a `@media (prefers-reduced-motion: reduce)` alternative.
- The tell is the uniform reflex (one identical entrance on every section), not motion itself. Never ship a page with no motion at all, either.
- Reveal animations must enhance an already-visible default — don't gate content visibility on a class-triggered transition (ships blank in headless renderers).
- Premium motion materials include blur, backdrop-filter, clip-path, mask, shadow/glow — when they materially improve the effect and stay smooth.

### Interaction

- Dropdowns with `position: absolute` inside `overflow: hidden|auto` get clipped. Use native `<dialog>` / popover API, `position: fixed`, or a portal.

### New projects only

- Use OKLCH.
- **The cream/sand/beige body bg is the saturated AI default.** The whole warm-neutral band (OKLCH L 0.84-0.97, C < 0.06, hue 40-100) reads as cream/paper regardless of token name (`--paper`, `--cream`, `--sand`, `--linen`, `--ivory` are tells). Instead pick: (a) a saturated brand color as body (terracotta, oxblood, deep ochre, near-black), (b) a true off-white at chroma 0 or chroma toward the brand's own hue, or (c) a darker mid-tone tinted neutral. "Warmth" is carried by accent + typography + imagery, not body bg.
- Tinted neutrals: add 0.005–0.015 chroma toward the brand's hue.
- Dark vs light is never a default. Write one sentence of physical scene (who uses this, where, what light, what mood) — add detail until it forces the answer.
- Pick a **color strategy** before picking colors:
  - **Restrained**: tinted neutrals + one accent ≤10%. Product default.
  - **Committed**: one saturated color carries 30–60% of the surface. Brand default.
  - **Full palette**: 3–4 named roles used deliberately. Campaigns; data viz.
  - **Drenched**: the surface IS the color. Brand heroes.

## Absolute bans

Match-and-refuse. About to write one of these → rewrite the element with different structure.

- **Side-stripe borders** (`border-left/right` >1px as colored accent on cards/callouts/alerts). Use full borders, background tints, leading icons, or nothing.
- **Gradient text** (`background-clip: text` + gradient). Single solid color; emphasis via weight or size.
- **Glassmorphism as default.** Rare and purposeful, or nothing.
- **The hero-metric template** (big number, small label, supporting stats, gradient accent).
- **Identical card grids** (same-sized icon + heading + text cards repeated endlessly).
- **Tiny uppercase tracked eyebrow above every section** ("ABOUT" / "PROCESS" kickers). One named kicker as a deliberate brand system is voice; an eyebrow on every section is AI grammar.
- **Numbered section markers as default scaffolding (01 / 02 / 03).** Numbers earn their place only when the section IS a real sequence.
- **Text that overflows its container.** Test headings at every breakpoint; reduce clamp max or rewrite copy.

## The AI slop test

If someone could look at this interface and say "AI made that" without doubt, it's failed.

- **First-order:** if someone could guess the theme + palette from the category alone, it's the first training-data reflex. Rework until the answer isn't obvious from the domain.
- **Second-order:** if someone could guess the aesthetic family from category-plus-anti-references ("AI tool that's not SaaS-cream → editorial-typographic"), it's the trap one tier deeper. Rework until both answers are non-obvious.

## Brand register (design IS the product)

Landing pages, marketing, campaigns, portfolios, long-form content. The deliverable is the impression. Go big or go home — restraint without intent now reads as mediocre. Name the aesthetic lane before committing (Klim-specimen, Stripe-minimal, acid-maximalism…). Inverse test: describe what you're about to build the way a competitor would describe theirs; if the sentence fits the modal landing page in the category, restart.

**Font selection (never skip):**
1. Write three concrete brand-voice words (physical-object words, not "modern"/"elegant").
2. List the three fonts you'd reach for by reflex; reject any on the reflex-reject list.
3. Browse a real catalog (Google Fonts, Pangram Pangram, Future Fonts, Klim, Velvetyne) with the three words. Find the brand as a physical object. Reject the first thing that "looks designy."
4. Cross-check: if the final pick matches the original reflex, start over.

**Reflex-reject fonts (training-data defaults, ban for greenfield):** Fraunces · Newsreader · Lora · Crimson (all) · Playfair Display · Cormorant (all) · Syne · IBM Plex (all) · Space Mono · Space Grotesk · Inter · DM Sans · DM Serif (all) · Outfit · Plus Jakarta Sans · Instrument Sans · Instrument Serif

**Reflex-reject aesthetic lane:** editorial-typographic (display serif italic + small mono labels + ruled separators + monochromatic restraint) — saturated. Use only when the brief literally IS a magazine/terminal/signage system. (Identity-preservation wins when an existing brand already committed to a font/lane.)

- Two families minimum only when the voice needs it; one well-chosen family with committed weight/size contrast beats a timid pair.
- Modular scale, fluid `clamp()` headings, ≥1.25 ratio. Light text on dark: add 0.05–0.1 line-height.
- Color: brand has permission for Committed, Full palette, Drenched. Name a real reference ("Stripe purple-on-white restraint", "Liquid Death acid-green"). Unnamed ambition becomes beige. Don't converge across projects.
- Layout: asymmetric compositions allowed; fluid `clamp()` spacing; image-led briefs get full-bleed hero imagery.
- **Imagery: when the brief implies imagery, ship imagery.** Zero images is a bug. Unsplash default (`https://images.unsplash.com/photo-{id}?auto=format&fit=crop&w=1600&q=80`) — **verify URLs resolve before referencing; guessed IDs 404.** Search the brand's physical object ("handmade pasta on scratched wood table" not "Italian food"). One decisive photo beats five mediocre. Alt text is part of the voice.
- Brand bans (extra): monospace as lazy "technical" shorthand; large rounded icons above every heading; all-caps body copy; timid palettes ("safe = invisible"); zero imagery on image-implying briefs; defaulting to editorial-magazine aesthetics; repeated uppercase kickers.
- Brand permissions: ambitious first-load motion; single-purpose viewports; unexpected color strategies; art direction per section (consistency of voice beats consistency of treatment).

## Product register (design SERVES the product)

App UIs, dashboards, settings, tables, tools. The test isn't "would someone say AI made this" — it's: would a user fluent in Linear/Figma/Notion/Raycast/Stripe trust this interface? Failure mode is strangeness without purpose. The bar is earned familiarity; the tool should disappear into the task.

- Typography: one family is often right; fixed rem scale (not fluid); tighter ratio 1.125–1.2; prose 65–75ch, tables can run denser.
- Color: Restrained is the floor. State-rich semantic vocabulary (hover, focus, active, disabled, selected, loading, error, warning, success, info) standardized. Accent for primary actions/selection/state only. Second neutral layer for sidebars/panels.
- Every interactive component ships all states: default, hover, focus, active, disabled, loading, error. Skeletons for loading, not spinners. Empty states that teach. Consistent affordances (same button shape, same form vocabulary, same icon style).
- Motion: 150–250ms; conveys state, not decoration; no orchestrated page-load sequences.
- Product bans (extra): decorative motion; inconsistent component vocabulary; display fonts in UI labels; reinvented standard affordances (custom scrollbars, weird form controls); heavy color on inactive states; modal as first thought (exhaust inline/progressive alternatives).
- Product permissions: system fonts / familiar sans (Inter OK here); standard nav patterns; density; consistency over surprise.

## Production bar (definition of done for built UI)

- **Real content.** No placeholder copy, dead links, fake controls, unused scaffold.
- **Semantic first.** Real headings, landmarks, labels, form associations, accessible names.
- **Deliberate spacing and alignment.** No default gaps or accidental misalignment.
- **Intentional typography.** Loading strategy chosen, clear hierarchy, no overflow at any width.
- **Realistic state coverage.** Default, hover, focus-visible, active, disabled, loading, error, success, empty, overflow, long/short text, first-run.
- **Finished interaction quality.** Keyboard paths, ≥44px touch targets, feedback timing, no hover-only functionality.
- **Coherent icon set.** One library or accessible text. Don't mix.
- **Respect the build pipeline.** Edit source, run the project's build. Never write into `dist/`/`build/`/`.next/` directly.
- **Verify image URLs before referencing.**
- **Optimized media.** Correct dimensions, alt text, lazy loading below the fold, responsive `srcset`.
- **Technically clean.** Build passes, no console errors, no layout shift, no needless deps.
- After building, look at it like a designer: screenshot/preview at mobile + tablet + desktop, critique honestly against the brief and the bans, patch material defects, re-inspect. Don't invent defects to demonstrate iteration.

## Audit rubric (for reviewers)

Score 5 dimensions 0–4 (total /20; 18-20 excellent, 14-17 good, 10-13 acceptable, <10 overhaul):

1. **Accessibility** — contrast <4.5:1, missing ARIA, keyboard nav/focus, semantic HTML, alt text, unlabeled inputs.
2. **Performance** — layout thrashing, expensive animations, missing lazy loading, bundle bloat, unnecessary re-renders.
3. **Theming** — hard-coded colors vs tokens, broken dark mode, inconsistent tokens.
4. **Responsive** — fixed widths, touch targets <44px, horizontal scroll, missing breakpoints.
5. **Anti-patterns** — count the AI tells from the bans list above. 0 = slop gallery (5+ tells), 4 = no tells.

Tag findings P0 (blocking) / P1 (major, fix before release) / P2 (minor) / P3 (polish), each with location, impact, and concrete fix. Start the report with the anti-patterns verdict: pass/fail, "does this look AI-generated?", brutally honest.
