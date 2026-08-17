# Code graph — navigate by symbols, not file scans

Persistent code knowledge graph via the **code-review-graph** MCP server (github.com/tirth8205/code-review-graph). Tree-sitter parses the codebase into an AST, stored as a graph of nodes (classes, functions, imports) and edges (calls, inheritance, test coverage) in SQLite at `.code-review-graph/graph.db`. Agents locate symbols through graph queries instead of reading whole files — ~8x context reduction. Supported: Python, TS/JS, Vue, Go, Rust, Java, Scala, C#, Ruby, Kotlin, Swift, PHP, Solidity, C/C++.

Verified against **v1.27.0** on Windows 11 / Git Bash.

## Install (once per machine, if the MCP tools are missing)

```bash
pip install code-review-graph
code-review-graph install      # auto-detects Claude Code and registers the MCP server
code-review-graph build        # initial parse of the current repo
```

Then restart the session so the MCP server connects. If the tools are deferred, load via ToolSearch (query "code-review-graph" or "select:build_or_update_graph_tool,query_graph_tool"). If install is impossible (no pip / user declines), announce once and use the fallback ladder — never block the pipeline:
1. LSP tool (if available in the harness) — go-to-definition / find-references.
2. Grep with tight symbol patterns + Read with offset/limit.

**Two invocation paths must both work.** `.mcp.json` launches `uvx code-review-graph serve` (resolves ~80 deps on first cold start); the hooks below shell out to the bare `code-review-graph` binary on PATH (`~/AppData/Roaming/Python/Python313/Scripts/` for a pip `--user` install). Drop the pip install and the hooks die silently while the MCP server keeps working — symptom is a stale graph with no error.

`code-review-graph install` also writes configs for Cursor (`.cursor/mcp.json`), OpenCode (`.opencode.json`), and Antigravity (`~/.gemini/antigravity/mcp_config.json`). It is idempotent — preview with `--dry-run`. It reports only on MCP config: it stays **silent** about skills and hooks when it finds existing ones, and will not repair or overwrite them. Fix those by hand.

## Build / update (orchestrator)

1. `list_graph_stats_tool` — check status. `last_updated: null` → never built.
2. Build: `build_or_update_graph_tool(full_rebuild=True)` first time; `build_or_update_graph_tool()` (incremental) otherwise.
3. Verify with `list_graph_stats_tool` (files parsed, nodes/edges, languages, errors).

When:
- Phase 0 (setup) — full build if repo has existing code; skip for empty greenfield dirs (build it after the walking skeleton lands).
- After each completed build task — incremental update, so the next agents see fresh symbols.
- After major refactors or branch switches — full rebuild.

Notes: binary/generated files and `.code-review-graphignore` patterns are skipped. Optional extras: `embed_graph_tool` (enables semantic search), `generate_wiki_tool` (architecture wiki).

CLI equivalents, for hooks and for sessions where the MCP tools never attached: `update` (incremental), `build` (full re-parse), `postprocess` (recompute flows, communities, FTS index), `embed` (vector embeddings — semantic search needs this). `detect-changes` is **read-only** and does not re-parse; use `update --brief` to refresh and inspect in one step. Also available: `watch`, `visualize`, `wiki`, `dead-code`, `query`, `impact`, `search`, `flows`, `communities`, `architecture`, `large-functions`, `refactor`, `status`, `register`/`repos`, `uninstall`.

## Verify the graph is actually alive

Run top to bottom; each isolates a different failure.

```bash
uvx --version && which code-review-graph        # toolchain present
```

```bash
code-review-graph status                        # fastest health check
```

Expected shape — zero nodes or a stale timestamp means it needs a build:

