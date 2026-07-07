# Memory docs — cheap agent handoff

Two files in `docs/memory/`. Any agent (or a future session) reads these two files and has full working context without replaying the conversation.

## docs/memory/MEMORY.md — append-only log

Never rewrite or delete entries; append. Entry types:

```markdown
# Memory — <project name>

## Entries
- [P1/discovery] DECISION: chose Postgres over SQLite → user expects multi-user concurrent writes
- [T03] MISTAKE: assumed `zod.parse` returns `{success}` — it throws; `safeParse` returns the union → RESOLVED: API_RECORD.md updated, T03 refixed
- [T05] GOTCHA: Vite proxies /api only in dev; prod needs the express static mount → documented in README
- [P7/wireframe] REVIEW: sonnet flagged missing empty state on notes list twice → added "check empty states" to coder prompt template for remaining tasks
```

Format: `- [phase-or-task] TYPE: what → why/how resolved`. Types: `DECISION`, `MISTAKE`, `GOTCHA`, `REVIEW` (recurring review finding worth pre-empting).

Write triggers (orchestrator):
- A Sonnet review fails a task → log the MISTAKE and its resolution once fixed.
- Any decision that changes a doc after its gate → DECISION entry.
- Any surprise about a tool/library/environment → GOTCHA.
- Same review finding appears twice → REVIEW entry + amend future coder prompts.

## docs/memory/HANDOFF.md — overwritten snapshot

Rewritten (not appended) after every completed task and every phase gate:

```markdown
# Handoff — <project name>
Updated: <date time>

## Where we are
Phase: <n> — <name> · Gate status: <awaiting user | approved>

## Task board
Done: T01, T02 · In review: T03 · Next up: T04 (parallel group B: T04+T05)

## Read before doing anything
1. docs/memory/MEMORY.md (mistakes & decisions)
2. docs/IMPLEMENTATION_PLAN.md (current statuses)
3. Your task's feature doc
4. docs/API_RECORD.md

## Immediate next step
<one concrete action>

## Known landmines
<top 3 gotchas from MEMORY.md that affect upcoming tasks>
```

## Agent contract

Every dispatched agent prompt begins with: *"Read docs/memory/MEMORY.md and docs/memory/HANDOFF.md first."* Every agent's final report must include a `MEMORY:` section listing zero or more candidate entries; the orchestrator curates and appends them (agents never write the memory files directly — prevents append collisions from parallel agents).
