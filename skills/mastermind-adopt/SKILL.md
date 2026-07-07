---
name: mastermind-adopt
description: Use when the user wants to onboard an EXISTING / ongoing project into the mastermind workflow - scans the codebase, maps its initial state into a report, hunts for existing PRDs/specs and asks whether to adopt them, otherwise runs the full mastermind discovery interview. Triggers - "adopt this project", "map this project", "onboard existing project", "mastermind adopt", "analyze this codebase and plan". Not for greenfield projects (use mastermind directly) or quick code questions.
argument-hint: "[project path — defaults to cwd]"
user-invocable: true
---

# Mastermind Adopt — onboard an existing project

You are the orchestrator (top-tier model). Goal: take an ongoing project from "unknown pile of code" to "mastermind-ready" — initial-state report, adopted or freshly-built PRD, memory docs — so `/mastermind continue` can take over.

Shared rules from the mastermind skill apply (read `C:\Users\study\.claude\skills\mastermind\SKILL.md` §Non-negotiables): gates via AskUserQuestion, memory docs, evidence before claims, caveman chat / detailed deliverable docs.

## Phase A — Scan the project

Scope: the path given as argument, else the current working directory. **No git repo?** Skip steps 7's git commands and CODE_STATE's git sections (mark them "no git history"), still do stop-point detection from code markers — and flag "no version control" as a top risk.

Map the initial state. Orchestrator does this itself (dispatch one Explore/Haiku agent only if the repo is huge):

1. **Stack**: read manifest files (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `*.csproj`, `composer.json`…) — languages, frameworks, key dependencies + versions, scripts (build/test/dev commands).
2. **Structure**: directory tree (2–3 levels, ignore node_modules/dist/.git), entry points, config files.
3. **Code graph**: build it per `C:\Users\study\.claude\skills\mastermind\references\code-graph.md` (full build). Use its stats (files, nodes, languages) in the report; use graph queries instead of whole-file reads throughout.
4. **Features detected**: infer from routes/pages/screens, API endpoints, DB models/migrations, background jobs. List them as a feature census draft.
5. **Health**: does it build? do tests exist and pass (run them)? git state (branch, dirty files, last commits). Report actual command output, not guesses.
6. **Docs hunt**: Glob for existing product docs — `README*`, `docs/**`, `*.prd*`, `PRD*`, `SPEC*`, `spec/**`, `requirements*`, `ROADMAP*`, `DESIGN*`, `ARCHITECTURE*`, `.notion/`, wiki folders. Skim each hit: is it a real requirements/PRD-like doc or just boilerplate?
7. **Git archaeology** (what work was already done):
   - `git log --oneline --date=short --pretty="%h %ad %s" -50` + `git log --stat -10` — recent work, what files each commit touched.
   - `git shortlog -sn` (who), `git branch -a -v` (parallel efforts, unmerged branches), `git stash list`, `git status` (uncommitted work in flight).
   - Group the history into work streams ("auth built over commits a1b2..c3d4", "payment started, last touched 3 weeks ago") — commits are evidence of intent, not just changes.
   - Unmerged branches + stashes + dirty files = work someone stopped mid-flight; flag each.
8. **Stop-point detection** (where did coding stop):
   - Grep the source for unfinished-work markers: `TODO`, `FIXME`, `HACK`, `XXX`, `WIP`, `@ts-ignore`, `NotImplemented`, `unimplemented!`, "not implemented" throws, stub bodies. Each hit located (file:line) and classified.
   - Cross-check feature census: routes defined but handlers stubbed, models without UI, UI without backend, tests skipped (`skip|todo|only`), empty catch blocks.
   - Compare the last 5 commits' touched files against test/build results — did the work stop green or mid-break?

## Phase B — State reports → `docs/INITIAL_STATE.md` + `docs/CODE_STATE.md`

