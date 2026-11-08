# Polymarket TriAgent

An autonomous, read-only research loop for this repository's Polymarket investigations. Claude Code does the
on-chain forensics, OpenAI directs the programme and tries to refute every result, and Grok searches historical
X posts. A collector watches the public Polymarket trade feed and opens a mission when a new account shows
several preparatory signals at once. Everything runs as a macOS user service and keeps its memory in SQLite,
outside every model's conversation.

Selection signals are not evidence of insider trading, and a score is a count of flags, not a probability.

## Verified state (2026-11-07)

| Part | State |
|---|---|
| Supervisor, queue, recovery, budgets, kill switch, local page | Running under launchd on the owner's Mac (live mode) |
| Polymarket collector (Data API v2 global large-trade feed, `/v2/activity`, Polygon receipts) | Working on production data |
| Claude Code missions (fresh headless session each, subscription login) | Working: a real alert mission completed (27 turns, 4.4 min, 14/14 cited sources verified) |
| OpenAI director and auditor, `OPENAI_MODE=codex_cli` (Codex CLI on the ChatGPT subscription, strict JSON schema) | Working without an API key: a real review of the finished Claude mission (57 s, verdict stored, request id and SHA-256 checked) and a real plan that queued a new Claude mission, which the service then started on its own |
| OpenAI through the Responses API (`OPENAI_MODE=api`) | Code and tests only: no `OPENAI_API_KEY` |
| ChatGPT GUI / in-app browser (`OPENAI_MODE=chatgpt_gui`) | Blocked, not implemented (see below) |
| Grok via xAI API with X Search | Code and tests only: no `XAI_API_KEY` yet |
| Grok Build CLI 1.0.77 (`GROK_MODE=grok_cli`, grok.com login) | Working since 2026-11-08: a real X-research mission started by n8n (312 s) returned 8 posts, all re-read by the supervisor through X's public embed endpoint (author and time to the second), then a Codex review. Runs with an empty HOME and TriAgent's own `GROK_HOME` (no owner settings, rules, plugins, MCP or always-approve), tools limited to web search and fetch. The CLI has no X search tool of its own |
| "Grok Bot.app" on this Mac | Bundle `com.anysphere.sand`, not an xAI app; not used |
| Grok Bot webhook routine | Callback endpoint and authentication tested locally; not connected: it needs a public HTTPS URL |
| Prospective detector backtest | Harness and leak tests only; not run on labelled cases |
| n8n 2.46.6 (`com.benjamin.triagent-n8n`, code in `~/.local/lib/triagent-n8n` since 2026-11-08) and workflow `TriAgentV2Wake01` | Active since 2026-11-07 21:12 UTC with `ORCHESTRATOR=n8n`: the historical scheduler is off. Real chain observed: wake -> Claude mission (280 s) -> `mission.completed` -> Codex review in a fresh session (143 s); and wake -> Codex plan (35 s) -> 2 new missions -> n8n started the first one |
| Shadow record of new accounts and first payers (`ACCOUNTS_SHADOW=1`) | Recording since 2026-11-07; never alerts; funding bursts shown on the page only |
| Investigation center on 8790 (reports, daily digest, notifications, commands) | See below; tested on a copy of the live database (9 reviews reported, existing tables unchanged) |

## How it works

```
Polymarket feed ──> collector ──> point-in-time flags ──> alert ──┐
                                                                  v
repository inventory ──> OpenAI planner ──> mission queue (SQLite WAL)
                                   ^              │
                                   │              ├─> Claude Code: new headless session, read-only tools
                                   │              └─> Grok: xAI X Search | Grok CLI | Grok Bot webhook
                                   │                         │
                                   └── OpenAI review <───────┘  result stored first, then reviewed
                                        tiers, novelty, falsifiers, at most 2 follow-ups or "stop"
```

1. Every mission gets a folder with `MISSION.md`: the task, the falsifier to attempt, the rules, what earlier
   missions of the same investigation established, the full results of its lineage in `context/`, and the
   inventory of investigations already in the repository (including open PR branches). Its SHA-256 is stored.
