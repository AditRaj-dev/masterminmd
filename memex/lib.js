'use strict';
// memex core — one SQLite DB shared by every agent/provider (Claude, Codex, Gemini).
// DB path: %MEMEX_DB% or ~/.claude/memex.db
const { DatabaseSync } = require('node:sqlite');
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs');

const DB_PATH = process.env.MEMEX_DB || path.join(os.homedir(), '.claude', 'memex.db');

let db = null;
let hasFts = false;

function open() {
  if (db) return db;
  fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
  db = new DatabaseSync(DB_PATH);
  db.exec('PRAGMA journal_mode=WAL');
  db.exec(`
    CREATE TABLE IF NOT EXISTS memories(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      project TEXT NOT NULL,
      agent TEXT NOT NULL DEFAULT 'unknown',
      provider TEXT NOT NULL DEFAULT 'claude',
      type TEXT NOT NULL DEFAULT 'context',
      content TEXT NOT NULL,
      tags TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS handoffs(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      project TEXT NOT NULL,
      task_id TEXT NOT NULL DEFAULT '',
      from_agent TEXT NOT NULL,
      to_agent TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL DEFAULT 'open',
      summary TEXT NOT NULL,
      artifacts TEXT NOT NULL DEFAULT '',
      blockers TEXT NOT NULL DEFAULT '',
      created_at TEXT NOT NULL DEFAULT (datetime('now')),
      accepted_at TEXT
    );
    CREATE TABLE IF NOT EXISTS tasks(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      project TEXT NOT NULL,
      task_id TEXT NOT NULL,
      title TEXT NOT NULL DEFAULT '',
      domain TEXT NOT NULL DEFAULT '',
      status TEXT NOT NULL DEFAULT 'todo',
      assignee TEXT NOT NULL DEFAULT '',
      updated_at TEXT NOT NULL DEFAULT (datetime('now')),
      UNIQUE(project, task_id)
    );
  `);
  try {
    db.exec(`CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(content, tags)`);
    hasFts = true;
  } catch {
    hasFts = false; // ponytail: LIKE fallback below; upgrade path is better-sqlite3 if FTS missing
  }
  return db;
}

function remember({ project, content, agent = 'unknown', provider = 'claude', type = 'context', tags = '' }) {
  if (!project || !content) throw new Error('remember: project and content are required');
  open();
  const r = db.prepare(
    `INSERT INTO memories(project, agent, provider, type, content, tags) VALUES(?,?,?,?,?,?)`
  ).run(project, agent, provider, type, content, tags);
  const id = Number(r.lastInsertRowid);
  if (hasFts) db.prepare(`INSERT INTO memories_fts(rowid, content, tags) VALUES(?,?,?)`).run(id, content, tags);
  return { id };
}

function search({ query, project = null, limit = 10 }) {
  if (!query) throw new Error('search: query is required');
  open();
  const proj = project ? ` AND m.project = ?` : '';
  let rows;
  if (hasFts) {
    try {
      const params = project ? [query, project, limit] : [query, limit];
      rows = db.prepare(
        `SELECT m.* FROM memories_fts f JOIN memories m ON m.id = f.rowid
         WHERE memories_fts MATCH ?${proj} ORDER BY m.id DESC LIMIT ?`
      ).all(...params);
      return rows;
    } catch { /* bad FTS syntax in query -> fall through to LIKE */ }
  }
  const like = `%${query}%`;
  const params = project ? [like, like, project, limit] : [like, like, limit];
  rows = db.prepare(
    `SELECT m.* FROM memories m WHERE (m.content LIKE ? OR m.tags LIKE ?)${proj}
     ORDER BY m.id DESC LIMIT ?`
  ).all(...params);
  return rows;
}

