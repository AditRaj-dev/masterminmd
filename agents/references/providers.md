# Multi-provider bridge — headless CLIs

Specialist agents run on Claude. For second opinions, two external brains are available as shell commands (Bash tool). No GUI automation, ever.

## Gemini — visual/UI instinct
- Command: `gemini -p "<prompt>"` (add `-m <model>` for a specific model, e.g. latest flash/pro).
- Auth: `GEMINI_API_KEY` env var (AI Studio key). OAuth login is NOT used on this machine.
- Who: `ui-designer` (layout/visual direction), anyone needing a design gut-check.
- Unavailable (no key set / command fails)? Proceed without it — it is advisory, never a blocker.

## GPT via Codex — backend logic
- Command: `codex exec "<prompt>"` (installed globally; see codex plugin skill `codex:codex-cli-runtime` for flags like `--model`, sandbox options). Outside a git repo add `--skip-git-repo-check`. The final line of stdout is the answer (verified 2026-07-14).
- Who: `api-developer`, `database-engineer` (gnarly logic, concurrency, query plans, algorithms); anyone stuck after two failed attempts on a logic bug.

## Rules (all providers)
1. External output is ADVISORY. The Claude agent reviews, adapts, and owns the final code/artifact. Never paste external output verbatim into the codebase.
2. Reviews still gate everything: mastermind's reviewer/architect checks the result the same as any other code.
3. Log every consult to the shared memory so cross-provider context survives:
   `memex remember "<question + what was adopted/rejected>" --project <project> --agent <you> --provider gemini|codex --type decision`
4. Keep prompts self-contained: the external CLI has no access to this session's context — include the relevant spec lines, constraints, and code snippets in the prompt itself.
5. Never send secrets (keys, tokens, credentials, customer data) in a prompt to any external provider.

## Adding a provider later
Any headless CLI fits this pattern (e.g. Hermes Agent's CLI): document command + auth + who uses it here; agents pick it up by reading this file. memex remains the shared memory across all of them.
