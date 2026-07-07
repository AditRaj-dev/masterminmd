# Code graph — navigate by symbols, not file scans

Persistent code knowledge graph via the **code-review-graph** MCP server (github.com/tirth8205/code-review-graph). Tree-sitter parses the codebase into an AST, stored as a graph of nodes (classes, functions, imports) and edges (calls, inheritance, test coverage) in SQLite at `.code-review-graph/graph.db`. Agents locate symbols through graph queries instead of reading whole files — ~8x context reduction. Supported: Python, TS/JS, Vue, Go, Rust, Java, Scala, C#, Ruby, Kotlin, Swift, PHP, Solidity, C/C++.

## Install (once per machine, if the MCP tools are missing)

```bash
pip install code-review-graph
code-review-graph install      # auto-detects Claude Code and registers the MCP server
code-review-graph build        # initial parse of the current repo
```

Then restart the session so the MCP server connects. If the tools are deferred, load via ToolSearch (query "code-review-graph" or "select:build_or_update_graph_tool,query_graph"). If install is impossible (no pip / user declines), announce once and use the fallback ladder — never block the pipeline:
1. LSP tool (if available in the harness) — go-to-definition / find-references.
2. Grep with tight symbol patterns + Read with offset/limit.

## Build / update (orchestrator)

1. `list_graph_stats_tool` — check status. `last_updated: null` → never built.
2. Build: `build_or_update_graph_tool(full_rebuild=True)` first time; `build_or_update_graph_tool()` (incremental) otherwise.
3. Verify with `list_graph_stats_tool` (files parsed, nodes/edges, languages, errors).

When:
- Phase 0 (setup) — full build if repo has existing code; skip for empty greenfield dirs (build it after the walking skeleton lands).
- After each completed build task — incremental update, so the next agents see fresh symbols.
- After major refactors or branch switches — full rebuild.

Notes: binary/generated files and `.code-review-graphignore` patterns are skipped. Optional extras: `embed_graph_tool` (enables semantic search), `generate_wiki_tool` (architecture wiki).

## Tool map (what to use when)

| Need | Tool |
|------|------|
| Find a symbol / concept | `semantic_search_nodes` (needs embed), `query_graph` |
| What changed since last review | `detect_changes`, `get_review_context` |
| Blast radius of an edit | `get_impact_radius`, `get_affected_flows` |
| Big picture | `get_architecture_overview`, `list_communities` |
| Refactor assist | `refactor_tool`, `apply_refactor_tool` |
| Maintenance | `build_or_update_graph_tool`, `embed_graph_tool`, `generate_wiki_tool` |

Mastermind usage: reviewers get `get_impact_radius` + `get_review_context` for the task's files; coders get `query_graph`/`semantic_search_nodes` for orientation; orchestrator uses `get_architecture_overview` in adopt scans and `detect_changes` before the final whole-branch review.

## Navigation rule (injected into every agent prompt)

> Before reading any file to "find where X is defined/used": query the code graph (`query_graph`, `semantic_search_nodes`, `get_impact_radius`) — or, if unavailable, use LSP or Grep with a tight symbol pattern. Read only the specific line ranges you need (Read with offset/limit). Never read whole large files to orient yourself.
