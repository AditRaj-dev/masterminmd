# Git workflow — branches, worktrees, finishing

Condensed from superpowers `using-git-worktrees` + `finishing-a-development-branch`. Mastermind rule: all build work happens on a feature branch with per-task commits; main/master never receives uncommitted experiments.

## Phase 0 — repo + branch setup

1. No git repo → `git init`, initial commit of whatever exists (including the docs/ tree as it grows).
2. Existing repo → check state: `git status` clean? On main/master? Uncommitted changes get stashed or committed with the user's OK before anything else.
3. Create the feature branch before Phase 8 (docs phases can live on it too — branch at Phase 0): `git checkout -b mastermind/<project-slug>`.
4. Commit each approved phase deliverable: `docs: PRD approved`, `docs: implementation plan approved`, etc. Gates become commits — rollback points for revisions.

## Phase 8 — commits and parallel isolation

- **Commit after every accepted task**: `T<id>: <title>` once the Sonnet review passes. Never batch multiple tasks into one commit; each commit is a rollback point.
- **Parallel groups**: parallel Haiku coders editing disjoint files on the same branch is fine (default). If tasks in a group might touch overlapping files, give each agent its own worktree instead:
  ```bash
  # verify ignored first — .worktrees/ must be in .gitignore (add it if missing)
  git worktree add .worktrees/T04 -b mastermind/T04
  ```
  Agent works in `.worktrees/T04`; after its review passes, orchestrator merges `mastermind/T04` back into the feature branch, then:
  ```bash
  cd <main repo root>   # NEVER run remove from inside the worktree
  git worktree remove .worktrees/T04 && git worktree prune
  git branch -d mastermind/T04
  ```
- Native worktree tools (EnterWorktree / `isolation: "worktree"` on the Agent tool) beat manual `git worktree add` — use them when available; don't create phantom state the harness can't see.
- Detect pre-existing isolation before creating worktrees: `git rev-parse --git-dir` ≠ `git rev-parse --git-common-dir` (and not a submodule: `git rev-parse --show-superproject-working-tree` empty) → already in a worktree, don't nest another.

## Phase 9 — finishing the branch

**Step 1 — verify first.** Run the full test suite / build. Failing → fix before offering anything. No merge/PR with red tests, ever.

**Step 2 — present exactly these 4 options (no extra prose):**

```
Implementation complete. What would you like to do?
1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work
```

**Step 3 — execute:**

- **1 Merge:** `git checkout <base> && git pull && git merge mastermind/<slug>` → re-run tests on the merged result → only then clean up worktrees and `git branch -d`.
- **2 PR:** `git push -u origin mastermind/<slug>` then `gh pr create`. Keep the worktree/branch alive — user needs it for PR feedback.
- **3 Keep:** report branch name + worktree path. Touch nothing.
- **4 Discard:** destructive — list branch, commits, and worktree that will be deleted; require the user to type `discard`; only then `git branch -D` + worktree removal.

**Cleanup rules:** only remove worktrees mastermind created (under `.worktrees/`); harness-owned workspaces are left alone. Always `cd` to the main repo root before `git worktree remove`; run `git worktree prune` after. Delete branches only after merge success is verified.

**Never:** merge with failing tests · force-push unrequested · delete work without typed confirmation · remove a worktree before its merge is confirmed.