2. Claude runs in a new session (`--session-id`, `--no-session-persistence`, never `--resume`), in
   `--safe-mode` with the subscription login or `--bare` with an API key, `--restricted`, `--permission-mode
   dontAsk`, with Read/Glob/Grep and one Bash command: `tg-fetch`.
3. `tg-fetch` is the only network access: GET on an allowlist of public hosts and read-only JSON-RPC methods
   (Polygon, Ethereum, Base, Arbitrum, Optimism, BSC, Solana). Each response is archived under its SHA-256 in the
   mission's `evidence/`, so a report can cite primary sources the supervisor re-checks byte for byte.
4. The raw result is saved before any review. The supervisor then runs deterministic checks (cited evidence ids
   exist and are unchanged; reported Polygon transfers are replayed against their receipt) and sends the report,
   the checks, the investigation memory and the inventory to OpenAI with a strict schema.
5. The reviewer assigns tiers (CONFIRMED needs a verified primary transaction), scores novelty, lists
   alternative explanations and falsification tests, and returns at most two follow-ups or a stop decision.
   Follow-ups need novelty >= 3; depth is capped; two low-novelty reviews in a row close the investigation.
6. Every 12 h the planner reads the inventory, open questions, alerts and closed investigations and proposes at
   most three new missions, or none with a reason.

## Polymarket surveillance

- **Trades:** `GET /v2/trades?filter_type=CASH&filter_amount=5000&taker_only=false` (global feed, newest first,
  cursor pagination, checkpoint with a 5-minute overlap, bounded backfill after sleep with a logged gap warning,
  deduplication on the fill key). About 470 fills of at least 5,000 USDC in 4 hours on 2026-11-07.
- **Accounts:** `/v2/activity?user=…&start=1&sort_direction=ASC&exclude_deposits_withdrawals=false&limit=1000`.
  Names, pseudonyms, bios and images are dropped on reception.
- **Funding and exits:** the Polygon receipt of each DEPOSIT and WITHDRAWAL row. The payer is found inside that
  one transaction, walking back through relay contracts that pass the same amount (deposit wallet, on-ramp);
  equal amounts are never matched across transactions. Receipts are archived; edges are stored with the transaction.
- **Services:** Blockscout's public name tags (chain 137) mark bridges, pools and exchanges (e.g. "Relay: Solver",
  "UniswapV3Pool"). A tagged address never produces a link flag; if tags are unavailable, link flags are off.
- **Reorgs:** a trade raises nothing until its transaction has a successful receipt 64 blocks deep; a trade
  without a receipt is marked `missing` and ignored.
- **PolyBolt** streams reference prices only and needs CLOB credentials: it carries no trade tape, so the feed is
  polled. The first order *submission* is not observable here; the earliest observable event is the first fill.

Flags, computed only from data before the trade (`triagent/detector.py`): `NEW_WALLET` (< 7 days),
`FRESH_FUNDING` (< 24 h), `FEW_PRIOR_TRADES` (< 5), `CONCENTRATED` (trade >= half the deposits),
`SHARED_FUNDER`, `SHARED_DESTINATION` (not services, fan-out <= 25), `COORDINATED_ENTRY` (2+ other new accounts on
the same outcome in 6 h), `KNOWN_INFRA_REUSE` (address in an earlier investigation), `LIQUIDITY_SHARE` (live
only). Three flags open an alert; at most two alert missions a day.

## Prospective detection

`triagent backtest cases.csv` evaluates the flags on labelled cases (`address,t,label,event_ts,trade_usdc`):
features see only rows before each case's `t` (`AsOf` raises on any later row), the threshold is chosen on
cases before the split and applied unchanged after it, and the output gives precision, recall, false positives
per 1,000 accounts, median lead time, the number of configurations tried (for Bonferroni) and a placebo test on
shifted decision times. `labels_sufficient` stays false below 20 positives and 200 controls after the split.
No labelled evaluation has been run yet: the repository's cases first need verified decision times and
representative controls.

## Financial graph

