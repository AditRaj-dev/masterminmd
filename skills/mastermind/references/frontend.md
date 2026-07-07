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

## Phase 7 — Wireframe (Haiku builds, Sonnet reviews, user sees it)

Purpose: user sees and approves the structure of every page BEFORE real frontend work. Deliberately unstyled — structure, not beauty.

### Wireframe rules
- Location: `wireframe/` — one `<page>.html` per page in the PRD's user flows, plus `wireframe/wf.css` shared.
- **Grayscale only**: white/black/3 grays. System font. No brand colors, no images (gray placeholder boxes labeled "IMG: hero photo"), no icons (text labels), no JS beyond trivial nav.
- Real structure: actual nav with working links between wireframe pages, real headings/copy hierarchy (draft copy OK, no lorem ipsum), every component from DESIGN.md's inventory present as a labeled box, every PRD flow walkable page-to-page.
- Every feature's states get wireframed: each page shows its default state, plus a `<page>-states.html` strip showing empty / loading / error variants.

### Loop
1. **Dispatch Haiku coder** (references/agents.md template; task = wireframe set, spec = PRD flows + DESIGN.md component inventory + rules above).
2. **Dispatch Sonnet reviewer** with rubric:
   - Every PRD §4 flow walkable by clicking through the pages?
   - Every P0 feature's UI represented, with all its states?
   - Layout follows DESIGN.md composition notes?
   - Nothing present that PRD marks as non-goal?
   - Grayscale/no-styling rules respected (a styled wireframe = FAIL — it anchors the user on wrong visuals)?
3. Fix loop per agents.md (max 3 rounds).
4. **Show the user**: serve the folder (preview server or `Start-Process wireframe\index.html`) and name each page + which flow it covers. GATE: user clicks through and approves / requests changes (changes → back to step 1 with a delta task).

Approved wireframes become the structural contract for Phase 8 frontend tasks.
