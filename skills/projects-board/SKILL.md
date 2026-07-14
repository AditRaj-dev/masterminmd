---
name: projects-board
description: Overview board of all registered projects — status, tasks, open handoffs, git state, next steps. Trigger with /projects or /projects-board. Args: (none)=board, add <path>, open <name>, html.
---

# Projects board

Registry: `C:\Users\study\.claude\projects-registry.json` — array of `{name, path, stack, status, added}`. Hand-editable; mastermind Phase 0 appends new projects. Shared memory/tasks: `memex` CLI (global) — same DB every agent writes to.

## `/projects` (no args) — render the board

1. Read the registry. Skip entries whose `path` no longer exists (note them at the bottom as "missing").
2. Get the cross-project rollup in ONE call: `memex board --json` (per-project task counts, done counts, open handoffs, memory counts, last activity).
3. For each registered project (batch these — one PowerShell call for all projects, not one per project):
   - `git -C <path> log -1 --format="%h %ar %s"` and `(git -C <path> status --porcelain | Measure-Object -Line).Lines` → last commit + dirty file count (skip silently if not a git repo).
   - If `<path>\docs\memory\HANDOFF.md` exists: read first ~30 lines, extract the current state / next step line.
4. Render a markdown table, most-recently-active first:

   | project | stack | tasks (done/total) | open handoffs | last commit | dirty | next step |

   After the table: one line per project with open handoffs or blockers worth attention ("CrewC: 2 open handoffs — run `memex handoff list --project CrewC --status open`"). Then missing-path entries, if any.
5. Keep it one screen. No prose padding.

## `/projects add <path>`

1. Verify the path exists. Infer `name` (dir basename) and `stack`: pubspec.yaml → flutter; package.json deps: next → nextjs, react-native/expo → react-native, react → react, else node; requirements.txt/pyproject.toml → python; check one subdir level for monorepos; else unknown.
2. Append `{name, path, stack, status: "active", added: <today>}` to the registry JSON (no duplicates by path — update instead).
3. Confirm with the new registry row.

## `/projects open <name>`

1. Find the entry (fuzzy match on name). Print resume block:
   - `cd <path>`
   - Board slice: `memex board --project <name> --json` summarized (in-progress tasks, open handoffs).
   - If `docs/memory/HANDOFF.md` exists → "resume with `/mastermind continue`"; else → "start with `/mastermind <idea>` or `/mastermind-adopt`".

## `/projects html`

Same data as the board, rendered as a static HTML report via the Artifact tool (load the `artifact-design` skill first, per Artifact tool rules). Cards per project: name, stack badge, task progress bar, open handoffs list, last commit, next step. This HTML is the precursor of the future D:\new web dashboard — keep the data shape identical to `memex board --json`.

## Rules

- Read-only except `add` (registry append) — never mutate project dirs from this skill.
- Batch shell calls; the whole board should take ≤3 tool calls for any number of projects.
- Numbers come from real command output, never from memory of a previous render.