Edge kinds: `DIRECT_TRANSFER`, `SAME_FUNDER`, `SAME_DEPOSIT_ADDRESS`, `BRIDGE_ORDER`, `SHARED_SERVICE`,
`TEMPORAL_CORRELATION`, `HYPOTHESIS`. Levels: `receipt_verified` (a matching log in the archived receipt),
`agent_reported`, `derived`, `hypothesis`. Each edge keeps chain, transaction, token, raw amount, time, method
and evidence hash. An exchange address is a destination of funds, not an identity.

## Install and commands

```sh
sh automation/triagent/install.sh          # code -> ~/.local/lib/triagent, state -> ~/.local/state/triagent
triagent doctor --online                   # environment, credentials (names only), connectivity
triagent start | stop | restart | status | logs [-f] | pause | resume | kill | test
triagent retry <job_id>                    # requeue a blocked or failed mission (operator decision)
triagent inventory                         # rebuild the inventory of earlier investigations now
```

Local page: <http://127.0.0.1:8790/> (bound to 127.0.0.1, Host header checked, all data rendered as text).

Configuration: `~/.config/triagent/config.env` (`config.example.env`). Secrets: `~/.config/triagent/secrets.env`
(mode 600; `secrets.example.env`): read by the supervisor only, never placed in a prompt, a mission environment
or a log. `RUN_MODE=dryrun` calls no provider and replaces each with a deterministic fake.

The service runs only while the Mac is awake and the user is logged in; it does not change sleep settings.
After sleep, the collector backfills the gap up to `BACKFILL_MAX_PAGES` pages and logs any remaining gap.

## Reliability

Statuses: `queued`, `running`, `awaiting_external_result`, `reviewing`, `done`, `failed`, `blocked`, `paused`.
Claude missions run in their own process group and write to files, so a supervisor restart neither kills them nor
loses their result: a live mission is adopted, a finished one collected, and one that died without a result is
`blocked` (the provider may have billed it) until `triagent retry`. A synchronous Grok call interrupted mid-way
is `blocked` for the same reason; an uncertain HTTP outcome (timeout, 5xx after sending) is never retried
blindly. Missing or expired credentials, rate limits and daily budgets put the provider on hold and leave jobs
queued or reviewing. A Grok Bot webhook acknowledgement only starts the job: without an authenticated callback
(secret + one-time nonce) before the deadline, the job fails. One Claude mission at a time; per-provider daily
caps on spend and calls; missions and collection stop below `DISK_MIN_FREE_GB` (13.5) free. `triagent kill`
writes a kill file, stops running missions and the service; `triagent start` clears it. The database is
checked at start-up and backed up daily (7 kept).

## Security

- Measured on 2026-11-07 with Claude Code 2.1.319: in `dontAsk` mode Claude Code still auto-approves some
  read-only git commands inside the working directory; explicit deny rules win, so every git subcommand that
  could reveal a credential or reach a remote is denied. Reads outside the mission folder, the research checkout
  and the branch-report copies are refused, and so are `curl`, `python`, file writes and `git push`.
- Content from X, GitHub, APIs and earlier agents is untrusted data; the director prompt says so and the page
  renders it as text.
- No trading, wallet keys or identity attribution; nothing merges. Only `publish.py` pushes, and only a
  `triagent/campaign-*` research branch (normal push, after every repository check) with its draft PR. Development missions
  edit only their own sparse worktree and branch `triagent/dev-<id>`, committed locally and never pushed.
- The research context is a sparse, detached checkout of `origin/main` (reports, code, manifests; about 15 MB);
  raw investigation data stays out of it.

## Connecting the remaining agents

- OpenAI without an API key: `OPENAI_MODE=codex_cli` in `config.env` (signed in once with `codex login`, ChatGPT
  plan), `triagent doctor`, `triagent restart`. This is the Codex CLI, not the ChatGPT browser; the page says so.
- OpenAI through the API instead: `OPENAI_MODE=api` and `OPENAI_API_KEY` in `secrets.env`. No mode ever falls back
  to another: a failing mode puts the reviewer on hold and keeps the results waiting.
