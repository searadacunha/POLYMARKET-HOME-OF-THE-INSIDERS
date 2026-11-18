-- PHI registry, PostgreSQL / Supabase only (the `.pg.sql` suffix keeps the SQLite loader from reading it).
-- Apply after the two portable migrations: psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f <file>, in filename order.
-- Assumes the Supabase roles anon, authenticated and service_role exist (they do on every Supabase project).
--
-- Access model, two layers as Supabase documents them (grants decide which roles reach a table, RLS decides which rows):
--   anon           nothing.
--   authenticated  read the 8 derived tables, no write, no task tables, no RPC.
--   service_role   everything (it bypasses RLS); the importer and trusted agents use it. A per-agent role is future work.
-- Task functions are SECURITY DEFINER with a pinned search_path and touch only the two task tables.

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['registry_meta', 'investigations', 'findings', 'open_items', 'evidence', 'finding_addresses',
                           'wallet_mentions', 'hypothesis_tests', 'agent_tasks', 'task_events']
  LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC, anon, authenticated', t);
    EXECUTE format('GRANT ALL ON public.%I TO service_role', t);
  END LOOP;
  FOREACH t IN ARRAY ARRAY['registry_meta', 'investigations', 'findings', 'open_items', 'evidence', 'finding_addresses',
                           'wallet_mentions', 'hypothesis_tests']
  LOOP
    EXECUTE format('GRANT SELECT ON public.%I TO authenticated', t);
    EXECUTE format('DROP POLICY IF EXISTS registry_read ON public.%I', t);
    EXECUTE format('CREATE POLICY registry_read ON public.%I FOR SELECT TO authenticated USING (true)', t);
  END LOOP;
END $$;

-- Same normalisation as phi_registry.py: lower-case, whitespace runs collapsed to one space, trimmed.
CREATE OR REPLACE FUNCTION add_task(p_kind text, p_subject text, p_priority integer DEFAULT 3, p_max_attempts integer DEFAULT 3)
RETURNS TABLE (task_id text, created boolean)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
  v_key text := lower(p_kind) || ':' || btrim(regexp_replace(lower(p_subject), '\s+', ' ', 'g'));
  v_id  text := substr(encode(sha256(convert_to(v_key, 'UTF8')), 'hex'), 1, 16);
  v_now bigint := floor(extract(epoch FROM now()))::bigint;
  v_n   integer;
BEGIN
  INSERT INTO agent_tasks (id, dedup_key, kind, subject, priority, max_attempts, created_at, updated_at)
  VALUES (v_id, v_key, lower(p_kind), btrim(regexp_replace(p_subject, '\s+', ' ', 'g')), p_priority, p_max_attempts, v_now, v_now)
  ON CONFLICT (dedup_key) DO NOTHING;
  GET DIAGNOSTICS v_n = ROW_COUNT;
  IF v_n = 1 THEN
    INSERT INTO task_events (id, task_id, at, agent, event, detail) VALUES (gen_random_uuid()::text, v_id, v_now, NULL, 'added', NULL);
  END IF;
  RETURN QUERY SELECT t.id, (v_n = 1) FROM agent_tasks t WHERE t.dedup_key = v_key;
END $$;

-- Hands out one task, or nothing. SKIP LOCKED lets concurrent callers take different rows without waiting for each other.
-- A lease that expired is taken over; a task whose lease expired after its last allowed attempt is closed as failed.
CREATE OR REPLACE FUNCTION claim_task(p_agent text, p_ttl integer DEFAULT 900)
RETURNS TABLE (task_id text, task_kind text, task_subject text, task_key text, token integer)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
  v_now bigint := floor(extract(epoch FROM now()))::bigint;
  v_id text; v_prev text; v_prev_agent text; v_kind text; v_subject text; v_key text; v_attempts integer;
