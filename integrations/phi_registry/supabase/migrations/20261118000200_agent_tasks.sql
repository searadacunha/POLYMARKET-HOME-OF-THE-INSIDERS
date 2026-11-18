-- PHI registry, agent coordination. Portable SQL (SQLite 3.35+ and PostgreSQL 15+). This is OPERATIONAL state, not
-- derived: `build` never touches it. A task is one unit of research (a wallet, a market, a hypothesis) that exactly one
-- agent may hold at a time; `dedup_key` makes two agents proposing the same unit create one row.

CREATE TABLE IF NOT EXISTS agent_tasks (
  id           TEXT PRIMARY KEY,
  dedup_key    TEXT NOT NULL UNIQUE,
  kind         TEXT NOT NULL,
  subject      TEXT NOT NULL,
  priority     INTEGER NOT NULL DEFAULT 3,
  status       TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'done', 'failed')),
  attempts     INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  claimed_by   TEXT,
  lease_until  BIGINT,
  result_ref   TEXT,
  last_error   TEXT,
  created_at   BIGINT NOT NULL,
  updated_at   BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS agent_tasks_queue ON agent_tasks (status, priority, created_at);

-- Append-only audit trail of every transition (who, when, what).
CREATE TABLE IF NOT EXISTS task_events (
  id      TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES agent_tasks (id),
  at      BIGINT NOT NULL,
  agent   TEXT,
  event   TEXT NOT NULL CHECK (event IN ('added', 'claimed', 'heartbeat', 'done', 'requeued', 'failed')),
  detail  TEXT
);
CREATE INDEX IF NOT EXISTS task_events_task ON task_events (task_id, at);