Write both reports (full detailed prose — they're deliverables):

```markdown
# Initial state — <project>
Date · Commit: <sha> · Branch: <name>

## Stack
Languages, frameworks, key deps + versions, build/test/dev commands.

## Structure
Annotated tree: what lives where, entry points.

## Detected features (census draft)
| # | Feature | Evidence (files/routes) | Apparent completeness |

## Health
Build: <ran command → result> · Tests: <ran → n pass/fail> · Graph: <nodes/files> · Git: <state>

## Existing product docs found
| Path | Looks like | Verdict (PRD-candidate / reference-only / boilerplate) |

## Risks & unknowns
Dead code suspicions, undocumented areas, failing tests, version hazards.
```

Also write `docs/CODE_STATE.md` — where the coding process stopped:

```markdown
# Code state — <project>
Date · Commit: <sha> · Branch: <name>

## Work history (from git)
Work streams grouped from the log:
| Stream | Commits | Period | State |
|--------|---------|--------|-------|
| Auth | a1b2f..c3d4e (6) | 2026-05-01..05-12 | complete, tests green |
| Payments | e5f6a..91b2c (3) | 2026-06-10..06-14 | stopped mid-flight |

## Stopped-at snapshot
- Last commit: <sha> "<msg>" (<date>) — <stopped green | mid-break: what's failing>
- Uncommitted changes: <files + what they appear to be doing, or none>
- Stashes: <list + gist, or none>
- Unmerged branches: <branch → what it contains → merge-ready?>

## Unfinished work inventory
| Where (file:line) | Marker | What's missing | Blocking? |
|-------------------|--------|----------------|-----------|
TODOs/FIXMEs/stubs/skipped tests, each classified.

## Per-feature completeness
| Feature | Backend | Frontend | Tests | Wired end-to-end? | Verdict |

## Resume points
Ordered list: the most likely "next tasks" the previous work implies.
```

Present a summary of both docs. **GATE**: user confirms the map is accurate (corrections → update reports).

## Phase C — PRD: adopt or discover

**If PRD-candidate docs were found:** show them (path + 3-line gist each) and ask via AskUserQuestion: "Is this the PRD/spec you actually work from?"

- **Adopts one** → copy/consolidate it into `docs/PRD.md` (mastermind format, `C:\Users\study\.claude\skills\mastermind\references\documents.md` §Phase 2). Then run a **gap check**: walk the discovery drill-down checklist (`C:\Users\study\.claude\skills\mastermind\references\discovery.md` Round 3) against it; anything the adopted PRD doesn't answer becomes a short targeted interview — only the gaps, not the full process. Record the gap answers in `docs/DISCOVERY.md` (marked "gap-fill for adopted PRD") so downstream feature docs have a source. **GATE** on the resulting PRD.
- **Refuses / none found / all boilerplate** → run the FULL mastermind discovery process: read `C:\Users\study\.claude\skills\mastermind\references\discovery.md` and execute it exactly (feature census seeded from Phase A's detected features — confirm/extend it rather than starting blind), then write the PRD per documents.md. **GATE** each per mastermind rules.

## Phase D — Handoff to mastermind

1. Create `docs/features/`, `docs/memory/` if missing; write initial `MEMORY.md` (seed with GOTCHA entries from Phase A findings — failing tests, version hazards, mid-flight work) and `HANDOFF.md` (phase: mastermind Phase 3 — feature docs; next step = top entry from CODE_STATE.md §Resume points; landmines = its blocking unfinished-work items).
2. Git (repo exists): ask once at the Phase B gate — commit the docs on the current branch, or create `mastermind/<slug>` first (per `C:\Users\study\.claude\skills\mastermind\references\git-workflow.md`) if build work follows. Never commit onto a dirty tree silently — the user's uncommitted work from CODE_STATE.md gets stashed/committed only with their OK. Then commit: `docs: project adopted into mastermind workflow`.
3. Tell the user: state mapped, PRD in place — run `/mastermind continue` to proceed with feature docs → plan → API record → design → build.
