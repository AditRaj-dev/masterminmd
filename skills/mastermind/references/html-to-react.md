# Phase 7.5 — Mockup → React/Next conversion (h2r pipeline)

Purpose: turn the **approved** `wireframe/*.html` into modular React/Next components without you
retyping a single line of markup. The script does everything mechanical; you do only the part that
needs judgment — deciding what a component *is*, what it's called, and what its props are.

Token math: for a 10-page mockup set (~6k lines of HTML), hand-writing the TSX costs ~40–60k output
tokens. This pipeline costs one ~300-line manifest read + one ~80-line plan write. The markup itself
is never in your context.

Script: `~/.claude/skills/mastermind/scripts/h2r.py` (stdlib Python 3.8+, no deps).

## Hard rules

- **Never read the wireframe HTML files.** Read `.h2r/manifest.md` instead. If you catch yourself
  opening a `.html`, stop — the manifest has what you need, and if it doesn't, re-run extract with
  `--depth 6`.
- **Never write .tsx for a page or a repeated block by hand.** The script emits it verbatim from the
  approved HTML, which is also what guarantees visual fidelity. Hand-typing = drift from the contract
  the user approved at the Phase 7 gate.
- Only run this **after** the Phase 7 gate. Converting unapproved mockups wastes the whole point.
- Emitted code is a starting point for markup and styling only. Interactivity, data, and state are
  Phase 8 tasks against the emitted files.

## Step 1 — extract

```bash
python "C:\Users\study\.claude\skills\mastermind\scripts\h2r.py" extract wireframe --out .h2r
```

Produces `.h2r/manifest.md`:

- **assets** — css files, `tokens.css` variable list, remote head `<link>`s (fonts), script count.
- **repeat groups** — every subtree that appears 2+ times anywhere in the mockup set, keyed `R1, R2…`,
  with: how many instances, where they are, and — this is the useful part — **`varies:`**, the exact
  paths whose text/attributes differ between instances, with sample values. Those are your props,
  pre-computed. Paths that don't vary are static and need no prop.
- **page outlines** — depth-limited element trees with child-index paths, repeat roots marked `<= R1`.

Read it once. Everything you need to design the component tree is in it.

## Step 2 — plan (this is the only thing you write)

Write `.h2r/plan.json`. Schema in `.h2r/plan.schema.json`.

```json
{
  "framework": "next",
  "wireframe": "wireframe",
  "outDir": ".",
  "componentsDir": "components",
  "layout": true,
  "components": [
    { "name": "Card", "repeat": "R1",
      "props": [
        { "name": "title", "path": "/3/0" },
        { "name": "body",  "path": "/5/0" },
        { "name": "href",  "path": "/7@href" },
        { "name": "children", "path": "/5", "kind": "children" }
      ] },
    { "name": "SiteHeader", "repeat": "R2" },
    { "name": "Hero", "source": "index:/3/1", "client": true }
  ],
  "pages": [
    { "src": "index.html",   "route": "/",        "name": "Home" },
    { "src": "pricing.html", "route": "/pricing", "name": "Pricing" }
  ]
}
```

Field notes:
- `repeat: "R1"` — component from a repeat group; **all** its instances across all pages become call
  sites automatically, with per-instance prop values extracted from the HTML. You never type the copy.
- `source: "page:/3/1"` — one-off component (a hero, a distinctive section) that appears once.
- `props[].path` — relative to the component root, straight from the manifest's `varies:` list.
  `/3/0` = a text node → `string` prop. `/7@href` = an attribute → `string` prop.
  `kind: "children"` = that subtree becomes a `ReactNode` slot.
- `client: true` — emits `'use client'`. Set it for anything that will need state/handlers in Phase 8.
- Omit `props` entirely for chrome that's identical everywhere (header, footer).

### Your judgment, applied here (the part no script can do)

- **Name by role, not by shape.** `PricingTier`, not `Card2`. Names outlive the markup.
- **Don't componentize everything.** A repeat group of 2 trivial nodes is noise — inline it. Rule of
  thumb: 3+ instances, or 2 instances that are conceptually one thing (header/footer).
- **Split a group when the concepts differ.** If R1's instances are feature cards on one page and
  pricing tiers on another, that's two components sharing markup — emit two (`repeat` twice with
  different names is allowed only if you also narrow with `source`; otherwise emit one and split by
  hand later, and say so).
- **Props vs children.** Plain text → prop. Rich/variable inner markup → `children` slot.
- **Server by default.** Only mark `client` where Phase 8 will actually attach interactivity.
- **Layout chrome goes in `layout.tsx`,** not on every page: if `SiteHeader`/`SiteFooter` wrap every
  page, emit them, then move the two call sites into `app/layout.tsx` after emit (a 3-line edit).

## Step 3 — emit

```bash
python "C:\Users\study\.claude\skills\mastermind\scripts\h2r.py" emit --plan .h2r/plan.json --dry
```

`--dry` lists the files first. Then drop `--dry`.

What the script handles so you don't: `class`→`className`, `for`→`htmlFor`, all SVG attribute/tag
casing, void self-closing, `style=""`→ style object (with a `React.CSSProperties` cast when CSS custom
properties are present), `{}` escaping, comments→`{/* */}`, `<script>` dropped, inline `onclick`
dropped, `*.html` links rewritten to routes (and to `next/link` in Next), css copied to
`app/styles/` + imported in `layout.tsx`, remote font `<link>`s preserved in the layout head,
`<title>`→ per-page `metadata`, component imports per page.

Output for `framework: "next"`: `app/page.tsx`, `app/<route>/page.tsx`, `app/layout.tsx`,
`components/*.tsx`, `app/styles/*.css`.
For `framework: "react"`: `src/pages/<Name>.tsx`, `components/*.tsx`, `src/styles/*.css` +
`src/styles.ts` to import from your entry (you wire the router yourself — a few lines).

## Step 4 — verify

```bash
python "C:\Users\study\.claude\skills\mastermind\scripts\h2r.py" verify .
```

Structural lint only (leftover `class=`, `for=`, inline handlers, `<script>`, unbalanced
braces/parens). It is **not** a typecheck. Follow it with the real thing and paste the output:
`npx tsc --noEmit` or `npm run build`. Per the evidence rule, no "converted" claim without that.

Then eyeball one page side-by-side with its mockup in the browser. Any visual drift is a bug in the
plan (usually a prop path pointing at the wrong node), not something to patch by hand in the TSX —
fix the plan and re-emit.

## Re-emitting

Emit is idempotent and overwrites. If the user changes a mockup after conversion: update the HTML,
re-run extract (group ids can shift — re-read the `repeat groups` section), fix the plan, re-emit.
Once Phase 8 has added logic to the emitted files, re-emitting **destroys it** — from that point,
emit to a scratch `outDir` and diff instead.

## Where this sits in the pipeline

Phase 7 gate (user approves mockups) → **Phase 7.5 (this)** → Phase 8 tasks now start from real
components instead of empty files. Update `docs/IMPLEMENTATION_PLAN.md`: frontend tasks change from
"build page X" to "wire page X" (data, state, handlers, a11y). Record the component inventory in
`docs/memory/HANDOFF.md` so coder agents import instead of re-creating.