function handoffCreate({ project, from, summary, taskId = '', to = '', artifacts = '', blockers = '' }) {
  if (!project || !from || !summary) throw new Error('handoff create: project, from and summary are required');
  open();
  const r = db.prepare(
    `INSERT INTO handoffs(project, task_id, from_agent, to_agent, summary, artifacts, blockers)
     VALUES(?,?,?,?,?,?,?)`
  ).run(project, taskId, from, to, summary, artifacts, blockers);
  return { id: Number(r.lastInsertRowid) };
}

function handoffAccept({ id, agent = '' }) {
  open();
  const row = db.prepare(`SELECT * FROM handoffs WHERE id = ?`).get(id);
  if (!row) throw new Error(`handoff accept: no handoff #${id}`);
  db.prepare(
    `UPDATE handoffs SET status='accepted', accepted_at=datetime('now'),
     to_agent = CASE WHEN to_agent='' THEN ? ELSE to_agent END WHERE id = ?`
  ).run(agent, id);
  return db.prepare(`SELECT * FROM handoffs WHERE id = ?`).get(id);
}

function handoffClose({ id }) {
  open();
  const r = db.prepare(`UPDATE handoffs SET status='done' WHERE id = ?`).run(id);
  if (r.changes === 0) throw new Error(`handoff close: no handoff #${id}`);
  return db.prepare(`SELECT * FROM handoffs WHERE id = ?`).get(id);
}

function handoffList({ project = null, status = null, limit = 50 } = {}) {
  open();
  const where = [];
  const params = [];
  if (project) { where.push('project = ?'); params.push(project); }
  if (status) { where.push('status = ?'); params.push(status); }
  const sql = `SELECT * FROM handoffs${where.length ? ' WHERE ' + where.join(' AND ') : ''}
               ORDER BY id DESC LIMIT ?`;
  return db.prepare(sql).all(...params, limit);
}

function taskSet({ project, taskId, title = null, domain = null, status = null, assignee = null }) {
  if (!project || !taskId) throw new Error('task set: project and taskId are required');
  open();
  db.prepare(
    `INSERT INTO tasks(project, task_id, title, domain, status, assignee)
     VALUES(?,?,COALESCE(?,''),COALESCE(?,''),COALESCE(?,'todo'),COALESCE(?,''))
     ON CONFLICT(project, task_id) DO UPDATE SET
       title    = COALESCE(?, title),
       domain   = COALESCE(?, domain),
       status   = COALESCE(?, status),
       assignee = COALESCE(?, assignee),
       updated_at = datetime('now')`
  ).run(project, taskId, title, domain, status, assignee, title, domain, status, assignee);
  return db.prepare(`SELECT * FROM tasks WHERE project = ? AND task_id = ?`).get(project, taskId);
}

function board({ project = null } = {}) {
  open();
  if (project) {
    return {
      project,
      tasks: db.prepare(`SELECT * FROM tasks WHERE project = ? ORDER BY task_id`).all(project),
      open_handoffs: handoffList({ project, status: 'open' }),
      memory_count: db.prepare(`SELECT COUNT(*) c FROM memories WHERE project = ?`).get(project).c
    };
  }
  // cross-project rollup
  return db.prepare(`
    SELECT p.project,
      (SELECT COUNT(*) FROM tasks t WHERE t.project = p.project) AS tasks,
      (SELECT COUNT(*) FROM tasks t WHERE t.project = p.project AND t.status = 'done') AS done,
      (SELECT COUNT(*) FROM handoffs h WHERE h.project = p.project AND h.status = 'open') AS open_handoffs,
      (SELECT COUNT(*) FROM memories m WHERE m.project = p.project) AS memories,
      (SELECT MAX(updated_at) FROM tasks t WHERE t.project = p.project) AS last_activity
    FROM (SELECT project FROM tasks UNION SELECT project FROM handoffs UNION SELECT project FROM memories) p
    ORDER BY last_activity DESC
  `).all();
}

module.exports = { open, remember, search, handoffCreate, handoffAccept, handoffClose, handoffList, taskSet, board, DB_PATH };