```
Nodes: 276
Edges: 1367
Files: 103
Languages: python, javascript
Last updated: 2026-08-17T18:57:48
```

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}\n' | timeout 60 code-review-graph serve
```

Proves the server speaks MCP: one JSON line containing `"serverInfo":{"name":"code-review-graph","version":"1.27.0"}`. Expect **22 tools** from a `tools/list` follow-up.

## Tool map (what to use when)

**Every tool name ends in `_tool`.** This is the single most common cause of failed calls — prose and docs habitually drop the suffix. Full MCP names carry an `mcp__code-review-graph__` prefix.

| Need | Tool |
|------|------|
| Find a symbol / concept | `semantic_search_nodes_tool` (needs embed), `query_graph_tool` |
| What changed since last review | `detect_changes_tool`, `get_review_context_tool` |
| Blast radius of an edit | `get_impact_radius_tool`, `get_affected_flows_tool` |
| Big picture | `get_architecture_overview_tool`, `list_communities_tool` / `get_community_tool` |
| Execution paths | `list_flows_tool` then `get_flow_tool` |
| Decomposition targets | `find_large_functions_tool` |
| Refactor assist | `refactor_tool`, `apply_refactor_tool` |
| Maintenance | `build_or_update_graph_tool`, `embed_graph_tool`, `generate_wiki_tool` / `get_wiki_page_tool` |
| Multi-repo | `list_repos_tool`, `cross_repo_search_tool` |

`callers_of`, `callees_of`, `imports_of`, `tests_for`, `children_of` are **arguments** to `query_graph_tool` (`pattern=`), not callable tools. Calling them directly fails.

Mastermind usage: reviewers get `get_impact_radius_tool` + `get_review_context_tool` for the task's files; coders get `query_graph_tool`/`semantic_search_nodes_tool` for orientation; orchestrator uses `get_architecture_overview_tool` in adopt scans and `detect_changes_tool` before the final whole-branch review.

## Navigation rule (injected into every agent prompt)

> Before reading any file to "find where X is defined/used": query the code graph (`query_graph_tool`, `semantic_search_nodes_tool`, `get_impact_radius_tool`) — or, if unavailable, use LSP or Grep with a tight symbol pattern. Read only the specific line ranges you need (Read with offset/limit). Never read whole large files to orient yourself.

## Hooks — keep it fresh, and enforce the rule

In the project's `.claude/settings.json`:

| Event | Matcher | Command | Timeout |
|---|---|---|---|
| `PreToolUse` | `Grep\|Glob` | `python "$CLAUDE_PROJECT_DIR/.claude/hooks/require-graph.py"` | 5 s |
| `PostToolUse` | `Edit\|Write\|Bash` | `code-review-graph update --quiet` | 15 s |
| `SessionStart` | — | `code-review-graph status --json` | 10 s |

**The vendor installer writes an invalid hooks schema.** It emits `{matcher, command, timeout}` flat on the event, with the timeout in milliseconds, plus a `PreCommit` event that does not exist in Claude Code. All of it silently never fires — this is the real cause of the stale-graph symptom. The correct shape nests a `hooks` array and counts timeouts in **seconds**:

```json
{ "PostToolUse": [ { "matcher": "Edit|Write|Bash",
  "hooks": [ { "type": "command", "command": "…", "timeout": 15 } ] } ] }
```

Valid events: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Notification`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `PreCompact`. Re-running the installer reintroduces the broken block — re-fix by hand afterwards.

### The search gate

The navigation rule above is a prompt instruction; agents drift off it. To make graph-first mandatory, `.claude/hooks/require-graph.py` exits 2 on `PreToolUse` for `Grep|Glob`, which blocks the call and hands its stderr back as feedback:

