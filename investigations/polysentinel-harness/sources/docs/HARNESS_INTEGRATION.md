# Integrating the harness without interrupting anything

Nothing here has been done. Each step needs Benjamin's agreement, and the steps can stop at any point without touching production.

The harness never writes to production's folder or database: it reads the collector with `mode=ro`, keeps its own state, and runs under a sandbox profile that denies writes to production. So integration means starting a new service beside the existing ones. No existing service restarts, no file of `polysentinel/` or `signal_engine/` changes, and no data moves.

## Before starting

```sh
cd ~/Projects/PolySentinel-harness
sandbox-exec -D HOME="$HOME" -f deploy/deny_production.sb env SIGNAL_ENGINE_STATE=/tmp/harness-check .venv/bin/python -m unittest discover -s tests
plutil -lint deploy/com.benjamin.polysentinel-harness.plist
python3 ~/.local/lib/disk-guard/diskguard.py check --need 500M
```

Then check that production's source is the version the harness was built against, because it imports the engine from its own copy:

```sh
diff -rq --exclude=__pycache__ ~/Projects/PolySentinel/signal_engine signal_engine
diff -rq --exclude=__pycache__ ~/Projects/PolySentinel/polysentinel polysentinel
```

A difference is not a blocker, but the copy should be updated first and the tests rerun. The two copies can drift: this repository's code is a snapshot. Production has no Git repository to branch from, which remains an open decision.

## Step 1: one supervised run on real data, by hand

The collector must be in normal mode. In reduced mode the harness stops at once and says so, which is correct.

```sh
mkdir -p ~/.local/state/polysentinel-harness
cat > ~/.local/state/polysentinel-harness/config.json <<'JSON'
{"pipeline": {"warmup_rows": 200000}, "source": {"batch_rows": 5000, "batches_per_task": 2}}
JSON
sandbox-exec -D HOME="$HOME" -f deploy/deny_production.sb .venv/bin/python -m harness run --root ~/.local/state/polysentinel-harness --seconds 120
.venv/bin/python -m harness status --root ~/.local/state/polysentinel-harness
```

Check production afterwards: `launchctl list | grep polysentinel` shows the same PIDs, the collector's heartbeat keeps moving, and `metrics/runtime.jsonl` shows no change of pace.

The warm-up matters: without enough rows the engine's comparators are empty, and the verifier answers `INCOMPLETE`. Rows more than an hour behind live warm the comparators without opening cases, so a first run from cursor zero opens none until it catches up.

The defaults spend no token: `llm.enabled` is false, and so is any network use. `chain.type` is `none`, so on-chain checks stay open and no case can pass. To check receipts through public nodes, set `{"chain": {"type": "rpc"}}`; this reads `eth_getTransactionReceipt` within the daily `api_requests` budget. To trace funding, set `{"funding": {"type": "trace"}}`. Neither path has run against live nodes here.

## Step 2: the service

Needs the same command run by a person, since Claude Code's permissions refused writing to `~/Library/LaunchAgents` on 01/11:

```sh
cp deploy/com.benjamin.polysentinel-harness.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.benjamin.polysentinel-harness.plist
```

One passage every 5 minutes, each at most 240 seconds, nice 15. It stops by itself when the collector is not in normal mode, under 13.5 GB free, over its 500 MB budget, or over load 12.

To stop it, with no effect on anything else: `launchctl bootout gui/$(id -u)/com.benjamin.polysentinel-harness`. To remove it entirely, delete the plist and `~/.local/state/polysentinel-harness`. Production keeps running throughout.

## Step 3: alerts

They stay in `~/.local/state/polysentinel-harness/alerts/` as JSON. The harness sends no notification and writes to no production page. Connecting them to the dashboard would be a production change, with its own decision.

## Step 4: the model, if ever

Off by default, and it should stay off until a real run has shown that the deterministic part has run out of work.

```json
{"llm": {"enabled": true, "model": "claude-haiku-5-5", "max_usd_per_call": 0.1}, "budgets": {"llm_calls_per_day": 2, "llm_tokens_per_day": 40000, "llm_usd_per_day": 1.0}}
```

`REPRISE.md` says no paid model is authorised for the pilot, so turning this on changes that rule and is Benjamin's decision. Its calls count against the Claude Code quota.

## Step 5: moving cold data to an SSD

Only when a drive is connected, and only after a person has created its marker:

```sh
touch /Volumes/NAME/.polysentinel-archive
python -m harness.tiering plan --source ~/Projects/PolySentinel/evidence --volume /Volumes/NAME --older-days 14
python -m harness.tiering copy --source ~/Projects/PolySentinel/evidence --volume /Volumes/NAME --older-days 14 --max-bytes 1000000000
python -m harness.tiering check --volume /Volumes/NAME
```

`copy` keeps the sources. `--remove-source` deletes each source after its copy is verified, and refuses any production path: some services read `evidence/` by path, so removing those files is a decision for a person, made by hand. Each batch is safe to interrupt. Format the drive as encrypted APFS: this code does not encrypt. It refuses live SQLite files, so the collector's database stays where it is. Moving it needs the service stopped, and that is a separate migration.

## Rolling back

Remove the service and the state folder. Nothing else changed, so nothing else needs restoring.
