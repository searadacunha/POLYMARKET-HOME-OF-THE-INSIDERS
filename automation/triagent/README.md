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
| Grok Build CLI 1.0.13 | Installed; headless call answers "Not signed in" (`grok login` needed once) |
| "Grok Bot.app" on this Mac | Bundle `com.anysphere.sand`, not an xAI app; not used |
| Grok Bot webhook routine | Callback endpoint and authentication tested locally; not connected: it needs a public HTTPS URL |
| Prospective detector backtest | Harness and leak tests only; not run on labelled cases |

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
- No trading, wallet keys or identity attribution; nothing pushes, merges or opens a PR. Development missions
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

## Tests

`triagent test` (or `python -m unittest discover -s tests -t .` here): the Claude -> OpenAI -> Grok -> OpenAI ->
Claude chain, fresh context per mission, deduplication, bounded depth and children, persistence and migrations,
recovery of interrupted, finished and live missions, budgets, pause and kill switch, missing and expired
credentials, the Codex CLI reviewer against a stand-in binary (expired login, usage limit, timeout, missing binary,
stale or truncated answers, `chatgpt_gui` never running), uncertain calls, authenticated callbacks and replays, a missing Grok result, refusals and invalid
schemas, secret redaction, the publication guard, tool confinement, evidence hashing and tampering, divergent
verdicts, real payload shapes (`tests/fixtures`), pagination, checkpoints, malformed rows, reorgs, service
labels and leak-free backtests.
