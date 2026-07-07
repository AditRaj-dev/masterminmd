# Phase 1 — Discovery interview protocol

Goal: extract EVERY intricate detail of how each feature works before a single document is written. The orchestrator (top-tier model) runs this personally. Output: `docs/DISCOVERY.md`.

## Rules

- One topic at a time. Never fire a wall of 10 questions; ask 1–3 focused questions per turn (AskUserQuestion or plain conversation), digest the answer, then drill deeper.
- Never assume. If the user says "users can share notes," you do not know: with whom, via what mechanism, with what permissions, what happens on revoke, what the recipient sees. Ask.
- Offer opinions. You are the senior architect: when the user is unsure, propose a concrete default and get sign-off ("Most apps do X; I recommend that here because Y — OK?").
- Write as you go. Append confirmed answers to `docs/DISCOVERY.md` incrementally so nothing is lost if the session dies.

## Interview sequence

### Round 1 — The big picture
1. What is this product, in one sentence? Who uses it?
2. What problem does it solve that existing tools don't?
3. Platform: web / mobile / desktop? What stack preference, if any?
4. What does v1 absolutely need vs what can wait?

### Round 2 — Feature census
List every feature the user mentions plus features they implied but didn't name (auth, settings, onboarding, search, notifications, admin, billing, data export). Confirm the list. Number the features. This numbered list drives Phase 3.

### Round 3 — Per-feature drill-down (repeat for EVERY feature)
For each feature, cover the full checklist before moving to the next:

- **Happy path**: step-by-step, what does the user do, what does the system do?
- **Inputs**: what data enters? Validation rules? Limits (length, size, count)?
- **Outputs / side effects**: what is created, updated, sent, shown?
- **States**: empty state (first use), loading state, error state, success state, partial state.
- **Edge cases**: concurrency (two users edit at once?), duplicates, deletes (soft or hard? cascade?), offline, huge inputs, zero inputs.
- **Permissions**: who can see/do this? Anonymous? Roles?
- **Data lifecycle**: where is it stored, how long, can the user export/delete it?
- **Integrations**: does this touch an external service (payments, email, storage, AI)? Which one exactly?
- **Failure modes**: external service down, network fails mid-operation — what does the user see?

### Round 4 — Non-functional
- Expected scale (10 users or 10k?), performance expectations, budget for paid services.
- Look & feel: 3 adjectives, reference products/sites the user likes, dark/light preference, must-have brand elements.
- Deployment target (Vercel, VPS, local only?).

## Done criteria (before requesting the gate)

- Every feature in the census has all 9 drill-down bullets answered in `docs/DISCOVERY.md`.
- No sentence in the doc contains "probably", "TBD", or "we'll figure out later" — unless the user explicitly deferred it, marked `DEFERRED(user)`.
- Read the doc back top-to-bottom; every remaining ambiguity becomes one final question round.

Then present a summary and gate: user approves → Phase 2 (PRD).

## DISCOVERY.md format

```markdown
# Discovery — <project name>
Date: <date> · Status: draft | approved

## Vision
<one paragraph>

## Platform & stack
<confirmed choices>

## Feature census
1. <feature> — <one-liner>
2. ...

## Feature detail
### 1. <feature>
- Happy path: ...
- Inputs: ...
- Outputs: ...
- States: ...
- Edge cases: ...
- Permissions: ...
- Data lifecycle: ...
- Integrations: ...
- Failure modes: ...

## Non-functional
...

## Deferred decisions
- DEFERRED(user): <what and why>
```
