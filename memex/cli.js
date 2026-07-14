#!/usr/bin/env node
'use strict';
// memex CLI — universal access path: any agent/provider that can run a shell can use this.
const m = require('./lib.js');

const HELP = `memex — shared agent memory + task handoffs (db: ${m.DB_PATH})

  memex remember <content>  --project X [--agent A] [--provider claude|codex|gemini] [--type lesson|decision|api|context] [--tags a,b]
  memex search <query>      [--project X] [--limit 10] [--json]
  memex handoff create      --project X --from A --summary S [--task T-001] [--to B] [--artifacts paths] [--blockers text]
  memex handoff accept <id> [--agent A]
  memex handoff close <id>
  memex handoff list        [--project X] [--status open|accepted|done] [--json]
  memex task set <task_id>  --project X [--title T] [--domain nextjs|react|react-native|flutter|database|api|design|general] [--status todo|in_progress|done|blocked] [--assignee A]
  memex board               [--project X] [--json]`;

function parse(argv) {
  const pos = [];
  const opts = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith('--')) { opts[key] = true; }
      else { opts[key] = next; i++; }
    } else pos.push(a);
  }
  return { pos, opts };
}

function out(data, json) {
  if (json) { console.log(JSON.stringify(data, null, 2)); return; }
  if (Array.isArray(data)) {
    if (data.length === 0) { console.log('(none)'); return; }
    for (const row of data) console.log(fmtRow(row));
  } else if (typeof data === 'object' && data !== null) {
    console.log(JSON.stringify(data, null, 2));
  } else console.log(data);
}

function fmtRow(r) {
  if ('content' in r) return `#${r.id} [${r.project}] ${r.type}/${r.agent}@${r.provider} ${r.created_at}\n  ${r.content}${r.tags ? `\n  tags: ${r.tags}` : ''}`;
  if ('summary' in r) return `#${r.id} [${r.project}] ${r.status} ${r.task_id || '-'} ${r.from_agent} -> ${r.to_agent || '?'}\n  ${r.summary}${r.artifacts ? `\n  artifacts: ${r.artifacts}` : ''}${r.blockers ? `\n  BLOCKERS: ${r.blockers}` : ''}`;
  return JSON.stringify(r);
}

function main() {
  const { pos, opts } = parse(process.argv.slice(2));
  const [cmd, sub] = pos;
  const json = !!opts.json;
  try {
    switch (cmd) {
      case 'remember':
        out(m.remember({ project: opts.project, content: pos.slice(1).join(' '), agent: opts.agent, provider: opts.provider, type: opts.type, tags: opts.tags }), json);
        break;
      case 'search':
        out(m.search({ query: pos.slice(1).join(' '), project: opts.project || null, limit: Number(opts.limit) || 10 }), json);
        break;
      case 'handoff':
        if (sub === 'create') out(m.handoffCreate({ project: opts.project, from: opts.from, summary: opts.summary, taskId: opts.task, to: opts.to, artifacts: opts.artifacts, blockers: opts.blockers }), json);
        else if (sub === 'accept') out(m.handoffAccept({ id: Number(pos[2]), agent: opts.agent || '' }), json);
        else if (sub === 'close') out(m.handoffClose({ id: Number(pos[2]) }), json);
        else if (sub === 'list') out(m.handoffList({ project: opts.project || null, status: opts.status || null }), json);
        else throw new Error(`unknown handoff subcommand: ${sub}`);
        break;
      case 'task':
        if (sub !== 'set') throw new Error(`unknown task subcommand: ${sub}`);
        out(m.taskSet({ project: opts.project, taskId: pos[2], title: opts.title ?? null, domain: opts.domain ?? null, status: opts.status ?? null, assignee: opts.assignee ?? null }), json);
        break;
      case 'board':
        out(m.board({ project: opts.project || null }), json);
        break;
      case 'help':
      case undefined:
        console.log(HELP);
        break;
      default:
        throw new Error(`unknown command: ${cmd}`);
    }
  } catch (e) {
    console.error(`memex error: ${e.message}`);
    process.exit(1);
  }
}

main();
