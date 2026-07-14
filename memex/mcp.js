#!/usr/bin/env node
'use strict';
// memex MCP wrapper — thin stdio server over lib.js so Claude-side agents get native tools.
// ponytail: raw newline-delimited JSON-RPC, no SDK dep; CLI remains the contract if this breaks.
const m = require('./lib.js');

const TOOLS = [
  {
    name: 'memex_remember',
    description: 'Store a memory (lesson/decision/api/context) in the shared agent memory DB',
    inputSchema: { type: 'object', properties: {
      project: { type: 'string' }, content: { type: 'string' },
      agent: { type: 'string' }, provider: { type: 'string' },
      type: { type: 'string', enum: ['lesson', 'decision', 'api', 'context'] },
      tags: { type: 'string' }
    }, required: ['project', 'content'] }
  },
  {
    name: 'memex_search',
    description: 'Full-text search shared agent memories, newest first',
    inputSchema: { type: 'object', properties: {
      query: { type: 'string' }, project: { type: 'string' }, limit: { type: 'number' }
    }, required: ['query'] }
  },
  {
    name: 'memex_handoff_create',
    description: 'Create a structured task handoff for the next agent (summary, artifacts, blockers)',
    inputSchema: { type: 'object', properties: {
      project: { type: 'string' }, from: { type: 'string' }, summary: { type: 'string' },
      taskId: { type: 'string' }, to: { type: 'string' }, artifacts: { type: 'string' }, blockers: { type: 'string' }
    }, required: ['project', 'from', 'summary'] }
  },
  {
    name: 'memex_handoff_accept',
    description: 'Accept an open handoff by id (marks it accepted, records accepting agent)',
    inputSchema: { type: 'object', properties: {
      id: { type: 'number' }, agent: { type: 'string' }
    }, required: ['id'] }
  },
  {
    name: 'memex_handoff_list',
    description: 'List handoffs, filterable by project and status (open/accepted/done)',
    inputSchema: { type: 'object', properties: {
      project: { type: 'string' }, status: { type: 'string' }
    } }
  },
  {
    name: 'memex_task_set',
    description: 'Upsert a task on the live board (status: todo/in_progress/done/blocked)',
    inputSchema: { type: 'object', properties: {
      project: { type: 'string' }, taskId: { type: 'string' }, title: { type: 'string' },
      domain: { type: 'string' }, status: { type: 'string' }, assignee: { type: 'string' }
    }, required: ['project', 'taskId'] }
  },
  {
    name: 'memex_board',
    description: 'Project board (tasks, open handoffs, memory count) or cross-project rollup when no project given',
    inputSchema: { type: 'object', properties: { project: { type: 'string' } } }
  }
];

function callTool(name, a = {}) {
  switch (name) {
    case 'memex_remember': return m.remember(a);
    case 'memex_search': return m.search({ query: a.query, project: a.project || null, limit: a.limit || 10 });
    case 'memex_handoff_create': return m.handoffCreate(a);
    case 'memex_handoff_accept': return m.handoffAccept(a);
    case 'memex_handoff_list': return m.handoffList({ project: a.project || null, status: a.status || null });
    case 'memex_task_set': return m.taskSet({ project: a.project, taskId: a.taskId, title: a.title ?? null, domain: a.domain ?? null, status: a.status ?? null, assignee: a.assignee ?? null });
    case 'memex_board': return m.board({ project: a.project || null });
    default: throw new Error(`unknown tool: ${name}`);
  }
}

function send(msg) { process.stdout.write(JSON.stringify(msg) + '\n'); }

function handle(req) {
  const { id, method, params } = req;
  if (method === 'initialize') {
    send({ jsonrpc: '2.0', id, result: {
      protocolVersion: (params && params.protocolVersion) || '2024-11-05',
      capabilities: { tools: {} },
      serverInfo: { name: 'memex', version: '1.0.0' }
    } });
  } else if (method === 'tools/list') {
    send({ jsonrpc: '2.0', id, result: { tools: TOOLS } });
  } else if (method === 'tools/call') {
    try {
      const result = callTool(params.name, params.arguments || {});
      send({ jsonrpc: '2.0', id, result: { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] } });
    } catch (e) {
      send({ jsonrpc: '2.0', id, result: { content: [{ type: 'text', text: `error: ${e.message}` }], isError: true } });
    }
  } else if (method === 'ping') {
    send({ jsonrpc: '2.0', id, result: {} });
  } else if (id !== undefined) {
    send({ jsonrpc: '2.0', id, error: { code: -32601, message: `method not found: ${method}` } });
  }
  // notifications (no id) are ignored
}

let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  buf += chunk;
  let nl;
  while ((nl = buf.indexOf('\n')) !== -1) {
    const line = buf.slice(0, nl).trim();
    buf = buf.slice(nl + 1);
    if (!line) continue;
    try { handle(JSON.parse(line)); }
    catch { /* ignore malformed lines */ }
  }
});
process.stdin.on('end', () => process.exit(0));
