# Session handoff — one phase per session

Mastermind runs long. A single session that carries Phase 1 through Phase 9 drags every
transcript byte of discovery into the build, and the context window is spent on
conversation nobody needs anymore. So: **each phase runs in its own fresh session**, and
the only thing that crosses the boundary is written state.

`/compact` is not a substitute. Compaction summarizes lossily and keeps the compacted blob
in context forever; a new session starts at zero and reads a doc you controlled the
contents of.

## The rule

After a phase's **GATE is approved**, do not start the next phase. Instead:

1. Update `docs/memory/MEMORY.md` (append) and `docs/memory/HANDOFF.md` (rewrite) — the
   HANDOFF is the whole handoff, see §Frozen facts below.
2. Write `docs/memory/RESUME.md` from the template below.
3. Mirror it into memex so the next session (or another provider) can pull it without the
   file: `memex handoff create` with the resume text, project name, and phase tag. Also
   `memex remember` any decision made at the gate — and at the **Phase 7 gate specifically**,
   one `memex remember` per mockup page (route · PRD flow · states · components) from
   `wireframe/INDEX.md`. If memex is unavailable, skip it — the files are the source of truth,
   memex is the convenience copy.
4. Copy the resume prompt to the clipboard and tell the user to paste it into a new
   session:

   ```bash
   Get-Content docs/memory/RESUME.md -Raw | Set-Clipboard
   ```

   Offer the alternative one-liner too — `claude "$(Get-Content docs/memory/RESUME.md -Raw)"`
   in a new terminal — but never spawn it yourself; opening the session is the user's move.
5. Stop. End your turn. Do not begin the next phase in this session even if the user says
   "continue" — if they do, tell them once that the point is the fresh window, and if they
   repeat it, comply and continue here.

Phase 8 is too long for one session as well. Break it at every **parallel group boundary**
or every ~5 accepted tasks, whichever comes first, using the same procedure with the group
id in place of the phase.

Phase 0 → 1 and Phase 7 → 7.5 have no gate; they stay in the same session.

## docs/memory/RESUME.md template

Written by the ending session, pasted by the user into the starting one. It is a prompt,
not a report — it addresses the next session directly.

```markdown
/mastermind continue

Project: <name> — <one-line what it is>
Working dir: <abs path>
Branch: <branch>
Last completed: Phase <n> — <name>, approved by the user on <date>.
You are starting: Phase <n+1> — <name>.

Read exactly these, in this order, and nothing else before you start:
1. docs/memory/HANDOFF.md
2. docs/memory/MEMORY.md
3. <phase-specific docs — from the read-set table, absolute list>
4. ~/.claude/skills/mastermind/<the phase's reference>

Do not re-read documents from earlier phases; whatever mattered from them is in
HANDOFF.md §Frozen facts. If something you need is genuinely missing there, read the one
doc that has it and then add the fact to Frozen facts so the next session doesn't repeat
the read.

Open questions the user still owes you: <list, or "none">
First action: <one concrete thing>
```

## Read-set table

Per phase, the complete list of what the **orchestrator** reads. Everything not listed is
off-limits without a stated reason. Agents read their own task's docs — the orchestrator
does not read them on the agents' behalf.

| Starting phase | Reads (after HANDOFF + MEMORY) | Never reads |
|---|---|---|
| 1 discovery | `references/discovery.md` | project source |
| 2 PRD | `docs/DISCOVERY.md`, `references/documents.md` §2 | — |
| 3 features | `docs/PRD.md`, `references/documents.md` §3 | DISCOVERY (PRD supersedes it) |
| 4 plan | `docs/PRD.md`, `docs/features/*.md`, `references/documents.md` §4 | DISCOVERY |
| 5 API record | `docs/IMPLEMENTATION_PLAN.md`, dependency manifest + installed types, `references/api-record.md` | feature docs, PRD |
| 6 design | `docs/PRD.md` (personas + flows only), `references/frontend.md` §6, the four `references/design/*.md` | feature docs, plan |
| 7 mockups | `docs/DESIGN.md`, `docs/PRD.md` §flows, `wireframe/INDEX.md`, `references/frontend.md` §7 | the mockup HTML itself (only the reviewer agent reads it) |
| 7.5 h2r | `references/html-to-react.md`, `.h2r/manifest.md`, `wireframe/INDEX.md` | mockup HTML, emitted `.tsx` |
| 8 build | `docs/IMPLEMENTATION_PLAN.md`, `docs/API_RECORD.md`, `wireframe/INDEX.md` (frontend tasks), `references/agents.md`, `references/git-workflow.md` | feature docs (coder reads them), source files (review is a diff, by an agent), mockup HTML (frozen) |
| 9 wrap | `docs/PRD.md` §8, `docs/IMPLEMENTATION_PLAN.md`, `references/git-workflow.md` | source files |

Symbol lookups during Phase 8 go through the code graph (`references/code-graph.md`), never
through opening files to look around.

## Frozen facts — why the next session doesn't re-read

`HANDOFF.md` carries a `## Frozen facts` section: the small set of things that agents
otherwise rediscover by opening files. Every time you find yourself reading a file to
answer a question you already answered once, the answer belongs here.

What lives there: stack + exact versions, package manager, run/build/test commands,
directory layout (top two levels), where the design tokens live and their names, the
component inventory after 7.5, external services + env var names, and the decisions that
are locked (with a one-line why). Keep it factual and short — it is a lookup table, not a
narrative. See `references/memory.md` for the full HANDOFF format.
