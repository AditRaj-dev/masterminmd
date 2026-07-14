'use strict';
// memex self-check — node test.js
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

const tmpDb = path.join(os.tmpdir(), `memex-test-${Date.now()}.db`);
process.env.MEMEX_DB = tmpDb;
const m = require('./lib.js');

// remember -> search roundtrip
const { id } = m.remember({ project: 'demo', content: 'use zod for input validation at API boundaries', agent: 'api-developer', type: 'decision', tags: 'validation,zod' });
assert.ok(id > 0, 'remember returns id');
let hits = m.search({ query: 'zod', project: 'demo' });
assert.strictEqual(hits.length, 1, 'search finds the memory');
assert.strictEqual(hits[0].agent, 'api-developer');
assert.strictEqual(m.search({ query: 'zod', project: 'other' }).length, 0, 'project filter works');

// handoff create -> accept -> close
const h = m.handoffCreate({ project: 'demo', taskId: 'T-001', from: 'database-engineer', summary: 'schema done, run migrations before wiring routes', artifacts: 'prisma/schema.prisma' });
let open = m.handoffList({ project: 'demo', status: 'open' });
assert.strictEqual(open.length, 1, 'handoff listed as open');
const accepted = m.handoffAccept({ id: h.id, agent: 'api-developer' });
assert.strictEqual(accepted.status, 'accepted');
assert.strictEqual(accepted.to_agent, 'api-developer', 'accepting agent recorded');
assert.strictEqual(m.handoffClose({ id: h.id }).status, 'done');

// task upsert + board
m.taskSet({ project: 'demo', taskId: 'T-001', title: 'DB schema', domain: 'database', status: 'done', assignee: 'database-engineer' });
m.taskSet({ project: 'demo', taskId: 'T-001', status: 'done' }); // upsert keeps title
m.taskSet({ project: 'demo', taskId: 'T-002', title: 'API routes', domain: 'api', status: 'in_progress' });
const b = m.board({ project: 'demo' });
assert.strictEqual(b.tasks.length, 2);
assert.strictEqual(b.tasks[0].title, 'DB schema', 'upsert preserved title');
assert.strictEqual(b.memory_count, 1);
const rollup = m.board({});
assert.strictEqual(rollup[0].project, 'demo');
assert.strictEqual(rollup[0].done, 1);

console.log(`OK — all memex checks passed (db: ${tmpDb})`);
try { fs.unlinkSync(tmpDb); } catch {}
