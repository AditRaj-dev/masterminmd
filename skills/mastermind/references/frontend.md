# Phases 6–7 — Frontend design + wireframe

## Phase 6 — Design system & DESIGN.md (orchestrator does this personally)

Read the bundled design references IN THIS ORDER and synthesize one `docs/DESIGN.md`:

1. **references/design/ui-ux-pro-max.md** — follow its workflow: run the bundled search engine
   `python "C:\Users\study\.claude\skills\mastermind\scripts\search.py" "<product type> <industry> <keywords>" --design-system -p "<Project>"`
   to generate the base design system (style, palette, fonts, effects). Use its `--domain` searches (style/color/typography/ux/chart) for specifics. Requires Python 3.8+; if Python is unavailable, pick style/palette/font manually from the guidance in the file and say so.
2. **references/design/taste-design.md** — use its DESIGN.md structure and anti-generic rules to write the semantic design doc (descriptive color names + hex + functional role, atmosphere scores, hero composition, component specs). Ignore its Google-Stitch-specific instructions; only the DESIGN.md format and taste rules apply here.
3. **references/design/impeccable.md** — pick the register (brand vs product), apply the register rules, then run every choice against the Absolute Bans, reflex-reject font list, and the AI slop test (first- and second-order). Anything that fails gets redesigned now, not after build.
4. **references/design/frontend-design.md** — apply its principles for distinctive, production-grade frontend (typography, theme, motion, backgrounds) as the final pass over DESIGN.md.

`docs/DESIGN.md` must contain: register + aesthetic lane (named reference), color palette table (name/hex/role), font pairing + scale, spacing/layout system, component inventory with states, motion language (durations/easings/reduced-motion), page-by-page composition notes, and an explicit "banned on this project" list (from the bans + anything user rejected).

Also honor the user's Round-4 discovery answers (adjectives, reference products, dark/light). GATE: user approves DESIGN.md.

## Phase 7 — High-fidelity mockups (Haiku builds, Sonnet reviews, user sees it)

Purpose: user sees and approves how every page actually LOOKS — real colors, typography, spacing, corner radii, shadows — before real frontend work. These are static previews of the final design, not the final code.

### Mockup rules
- Location: `wireframe/` — one `<page>.html` per page in the PRD's user flows, plus `wireframe/tokens.css` shared.
- **Implements DESIGN.md faithfully**: `tokens.css` carries the design system as CSS variables (palette hex values, font pairing loaded via Google Fonts `<link>`, spacing scale, corner radii, shadows, motion durations as comments). Every page consumes the tokens — no hard-coded one-off values.
- Real look: actual colors on actual components, real fonts, real border-radius, real elevation. Buttons/cards/inputs styled per DESIGN.md's component inventory with hover/focus states in CSS.
- Real structure: working nav links between pages, real headings/copy hierarchy (draft copy OK, no lorem ipsum), every DESIGN.md component present, every PRD flow walkable page-to-page.
- **Still static**: HTML+CSS only, no JS beyond trivial nav. Images: verified stock URLs (per the impeccable imagery rules — verify they resolve) or neutral placeholder blocks styled with the design's surface tokens; never broken links.
- Every feature's states get mocked: each page shows its default state, plus a `<page>-states.html` strip showing empty / loading / error variants — styled per DESIGN.md.
- Run the impeccable Absolute Bans over the mockups (gradient text, eyebrow kickers, identical card grids…) — catching a ban here is 10x cheaper than in Phase 8.

### Loop
1. **Dispatch Haiku coder** (references/agents.md template; task = mockup set, spec = PRD flows + full DESIGN.md + rules above).
2. **Dispatch Sonnet reviewer** with rubric:
   - Every PRD §4 flow walkable by clicking through the pages?
   - Every P0 feature's UI represented, with all its states?
   - **DESIGN.md fidelity**: palette hex values, fonts, spacing scale, corner radii, shadows all match the tokens — any deviation or hard-coded off-token value = FAIL?
   - Layout follows DESIGN.md composition notes?
   - No impeccable Absolute Ban present (= FAIL)?
   - Nothing present that PRD marks as non-goal?
   - Static rule respected (no app logic in JS)?
3. Fix loop per agents.md (max 3 rounds).
4. **Show the user**: serve the folder (preview server or `Start-Process wireframe\index.html`) and name each page + which flow it covers. GATE: user clicks through and approves / requests changes (changes → back to step 1 with a delta task). Visual changes the user requests here get written BACK into DESIGN.md so the two never diverge.

Approved mockups become the structural AND visual contract for Phase 8 frontend tasks: same tokens.css seeds the real project's design tokens.

Keep the mockups mechanically convertible — Phase 7.5 (`references/html-to-react.md`) turns them into
React/Next components by script, and it pays off in proportion to how regular they are:
- **Repeated blocks must be structurally identical** (same tags, same class lists, same child order).
  Vary only text and attribute values between instances. A card that drops an `<svg>` in one instance
  breaks the repeat group and forces a hand-written component.
- Same header/footer markup byte-for-byte on every page.
- Semantic tags and stable class names; no inline `style=` unless the value genuinely varies per instance.
- Cross-page nav via plain `<a href="page.html">` — those become routes automatically.
- No JS beyond trivial nav (it gets dropped on conversion anyway).
