# Phases 2–4 — Document templates

All documents are written by the orchestrator, in full detailed prose (caveman terseness applies to chat, NOT to these deliverables). Each ends with a user gate.

## Phase 2 — docs/PRD.md

```markdown
# PRD — <project name>
Version: 1.0 · Date · Status: draft | approved
Source: docs/DISCOVERY.md

## 1. Overview
Problem statement, product vision, target outcome.

## 2. Users & personas
For each persona: who, goals, pain points, technical level.

## 3. Feature list (prioritized)
| # | Feature | Priority (P0/P1/P2) | Depends on | Feature doc |
|---|---------|--------------------|-----------|-------------|
P0 = v1 blocker, P1 = v1 nice, P2 = later.

## 4. User flows
For each core flow: numbered steps from entry to success, including decision branches and error exits. Mermaid flowcharts welcome.

## 5. Data model
Every entity: fields, types, relations, constraints, indexes worth noting.

## 6. Non-functional requirements
Performance, scale, security, accessibility (WCAG AA), browser/device support.

## 7. Non-goals
Explicitly out of scope for v1, so agents don't build them.

## 8. Acceptance criteria
Per P0 feature: measurable "done" statements a reviewer can check.

## 9. Open questions
Anything DEFERRED(user) from discovery.
```

## Phase 3 — docs/features/<nn>-<slug>.md (one per feature)

Numbers match the PRD feature list. Each file must be detailed enough that a Haiku agent can implement from it WITHOUT reading the whole PRD.

```markdown
# Feature <nn>: <name>
Status: specced | building | reviewed | done · PRD ref: §3.<nn>

## What it does
2–4 sentences, user-visible behavior.

## How it works (exact behavior)
Step-by-step mechanics. Every button, every transition, every rule.
Include: validation rules with exact limits, sort/filter defaults, pagination sizes, debounce timings — real numbers, not "reasonable".

## Inputs & outputs
| Input | Type | Validation | Error message shown |
Outputs / side effects: what's persisted, emitted, displayed.

## States
- Empty: <exact copy + visual>
- Loading: <skeleton/spinner spec>
- Error: <per error type: message + recovery action>
- Success: <feedback shown>

## Edge cases
Bulleted, each with expected behavior (from DISCOVERY.md).

## Data
Entities touched, fields read/written, queries needed.

## API surface
Endpoints / functions this feature needs — MUST exist in docs/API_RECORD.md before build.

## Dependencies
Features that must exist first; features that consume this one.

## Acceptance checklist
- [ ] <testable statement>
```

## Phase 4 — docs/IMPLEMENTATION_PLAN.md

```markdown
# Implementation plan — <project name>
Status: draft | approved | executing · Progress: <n>/<total> tasks

## Build order rationale
Why this sequence (dependencies, risk-first, walking skeleton).

## Tasks
### T01 — <title>
- Feature: docs/features/<nn>-<slug>.md
- Files: <paths to create/modify>
- Model: haiku (coder) → sonnet (reviewer)   [orchestrator handles integration-only tasks itself]
- Depends on: <task ids or none>
- Parallel group: <letter — tasks in the same letter can run simultaneously>
- Review criteria: <what the sonnet reviewer specifically checks, beyond the standard rubric>
- Status: [ ] pending / [~] building / [r] in review / [x] done

### T02 — ...
```

Rules:
- Every task small enough for one Haiku agent: one feature slice, ≤ ~5 files, one review round expected.
- First tasks = walking skeleton (project scaffold, DB schema, one end-to-end slice) so integration risk dies early.
- Wireframe-approved HTML (Phase 7) is listed as input to frontend tasks.
- Orchestrator updates Status + Progress after every task, and mirrors into docs/memory/HANDOFF.md.