- Grok through the API: `XAI_API_KEY` in `secrets.env` (`GROK_MODE=xai_api`).
- Grok Build CLI instead (no key): `grok login` once in a terminal, then `GROK_MODE=grok_cli`. The CLI's own default
  model is used unless `GROK_CLI_MODEL` is set (`grok models` lists them; `XAI_MODEL` is the API's).
- Grok Bot: `GROK_MODE=bot`, the routine's webhook URL and key, a public HTTPS URL that forwards only
  `/api/grok-complete` to this Mac, and `GROK_CALLBACK_SECRET` stored in the routine's secret manager. The routine
  must POST `{job_id, nonce, summary, leads, unresolved, proposed_tests}` with `Authorization: Bearer <secret>`.

### Codex CLI reviewer (`OPENAI_MODE=codex_cli`)

Each review or plan is one `codex exec` run: a new ephemeral session, read-only sandbox, `--ignore-user-config`
(the owner's `~/.codex/config.toml` routes Codex to another provider; authentication still comes from the
ChatGPT login), and shell, code execution, sub-agents, plugins, memories, hooks and web search disabled. Measured
on 2026-11-07 with codex-cli 0.166.0: with these flags a session could not read a canary file in its own folder.
The prompt asks for a one-time `request_id`; an answer that does not echo it, fails the strict schema or is
truncated is rejected and counted as a failed attempt (three attempts, then the job is blocked). Prompt, event
stream and answer are kept under `missions/<job>/reviews/<request_id>/` (plans under `plans/reviews/`) and their
SHA-256 values are stored with the verdict (`review_json._provider`). Expired login, usage limits, timeouts and
a missing binary put the reviewer on hold; the result waits in `reviewing`. Calls are counted against
`OPENAI_MAX_CALLS_DAY` at $0 (subscription). One review runs at a time, in the supervisor's agent loop.

### ChatGPT GUI (`OPENAI_MODE=chatgpt_gui`): blocked, not implemented

Checked on 2026-11-07 on the owner's Mac (ChatGPT.app 26.1027.61615, bundle `com.openai.codex`):

- OpenAI's Terms of Use forbid automatically or programmatically extracting data or Output from the service.
  Driving the ChatGPT window, or chatgpt.com in another browser, to send prompts and read answers is that.
- The app's in-app browser is controlled by the agent running inside the app (its bundled `browser` plugin, an
  internal Node REPL RPC and a peer-authorization module). The app has no AppleScript dictionary, no Shortcuts or
  App Intents action and no documented external interface for it.
- The running instance on this Mac is started by claude-code-router with its Codex app server routed to that
  router, so its Codex threads do not reach OpenAI at all.
- Accessibility control would need a permission over every app, and a launchd job has no screen once the
  session is locked.

The mode is accepted in `config.env` only so that the choice is explicit: it never sends anything and holds the
reviewer with this reason.

## Investigation center (port 8790)

The local page is a research center grouped by investigation, not by agent: Home (what changed since the last
visit, latest finding, items needing attention, running missions, health of n8n, Codex, Claude, Grok and the
collectors), Investigations (one page per investigation: successive missions as a tree, conclusions, refuted
hypotheses, open questions, sources with SHA-256, wallets, links, next missions; the repository's own dossiers
from the inventory, read-only), Early alerts, Financial networks (SVG graph: direct transfers, shared funding,
exchanges, bridges, shared services and hypotheses differ by color and line pattern, verified links are thicker;
each link opens its transactions and archived evidence), Agents, Reports, Commands, Settings and Raw data. Every
view is a query on the SQLite memory above (`triagent/center.py`); no view calls a model, so the page works while
every agent is down. All text from agents, X and APIs is inserted as text, under a nonce-based CSP.

- **Mission reports.** When GPT's review of a mission is stored, `triagent/reports.py` writes the standard report
  (French headings: investigation, summary of at most 150 words, new findings, financial links, refuted
  hypotheses, uncertain points, importance, GPT decision, next missions with their falsifier, sources with
  transaction ids and SHA-256). It restates the stored review, the deterministic checks and the rows they point
  to; nothing is generated by a model. A mission with no established new fact says so. Rows go in `reports`
  (id `RPT-<date>-<job>-v<n>`, version, date, SHA-256 of the body, unique per review digest, so a restart adds
  nothing); reviews made before this feature are reported once by the maintenance tick. Export: Markdown.
