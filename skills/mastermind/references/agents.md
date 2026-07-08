# Agent dispatch — Haiku codes, Sonnet reviews, orchestrator integrates

Mechanism: the `Agent` tool with `model: "haiku"` (coders) or `model: "sonnet"` (reviewers), `subagent_type: "general-purpose"`. The orchestrator NEVER writes production code itself — it discusses, documents, dispatches, verifies, integrates.

## Pre-flight plan review (once, before dispatching task 1)

Scan the whole plan for: tasks that contradict each other or the API record, tasks the review rubric would auto-fail (e.g. mandated unlisted APIs), and anything ambiguous enough to sink a Haiku agent. Batch ALL findings into one AskUserQuestion before execution begins — never one interrupt per discovery mid-build. Clean scan → start without comment.

## Dispatch rules

- One task (from docs/IMPLEMENTATION_PLAN.md) = one Haiku agent. Same parallel group + no shared files → dispatch in parallel (multiple Agent calls in one message).
- Every deliverable gets a Sonnet review before its task is marked done. No exceptions, including wireframes.
- **Review the diff, not the tree**: after a coder finishes, write the task's diff to a file (`git diff <before>..HEAD > docs/memory/reviews/T<id>.diff`) and point the reviewer at it plus the feature doc — cheaper context, sharper review.
- **Verification iron law (both templates carry it)**: no completion claim without fresh command output in the same report. "Should work", "probably passes", a previous run, or an agent's own success claim are not evidence — the command output is. This applies to the orchestrator too: verify agent reports independently (run the build/test yourself or check the diff) before marking a task done.
- Git: commit after every accepted task (`T<id>: <title>`); parallel-group isolation via worktrees when file overlap is possible — see `references/git-workflow.md`.
- Fix loop: Sonnet fails it → re-dispatch to a Haiku agent with the findings (use SendMessage to the same coder agent when its context helps; fresh agent when it's confused). Max 3 rounds; still failing → orchestrator diagnoses the root cause itself and either rewrites the task, splits it, or fixes the few offending lines directly (log a MEMORY entry either way).
- After each accepted task: update plan status, run incremental graph update, append MEMORY entries, rewrite HANDOFF.md.

## Haiku coder prompt template

```
You are a coder agent on project <name>, working dir <path>.

FIRST: read docs/memory/MEMORY.md and docs/memory/HANDOFF.md.

TASK <id>: <title>
Implement exactly what docs/features/<nn>-<slug>.md specifies — read it in full.
Files to create/modify: <paths>. Do not touch other files.

API RULE: Only call APIs listed in docs/API_RECORD.md (read the sections for <relevant packages/modules>). Need an unlisted API? DO NOT guess or improvise — stop, note it in your report under BLOCKED, and finish what you can without it.

CODE NAVIGATION: <graph available? "Query the code graph MCP tools to locate symbols" : "Use Grep with tight symbol patterns">. Read only the line ranges you need. Never read whole large files to orient yourself.

<paste style-rules.md STYLE BLOCK>

DESIGN (frontend tasks only): follow docs/DESIGN.md tokens/components exactly; the approved mockup wireframe/<page>.html is the structural + visual contract — reuse its tokens.css values as the project's design tokens.

VERIFY before reporting: <task-specific check — run build, run the test, open the page>. Report what you ran and its actual output.

REPORT FORMAT:
- DONE: files changed + one line each
- VERIFIED: command run + result
- BLOCKED: unlisted APIs or missing info (empty if none)
- MEMORY: candidate entries `[T<id>] TYPE: what → resolution` (empty if none)
```

## Sonnet reviewer prompt template

```
You are a review agent on project <name>, working dir <path>. Review task <id> just implemented by a coder agent.

FIRST: read docs/memory/MEMORY.md, docs/features/<nn>-<slug>.md, and the changed files: <paths>.

CHECK, in order:
1. SPEC: does the implementation do exactly what the feature doc says? Every acceptance-checklist item, every state (empty/loading/error/success), every edge case listed.
2. API: every external/internal API call in the diff exists in docs/API_RECORD.md with a matching signature. Unlisted or mismatched call = automatic FAIL.
3. TASK CRITERIA: <review criteria from the plan task>.
4. QUALITY: correctness bugs, security at trust boundaries, data-loss risks. Style-only nitpicks are NOT findings.
5. (frontend tasks) DESIGN: matches docs/DESIGN.md + approved wireframe; run the audit rubric in references/design/impeccable.md §Audit; any Absolute Ban present = FAIL.

Do not fix anything. Do not invent findings to look thorough — a clean PASS is a valid outcome.

<paste style-rules.md STYLE BLOCK — communication part>

REPORT FORMAT:
- VERDICT: PASS | FAIL
- FINDINGS: numbered, each with file:line, what's wrong, why it matters, concrete fix (empty on PASS)
- MEMORY: candidate entries (recurring patterns worth pre-empting)
```

## Escalation & sizing

- A task that comes back BLOCKED on APIs: orchestrator verifies + records the API (references/api-record.md procedure), then re-dispatches.
- A task failing review twice on the same finding: the feature doc is probably ambiguous — orchestrator fixes the DOC first, logs REVIEW memory entry, then re-dispatches.
- A task too big for Haiku (agent flounders, touches >5 files, review finds architectural problems): split it in the plan; never "just let Sonnet code it" without updating the plan — model assignments live in the plan, not in improvisation.

## Systematic debugging (when the 3-round fix loop exhausts)

NO FIXES WITHOUT ROOT CAUSE FIRST. When agents have shotgun-patched three times, the orchestrator stops dispatching and investigates:

1. **Read the actual error** completely — stack trace, line numbers, exit codes. It often contains the answer.
2. **Reproduce reliably** — exact command, exact steps. Not reproducible → gather more data, don't guess.
3. **Check recent changes** — `git diff` since the last green commit (per-task commits make this cheap).
4. **Multi-component failures**: instrument each boundary (log what enters/exits each layer), run once, find WHERE it breaks, then investigate that component only.
5. **Trace the bad value to its source** — fix at the source, never at the symptom.
6. Form ONE hypothesis, make the smallest change that tests it, verify with the reproduction. Then either fix the task doc + re-dispatch, or fix the offending lines directly. Log MISTAKE entry.

## Final whole-branch review (end of Phase 8, before Phase 9)

Per-task reviews miss cross-task problems. When the last task is accepted, dispatch one Sonnet reviewer over the full branch diff (`git diff <base>...HEAD`) with the PRD acceptance criteria + API record: integration seams, duplicated logic across tasks, drifted conventions, unfinished TODOs. Findings become fix tasks; then Phase 9.
