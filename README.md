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
| 7 Wireframe | grayscale HTML wireframes: Haiku builds, Sonnet reviews, user clicks through |
| 8 Build | orchestrated execution: diff-based reviews, fix loop → root-cause debugging, commit per task, final whole-branch review |
| 9 Wrap | evidence-based verification + 4-option branch finish (merge / PR / keep / discard) |

Cross-cutting: memory docs (`MEMORY.md` mistakes→resolutions + `HANDOFF.md`) read by every agent, code-graph symbol navigation, optional browser **visual companion** with clickable option screens, `continue`/`status` resume.

### `/mastermind-adopt` — onboard an existing project

Scans an ongoing codebase → `docs/INITIAL_STATE.md` (stack, structure, feature census, health) + `docs/CODE_STATE.md` (git work-stream history, where coding stopped, unfinished-work inventory, resume points) → finds existing PRDs and asks whether to adopt them (gap-check interview) or runs full discovery → hands off to `/mastermind continue`.

## Install

```powershell
git clone https://github.com/AditRaj-dev/masterminmd
Copy-Item -Recurse masterminmd\skills\* "$env:USERPROFILE\.claude\skills\"
```

```bash
# macOS / Linux
git clone https://github.com/AditRaj-dev/masterminmd
cp -r masterminmd/skills/* ~/.claude/skills/
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
