-- PHI registry, core tables. Portable SQL: runs unchanged on SQLite 3.35+ and PostgreSQL 15+ (Supabase).
-- Everything below is DERIVED: `phi_registry.py build` rebuilds it from one git commit, so it is never edited by hand
-- and can always be thrown away and rebuilt. Raw histories (trades, API caches, tapes) stay in files and local databases.
-- Conventions: ids and enums are TEXT with CHECK, times are ISO-8601 UTC TEXT or epoch BIGINT, JSON would be TEXT.

CREATE TABLE IF NOT EXISTS registry_meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS investigations (
  id          TEXT PRIMARY KEY,
  title       TEXT NOT NULL,
  state       TEXT NOT NULL CHECK (state IN ('IN_PROGRESS', 'DONE', 'PAUSED', 'ABANDONED')),
  updated_utc TEXT NOT NULL,
  origin      TEXT NOT NULL,
  version     TEXT NOT NULL,
  objective   TEXT NOT NULL,
  conclusions TEXT NOT NULL,
  limits      TEXT NOT NULL
);

-- One row per classified finding. `level` is the repository's evidence scale: CONFIRMED and SUPPORTED are facts with
-- decreasing proof, HYPOTHESIS is an interpretation, REFUTED is a kept negative result, UNRESOLVED is "not enough data".
CREATE TABLE IF NOT EXISTS findings (
  investigation_id TEXT NOT NULL REFERENCES investigations (id),
  finding_id       TEXT NOT NULL,
  level            TEXT NOT NULL CHECK (level IN ('CONFIRMED', 'SUPPORTED', 'HYPOTHESIS', 'REFUTED', 'UNRESOLVED')),
  claim            TEXT NOT NULL,
  sources          TEXT NOT NULL,
  method           TEXT NOT NULL,
  limits           TEXT NOT NULL,
  links            TEXT NOT NULL,
  PRIMARY KEY (investigation_id, finding_id)
);
CREATE INDEX IF NOT EXISTS findings_level ON findings (level);

-- Contradictions, "missing to conclude" and "prospective monitoring" bullets of each FINDINGS.md: the open work list.
CREATE TABLE IF NOT EXISTS open_items (
  investigation_id TEXT NOT NULL REFERENCES investigations (id),
  kind             TEXT NOT NULL CHECK (kind IN ('contradiction', 'missing', 'monitoring')),
  seq              INTEGER NOT NULL,
  text             TEXT NOT NULL,
  PRIMARY KEY (investigation_id, kind, seq)
);

-- Rows of EVIDENCE.md. sha256 is 64 hex, 'local_only' (not archived) or 'auto' (hash not yet filled).
CREATE TABLE IF NOT EXISTS evidence (
  investigation_id TEXT NOT NULL REFERENCES investigations (id),
  path             TEXT NOT NULL,
  sha256           TEXT NOT NULL,
  role             TEXT NOT NULL,
  PRIMARY KEY (investigation_id, path)
);

-- Full 0x addresses cited by a finding (title, sources, method, limits or links).
CREATE TABLE IF NOT EXISTS finding_addresses (
  investigation_id TEXT NOT NULL,
  finding_id       TEXT NOT NULL,
  address          TEXT NOT NULL,
  PRIMARY KEY (investigation_id, finding_id, address),
  FOREIGN KEY (investigation_id, finding_id) REFERENCES findings (investigation_id, finding_id)
);
CREATE INDEX IF NOT EXISTS finding_addresses_address ON finding_addresses (address);

-- Where an address already appears in tracked text files. scope = investigation id, 'rn:<research note>' or a top-level
-- folder. An appearance is a pointer to prior work, never a link between accounts. Large: kept local by default.
CREATE TABLE IF NOT EXISTS wallet_mentions (
  address   TEXT NOT NULL,
  scope     TEXT NOT NULL,
  files     INTEGER NOT NULL,
  first_ref TEXT NOT NULL,
  PRIMARY KEY (address, scope)
);
CREATE INDEX IF NOT EXISTS wallet_mentions_scope ON wallet_mentions (scope);

-- Registered statistical tests of the frozen studies, as they appear in the repository. Counts are lower bounds when a
-- study declares more comparisons than it archived (the study's own declaration is in `declared_comparisons`).
CREATE TABLE IF NOT EXISTS hypothesis_tests (
  study       TEXT NOT NULL,
  test_id     TEXT NOT NULL,
  description TEXT NOT NULL,
  status      TEXT NOT NULL CHECK (status IN ('confirmatory', 'exploratory')),
  n           INTEGER,
  effect      DOUBLE PRECISION,
  p_value     DOUBLE PRECISION,
  alpha_study DOUBLE PRECISION,
  declared_comparisons INTEGER,
  source_path TEXT NOT NULL,
  PRIMARY KEY (study, test_id)
);