```python
import pathlib, sys

REPO = pathlib.Path(__file__).resolve().parents[2]   # <repo>/.claude/hooks/this.py
DB = REPO / ".code-review-graph" / "graph.db"

# No graph on this machine yet -> raw search is the only option. Let it through.
if not DB.exists() or DB.stat().st_size == 0:
    sys.exit(0)

sys.stderr.write(
    "Blocked: this repo has a knowledge graph, query it instead of scanning files.\n"
    "  find a function/class      mcp__code-review-graph__semantic_search_nodes_tool\n"
    "  callers / callees / tests  mcp__code-review-graph__query_graph_tool (pattern=callers_of|callees_of|imports_of|tests_for|children_of)\n"
    "  blast radius of a change   mcp__code-review-graph__get_impact_radius_tool\n"
    "  high-level structure       mcp__code-review-graph__get_architecture_overview_tool\n"
    "  source snippets            mcp__code-review-graph__get_review_context_tool\n"
    "Every tool name ends in _tool. If those tools are not attached (project MCP\n"
    "needs one-time interactive trust approval), the CLI needs no approval:\n"
    "  code-review-graph search '<term>'\n"
    "  code-review-graph query <node> --pattern callers_of\n"
    "Need raw text search (non-code files, config, logs, a literal string)?\n"
    "Run it through Bash with rg -- that path is deliberately left open.\n"
)
sys.exit(2)
```

Design decisions, so nobody "fixes" them back:

- **Exits 0 when `graph.db` is missing or empty.** A fresh clone has no graph; gating search there leaves no way to explore at all.
- **`Read` is not matched.** `Edit` requires a prior `Read` — gating it deadlocks every edit.
- **`Bash` + `rg` stays open** for what the graph does not model: non-code files, config, logs, literal strings. The gate makes the graph the default path, it does not seal off text search.
- **No per-pattern heuristics.** A shell-level guess at "is this a code search" is unreliable; one unconditional gate plus a message naming the escape hatches is smaller and more honest.
- **The message names the CLI**, because the MCP tools are absent until trust approval while the CLI always works. Without that line an unapproved session is gated with no route through.

Verify both branches:

```bash
python .claude/hooks/require-graph.py; echo "with graph: exit=$?   # expect 2"
```

```bash
T=$(mktemp -d)/r; mkdir -p "$T/.claude/hooks"; cp .claude/hooks/require-graph.py "$T/.claude/hooks/"; python "$T/.claude/hooks/require-graph.py"; echo "no graph: exit=$?   # expect 0"
```

## Gotchas

**Trust approval.** A project-scoped server in `.mcp.json` needs a one-time interactive approval before `mcp__code-review-graph__*` attaches. A non-interactive session cannot perform it and there is no config workaround — open an interactive `claude` in the repo root and approve. Until then the CLI works fine while the MCP tools are simply absent.

**Naming drift across editor configs.** `.cursorrules`, `.windsurfrules`, `GEMINI.md`, `AGENTS.md`, and `CLAUDE.md` tend to carry the same doc block with tool names written *without* the `_tool` suffix. Keep them in sync or those editors emit failing calls. Note the hooks above are Claude Code only — the gate does not apply in other editors.

**Companion skills must be directories.** A loose `.claude/skills/foo.md` is not discoverable; it must be `.claude/skills/<name>/SKILL.md` with kebab-case `name` matching the directory and a "Use when…" `description`.

**`apply_refactor_tool` mutates files.** Always run `refactor_tool` with `mode="rename"` first and read the edit list before applying.

**CRLF breaks shell text comparison.** On Windows checkouts, `comm`/`diff`/`sort` pipelines silently match nothing unless carriage returns are stripped — pipe through `tr -d '\r'`. And `[a-z_]+_tool` will not span the hyphen in `mcp__code-review-graph__…`, yielding a truncated `graph__detect_changes_tool`; strip the prefix (`sed 's/^graph__//'`) before comparing against real names.

**Validate docs against the live server** — catches any tool name that would fail at call time:

```bash
grep -ohE '[a-z_]+_tool\b' CLAUDE.md mastermind/references/code-graph.md | sed 's/^graph__//' | tr -d '\r' | sort -u > /tmp/refd.txt
{ printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"v","version":"0"}}}\n'; printf '{"jsonrpc":"2.0","method":"notifications/initialized"}\n'; printf '{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n'; sleep 3; } | timeout 60 code-review-graph serve 2>/dev/null | tail -1 | python -c "import sys,json;[print(t['name']) for t in json.load(sys.stdin)['result']['tools']]" | tr -d '\r' | sort -u > /tmp/real.txt
comm -23 /tmp/refd.txt /tmp/real.txt
```

Empty output means every documented name is real.
