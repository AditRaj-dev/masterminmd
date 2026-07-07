# Phase 5 — API record (anti-hallucination registry)

LLMs hallucinate APIs: wrong method names, invented parameters, deprecated signatures. `docs/API_RECORD.md` is the single source of truth. THE RULE, injected into every agent prompt:

> **Only call APIs listed in docs/API_RECORD.md. Need one that isn't listed? STOP. Verify it against real documentation or real type definitions, add it to the record with its verified source, THEN use it. Never call an API from memory.**

## Verification procedure (how an entry earns its place)

1. **External library/SDK**: read the actual installed types — `node_modules/<pkg>/dist/*.d.ts`, `node_modules/<pkg>/README.md`, or the package's own source. Version-pin: record the version from package.json/lockfile.
2. **External HTTP API**: WebFetch the official docs page for the endpoint. Record the docs URL + date fetched.
3. **Internal module**: after the module is built and reviewed, record its exported interface from the actual source file (path + line).
4. If types/docs contradict what you expected: the record wins over memory — write what's actually there.

## docs/API_RECORD.md format

```markdown
# API record — <project name>
Rule: agents may ONLY use APIs listed here. Verify-then-add for anything new.

## External libraries
### <package>@<version>
| API | Signature | Does | Returns | Verified from |
|-----|-----------|------|---------|---------------|
| `createClient` | `createClient(url: string, key: string, opts?: Options)` | Creates client instance | `SupabaseClient` | node_modules/@supabase/supabase-js/dist/module/index.d.ts (2026-07-07) |

Gotchas: <quirks discovered — wrong assumptions that cost time go here AND in MEMORY.md>

## External HTTP APIs
### <service>
| Endpoint | Method | Params | Returns | Auth | Verified from (URL, date) |

## Internal interfaces
### <module path>
| Export | Signature | Does | Returns | Source |
|--------|-----------|------|---------|--------|
| `getUser` | `getUser(id: string): Promise<User \| null>` | Fetch user by id | User or null (not throw) | src/lib/users.ts:12 |
```

## Lifecycle

- **Phase 5 (initial build)**: orchestrator walks the implementation plan, lists every external dependency each task needs, verifies and records the specific APIs that will be called. Internal interfaces get *planned* signatures marked `PLANNED`; flipped to verified (with source path) when the module lands.
- **During build**: coder needs an unlisted API → coder reports back instead of guessing; orchestrator (or a dispatched verification step) verifies + adds, then re-dispatches. Reviewer checks every API call in the diff against the record — unlisted call = automatic review failure.
- **After build tasks**: orchestrator updates internal-interface entries for any new/changed exports.