- **Daily digest** at `DAILY_REPORT_TIME` in `DAILY_REPORT_TZ` (19:00 Europe/Lisbon, editable in Settings): only
  what happened since the previous digest, built from stored reviews, never a new GPT session.
- **Notifications** (macOS; a click opens the page when `terminal-notifier` is installed, otherwise the link is in
  the text): major report, receipt-verified link reported by a mission, mission blocked for
  `BLOCKED_NOTIFY_AFTER_S`, provider not signed in, orchestration stopped (an operator pause excluded). Deduplicated
  by key, `NOTIFY_MAX_DAY` per day, `NOTIFY_COOLDOWN_S` per kind, never in dry run, never for rows older than the
  install. Early alerts keep their own path and thresholds (`/v1/alerts/notify`), now with a link to the alert.
- **Commands**: submit an idea to the GPT director (one fresh planning session, leased by n8n like any GPT task;
  missions are filed under the idea's investigation), pause or resume, change the settings above. Each command
  needs the operator token (`UI_TOKEN`, generated by `install.sh`; `triagent ui-token` copies it for the Settings
  page, where it stays in the browser's local storage), a same-origin request and a JSON body; refusals and
  accepted commands are logged as `operator` events. No trading, keys or merges exist anywhere in the API.

Migration 5 adds only `reports`, `notifications` and `ideas`; preferences live in `kv` (`pref.<KEY>`).

## Historical campaign (persistent, until saturation)

`triagent campaign start` turns the programme into a campaign that survives restarts and new AI sessions: every
step reads and writes SQLite (migration 6: `leads`, `searches`, `passes`, `publications`), never a conversation.

```
coverage grid (8 topics x 5 periods) ──> Grok, one cell per fresh session ──> supervisor re-reads each post (X embed)
      ^                                                                              │ one lead per dedup key
      │ two full passes without a significant result = saturation                     v
      │                                         GPT triage (fresh session, short context from SQLite, 12 leads)
      │                                          investigate │ X follow-up (once) │ duplicate │ close │ defer │ gaps
      │                                                      v
      │                       Claude mission (fresh session, before / during / after checklist) ──> GPT review
      │                                                      v
      └──────── lead settled (confirmed / supported / refuted / unresolved) ──> significant? ──> GPT audit
                                                                                               v (evidence gate)
                                       isolated branch + note + every repository check ──> draft PR (never merged)
```

- **Leads.** One row per checkable claim, with id `L-<hash>`, a unique dedup key (`x:<post id>`, `addr:<address>`,
  `case:<file>#<id>`, `gap:<key>`), kind, topic and period, state (`new`, `deferred`, `investigating`, `confirmed`,
  `supported`, `refuted`, `unresolved`, `closed`, `duplicate`), owner, priority, sources (URL, post id, public author,
  UTC time, re-read result), addresses, transactions, hypothesis, checks needed and closure reason. `campaign start`
  registers the repository's 48 inventoried investigations as closed known cases (the memory against repetition) and
  the leads of its intake notes (X history, corpus reconciliation, external cases, KPMG/election intake), closed
  when the repository already settled them.
- **Grok.** One cell (`<topic>:<period>`, recent periods first) at a time, in twelve languages, posts already
  registered for the cell excluded, at most 15 original posts. A cell is not sent to the generic GPT review: the
  supervisor re-reads each post, then registers it (a post that does not exist or whose author differs is closed at
  once). Addresses already in the repository are flagged for the triage. In `grok_cli` mode only
  `GROK_MAX_MISSIONS_DAY` limits the pace (the CLI's dollar figure is an estimate on the grok.com plan).
- **GPT triage** (`triage`, leased by n8n like any GPT task). Scores nine criteria 0-5 (source quality, verifiable
  transactions, amount, unusual timing, financial connections, originality, refutability, value for the detector,
  cost); the priority is computed from them by fixed weights, not chosen by GPT. Decisions are applied once per lead;
  a lead GPT omits is deferred, a lead gets one X follow-up at most, a reused novelty key closes the lead instead of
  duplicating a mission. GPT may add two repository gaps per session. A failed session waits an hour.
- **Claude.** The existing mission, with the before / during / after checklist and the rule that a direct transfer,
  a bridge order, an exchange deposit and a correlation are separate edges. The existing GPT review follows.
- **Settlement.** When an investigation has nothing pending, its lead takes the best tier of its claims. It is
  significant when supported or confirmed with novelty >= 3, or when it has a receipt-verified link; only then is a
  publication audit queued. A mission that fails without a review settles its lead as unresolved.
- **Audit and publication.** GPT audits the whole dossier (`audit`); a claim is kept only when every evidence id is
  archived by this investigation. `publish.py` (no model) builds `research_notes/triagent-campaign/<lead>/` (REPORT
  with a Mermaid flow graph, CLAIMS, TIMELINE with phases, ADDRESSES, FLOWS, POSITIONS, RECONCILIATION, SOURCES with
  SHA-256, DETECTOR_SIGNALS, meta, and an offline `verify.py`) on branch `triagent/campaign-<lead>` from a fresh
  `origin/main` (or the branch with `origin/main` merged), runs `check_publication --target main --candidate HEAD
  --base-ref origin/main`, `test_publication`, `test_phi`, `test_integrity_regressions`, `test_parallel_publication`,
  `validate_evidence`, `build_master_report --check`, the Relay `verify.py`, `check_research_links` and the note's
  `verify.py`; only when all pass does it push normally and open or update one draft PR (`PUBLISH_MAX_OPEN` at a
  time). Raw API pages (which carry account names and bios) are listed by URL and SHA-256, never copied; chain
  receipts of verified flows are. A secret pattern refuses the publication. Merged or closed PRs are recorded.
- **Passes and saturation.** A pass ends when every cell has been searched and nothing is pending; deferred leads get
  one more triage per pass. Two consecutive passes without a significant result set the state `saturated`, write
  `~/.local/state/triagent/campaign/COVERAGE_REPORT.md` and notify « Campagne historique arrivée à saturation — bilan
  disponible ». `triagent campaign reopen` starts one more pass (a new source or method). Saturation means the
  defined sources and leads were examined without a sufficiently relevant new result, not that every case was found.
- **Detector preparation.** `triagent campaign dataset` writes every dated link of a campaign case with its phase:
  A before the first bet, B between entry and event, C after (from timestamps only; C never stands for A). No model
  is calibrated or enabled; labels are lead states, not proof.
- **Page.** « Campagne historique » on 8790: progress, coverage matrix, leads by state, active cases, re-read X
  sources, new receipt-verified links, publications, blockages, searches, yield per pass, next missions, saturation.

Commands: `triagent campaign start | stop | status | reopen | report | dataset`.

## n8n orchestration (V2, event-driven)

`n8n/TRIAGENT_N8N_ADAPTIVE_V2.json` (from PR 51, unchanged) is driven by the broker in `triagent/broker.py`. Two
speeds: the collector keeps polling the public feed on its own (60 s, 15 s while it has a backlog, `/v2/status`
lag recorded with each alert); provider work starts only from n8n, on an event or on its 15-minute recovery timer.

| Endpoint (POST, header `X-TriAgent-Key`) | Behaviour |
|---|---|
| `/v1/events/ingest` | Records `event_id` once; a replay returns `duplicate: true` and never re-notifies |
| `/v1/work/lease` | Under one lock: gate (kill switch, pause, disk), holds, daily caps, provider availability, one session per provider; single-use lease, 120 s. GPT audits of stored results first, then Claude, Grok, then the budgeted periodic plan |
| `/v1/work/dispatch` | Consumes the lease, starts the process or thread, answers 202 at once; fresh session only |
| `/v1/work/reconcile` | Process table and files only, never a model: finished missions, expired leases, lost threads, `suspected_stalled` label after `STALL_AFTER_S` without file progress (never a kill: only the hard timeout stops a mission) |
| `/v1/work/reject` | Blocks the job with the reason instead of dropping it |
| `/v1/alerts/notify` | One macOS notification per alert with a dossier in `alerts/alert-<id>.md`: `ALERT_NOTIFY_MIN_FLAGS` (4), 6 per day, 6 h per account, never in dry run |

The supervisor emits `work.ready`, `mission.completed`, `mission.failed`, `alert.early` and `provider.blocked`
into the `bus` table; a sender posts them to `N8N_WAKE_URL` with header `X-TriAgent-Wake` and backs off while n8n
is down. Durations are recorded per provider and task type (`runs`); P50/P90 are shown from 5 runs, P99 from 30,
and below that the configured hard timeout is the only bound. Alerts are WATCH (3-4 flags) or HIGH (5+), first
NOT VERIFIED, then `reviewed` once their mission has been audited. The notification threshold of 4 flags was
chosen on the observed alert load (2 of 15 alerts among 426 wallets on 2026-11-07), not calibrated.

`ORCHESTRATOR=internal` (default) keeps the historical 10 s scheduler and makes the broker refuse every lease, so
two schedulers never run together. `ORCHESTRATOR=n8n` turns that scheduler off and keeps the collector, process
watch, recovery and maintenance.

Install (needs the disk guard to accept about 3.8 GB): `sh n8n/install_n8n.sh` installs n8n 2.46.6 on Node 24 in
`~/.local/lib/triagent-n8n`, data in `~/.local/state/triagent-n8n`, LaunchAgent `com.benjamin.triagent-n8n`,
loopback only, telemetry off, Execute Command, SSH, file and git nodes excluded, and imports the two header
credentials and the workflow INACTIVE (`n8n/prepare_workflow.py` adds the credential references; the template
is not modified and no secret enters a JSON file of the repository). With `N8N_IMAGE=<path>.sparsebundle` the
code lives in that disk image instead (mounted hidden at `/Volumes/TriAgent-n8n`, attached by the launcher when
missing, launchd retrying every 5 minutes while the disk is absent); the n8n database and log stay internal.
On the owner's Mac the code first lived in `/Volumes/VERBATIM HD/TriAgent-n8n.sparsebundle` (2026-11-07, internal
disk at its floor); that USB disk dropped twice on 2026-11-08 and n8n stopped with it, so the code moved to the
internal default location the same morning, once space allowed. While n8n is down, events wait with backoff, early alerts are notified by the broker itself, and
with `ORCHESTRATOR=n8n` no mission starts. Activation, after the checks: stop n8n,
activate workflow `TriAgentV2Wake01` with the n8n CLI, set `ORCHESTRATOR=n8n`, `triagent restart`, start n8n.
Rollback: `ORCHESTRATOR=internal`, `triagent restart`, stop the n8n agent.

## Tests

`triagent test` (or `python -m unittest discover -s tests -t .` here): the Claude -> OpenAI -> Grok -> OpenAI ->
Claude chain, fresh context per mission, deduplication, bounded depth and children, persistence and migrations,
recovery of interrupted, finished and live missions, budgets, pause and kill switch, missing and expired
credentials, the Codex CLI reviewer against a stand-in binary (expired login, usage limit, timeout, missing binary,
stale or truncated answers, `chatgpt_gui` never running), uncertain calls, authenticated callbacks and replays, a missing Grok result, refusals and invalid
schemas, secret redaction, the publication guard, tool confinement, evidence hashing and tampering, divergent
verdicts, real payload shapes (`tests/fixtures`), pagination, checkpoints, malformed rows, reorgs, service
labels and leak-free backtests. `tests/test_broker.py`: idempotent ingest, eight concurrent wakes starting one
job, single-use and expiring leases, the Claude -> GPT -> Grok -> GPT -> Claude chain through leases, 202 before a
slow review ends, simulated 5/20/90-minute missions never relaunched, restart adoption, unavailable Grok, holds,
caps and disk gate, durations, one notification per alert, a later withdrawal never entering a pre-trade alert,
the event sender, loopback header authentication and size limit, and the workflow contract. `tests/test_center.py`:
reports after review (mandatory sections and order, SHA-256, version), a mission without discovery, no duplicate
after restart, backfill, agent text unable to forge a heading, the daily digest (once per day, only the new period,
no model call, settings), notifications (dedup, quota, cooldown, link, never for the backfill, a pause is not a
blockage, dry run), isolation between investigations, every view with every agent down, the idea flow through the
broker, authenticated commands, the CSP nonce, no HTML sink in the page, and migration 5 leaving existing rows
untouched.
