# Mastermind

Hierarchical build-orchestrator skills for [Claude Code](https://claude.com/claude-code). The top-tier model orchestrates and never writes production code; **Haiku agents code, Sonnet agents review**, every phase is document-driven and user-gated.

## Skills

### `/mastermind` — build a product end-to-end

10 gated phases:

| Phase | Deliverable |
|---|---|
| 0 Setup | git feature branch, `docs/` tree, code graph |
| 1 Discovery | `docs/DISCOVERY.md` — deep interview, per-feature drill-down (states, edge cases, permissions, data lifecycle, failure modes) |
| 2 PRD | `docs/PRD.md` |
| 3 Feature docs | `docs/features/<nn>-<slug>.md` — one buildable spec per feature |
| 4 Plan | `docs/IMPLEMENTATION_PLAN.md` — Haiku-sized tasks, parallel groups |
| 5 API record | `docs/API_RECORD.md` — verified-only API registry (anti-hallucination: unlisted API = review FAIL) |
| 6 Design | `docs/DESIGN.md` — 4 bundled design systems merged (ui-ux-pro-max, impeccable, taste-design, frontend-design) |
| 7 Mockups | high-fidelity static HTML+CSS mockups — real colors, fonts, spacing, corner radii from DESIGN.md via shared tokens.css: Haiku builds, Sonnet reviews fidelity, user clicks through |
| 8 Build | orchestrated execution: diff-based reviews, fix loop → root-cause debugging, commit per task, final whole-branch review |
| 9 Wrap | evidence-based verification + 4-option branch finish (merge / PR / keep / discard) |

Cross-cutting: memory docs (`MEMORY.md` mistakes→resolutions + `HANDOFF.md`) read by every agent, code-graph symbol navigation, optional browser **visual companion** with clickable option screens, `continue`/`status` resume.

### `/mastermind-adopt` — onboard an existing project

Scans an ongoing codebase → `docs/INITIAL_STATE.md` (stack, structure, feature census, health) + `docs/CODE_STATE.md` (git work-stream history, where coding stopped, unfinished-work inventory, resume points) → finds existing PRDs and asks whether to adopt them (gap-check interview) or runs full discovery → hands off to `/mastermind continue`.

### `/projects` — cross-project overview board

Reads `~/.claude/projects-registry.json` (mastermind Phase 0 auto-registers projects) + the memex board + git state per project, and renders a one-screen status table: tasks done/total, open handoffs, last commit, dirty files, next step. `add <path>` registers a project, `open <name>` prints resume instructions, `html` renders a report.

## Agentic-OS layer (agents/ + memex/)

Mastermind's Phase 8 routes coder tasks by **domain tag** to hardened specialist agents instead of generic Haiku dispatches (routing table: `skills/mastermind/references/agents.md`):

| agent | model | domain |
|---|---|---|
| `nextjs-dev`, `react-dev`, `react-native-dev`, `flutter-dev` | haiku | frontend/mobile stacks |
| `database-engineer`, `api-developer` | haiku | data + service layers |
| `architect` | sonnet | review-only architectural passes |
| `ui-designer` | sonnet | tokens, wireframes, Figma (Phase 6–7) |

Each agent def is self-contained: ~17 non-negotiable domain rules, caveman/ponytail style, memory + API-record protocol, verification iron law. Unmatched domains fall back to `general-purpose` + haiku, so mastermind still works without the agents installed.

**memex** (`memex/`) — shared memory + task-handoff store all providers can reach: zero-dep Node CLI (`node:sqlite`, FTS5 search, DB at `~/.claude/memex.db`) plus a thin MCP wrapper for native Claude tools. Agents log decisions (`memex remember`), pass work via structured handoffs (`memex handoff create/accept`), and mirror plan status (`memex task set`) — the `/projects` board reads the same DB.

**Multi-provider bridge** (`agents/references/providers.md`) — headless second opinions: `gemini -p` (UI instinct, auth via `GEMINI_API_KEY`) and `codex exec` (backend logic). Advisory only; Claude agents own the final code and every consult is logged to memex.

## Install

```powershell
git clone https://github.com/AditRaj-dev/masterminmd
Copy-Item -Recurse masterminmd\skills\* "$env:USERPROFILE\.claude\skills\"
Copy-Item -Recurse masterminmd\agents "$env:USERPROFILE\.claude\agents"
npm install -g .\masterminmd\memex
claude mcp add --scope user memex -- memex-mcp
```

```bash
# macOS / Linux
git clone https://github.com/AditRaj-dev/masterminmd
cp -r masterminmd/skills/* ~/.claude/skills/
cp -r masterminmd/agents ~/.claude/agents
npm install -g ./masterminmd/memex
claude mcp add --scope user memex -- memex-mcp
```

**Path note:** the skill files cross-reference each other via absolute paths under `C:\Users\study\.claude\skills\`. After copying, rewrite them for your machine:

```powershell
Get-ChildItem "$env:USERPROFILE\.claude\skills\mastermind*" -Recurse -Filter *.md |
  ForEach-Object { (Get-Content $_.FullName -Raw) -replace 'C:\\Users\\study', $env:USERPROFILE | Set-Content $_.FullName -NoNewline }
```

## Prerequisites

- **Claude Code** with the `Agent` tool (`model: haiku` / `sonnet` dispatch)
- **Python 3.8+** — bundled ui-ux-pro-max design search (`skills/mastermind/scripts/search.py` + 31 CSV datasets)
- **[code-review-graph](https://github.com/tirth8205/code-review-graph)** (recommended) — `pip install code-review-graph && code-review-graph install && code-review-graph build`; skills fall back to LSP/Grep without it
- **Node.js** (optional) — visual companion browser server (`skills/mastermind/scripts/companion/`)

## Credits

Bundles adapted content from: [ui-ux-pro-max](https://github.com/nextlevelbros/ui-ux-pro-max-skill), impeccable (Apache 2.0), taste-design, Anthropic's frontend-design skill, and [obra/superpowers](https://github.com/obra/superpowers) (visual companion, git worktree/branch-finishing workflows, verification and debugging protocols). Caveman/ponytail style rules adapted from their respective plugins.