BEGIN
  WITH reaped AS (
    UPDATE agent_tasks SET status = 'failed', last_error = 'lease expired after max attempts', lease_until = NULL, updated_at = v_now
     WHERE status = 'running' AND lease_until < v_now AND attempts >= max_attempts
    RETURNING id, claimed_by)
  INSERT INTO task_events (id, task_id, at, agent, event, detail)
  SELECT gen_random_uuid()::text, id, v_now, claimed_by, 'failed', 'lease expired after max attempts' FROM reaped;

  SELECT t.id, t.status, t.claimed_by INTO v_id, v_prev, v_prev_agent FROM agent_tasks t
   WHERE t.status = 'queued' OR (t.status = 'running' AND t.lease_until < v_now)
   ORDER BY t.priority, t.created_at, t.id LIMIT 1 FOR UPDATE SKIP LOCKED;
  IF v_id IS NULL THEN RETURN; END IF;

  UPDATE agent_tasks SET status = 'running', claimed_by = p_agent, lease_until = v_now + p_ttl, attempts = attempts + 1, updated_at = v_now
   WHERE id = v_id RETURNING kind, subject, dedup_key, attempts INTO v_kind, v_subject, v_key, v_attempts;
  INSERT INTO task_events (id, task_id, at, agent, event, detail)
  VALUES (gen_random_uuid()::text, v_id, v_now, p_agent, 'claimed', CASE WHEN v_prev = 'running' THEN 'taken over from ' || coalesce(v_prev_agent, '?') END);
  RETURN QUERY SELECT v_id, v_kind, v_subject, v_key, v_attempts;
END $$;

-- The token returned by claim_task fences every later call: a holder whose lease was taken over is refused.
CREATE OR REPLACE FUNCTION heartbeat_task(p_id text, p_agent text, p_token integer, p_ttl integer DEFAULT 900)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE v_now bigint := floor(extract(epoch FROM now()))::bigint; v_n integer;
BEGIN
  UPDATE agent_tasks SET lease_until = v_now + p_ttl, updated_at = v_now
   WHERE id = p_id AND status = 'running' AND claimed_by = p_agent AND attempts = p_token;
  GET DIAGNOSTICS v_n = ROW_COUNT;
  IF v_n = 1 THEN
    INSERT INTO task_events (id, task_id, at, agent, event, detail) VALUES (gen_random_uuid()::text, p_id, v_now, p_agent, 'heartbeat', NULL);
  END IF;
  RETURN v_n = 1;
END $$;

CREATE OR REPLACE FUNCTION complete_task(p_id text, p_agent text, p_token integer, p_result text DEFAULT NULL)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE v_now bigint := floor(extract(epoch FROM now()))::bigint; v_n integer;
BEGIN
  UPDATE agent_tasks SET status = 'done', result_ref = p_result, lease_until = NULL, updated_at = v_now
   WHERE id = p_id AND status = 'running' AND claimed_by = p_agent AND attempts = p_token;
  GET DIAGNOSTICS v_n = ROW_COUNT;
  IF v_n = 1 THEN
    INSERT INTO task_events (id, task_id, at, agent, event, detail) VALUES (gen_random_uuid()::text, p_id, v_now, p_agent, 'done', p_result);
  END IF;
  RETURN v_n = 1;
END $$;

-- A failure re-queues the task until its attempts are used up, then closes it as failed.
CREATE OR REPLACE FUNCTION fail_task(p_id text, p_agent text, p_token integer, p_error text)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE v_now bigint := floor(extract(epoch FROM now()))::bigint; v_status text;
BEGIN
  UPDATE agent_tasks SET status = CASE WHEN attempts < max_attempts THEN 'queued' ELSE 'failed' END,
         last_error = p_error, lease_until = NULL, claimed_by = NULL, updated_at = v_now
   WHERE id = p_id AND status = 'running' AND claimed_by = p_agent AND attempts = p_token
  RETURNING status INTO v_status;
  IF v_status IS NOT NULL THEN
    INSERT INTO task_events (id, task_id, at, agent, event, detail)
    VALUES (gen_random_uuid()::text, p_id, v_now, p_agent, CASE WHEN v_status = 'queued' THEN 'requeued' ELSE 'failed' END, p_error);
  END IF;
  RETURN v_status;
END $$;

DO $$
DECLARE f text;
BEGIN
  FOREACH f IN ARRAY ARRAY['add_task(text, text, integer, integer)', 'claim_task(text, integer)',
                           'heartbeat_task(text, text, integer, integer)', 'complete_task(text, text, integer, text)',
                           'fail_task(text, text, integer, text)']
  LOOP
    EXECUTE format('REVOKE ALL ON FUNCTION public.%s FROM PUBLIC, anon, authenticated', f);
    EXECUTE format('GRANT EXECUTE ON FUNCTION public.%s TO service_role', f);
  END LOOP;
END $$;
