# Nobel 2025, strict point-in-time replay

Question, plan and amendments: [PLAN.md](PLAN.md) (committed before the results). Results: [REPORT.md](REPORT.md).

## Files

| File | What it holds |
|---|---|
| `data/strict_summary.json`, `data/strict_c4.json` | Part A: links, `C4` and `C5` with each payer read at the block of its payment; study entry ids only |
| `data/queue.json` | Part B: alerts of each class during the night of 9 to 10 October 2025, ranks, load of the seven days before |
| `data/timeline.json`, `data/group_exposure.csv`, `data/detectors.json`, `data/ext_nn.json` | Parts C and D |
| `data/machado_tape.csv`, `data/machado_yes_prices_10min.json`, `data/accounts_activity.csv`, `data/accounts_inflows.csv` | Public inputs of part C, slimmed (no profile field) |
| `data/raw_index.csv` | Every raw response used for part C: request, SHA-256, size, fetch time |
| `scripts/` | Collectors and analyses (below) |
| `verify.py` | Offline check: recomputes part C from the files above and checks parts A, B and D |

## Reproduce

Offline, from this repository alone:

```sh
python3 -I research_notes/nobel-strict-replay-2026-11-20/verify.py
```

From the sources. Parts A and B read the frozen study of 14 November 2026 on the machine that computed it
(`research_notes/realtime-intelligence-2026-11-14/study/`, its `data/` and `derived/` are not published), read-only;
nothing is written there.

```sh
N=research_notes/nobel-strict-replay-2026-11-20/scripts
STUDY=/path/to/the/frozen/study; RAW=/path/outside/the/repository
python3 -I -B $N/pit_state.py "$STUDY" "$RAW/pit"                 # archive JSON-RPC reads, resumable
python3 -I -B $N/pit_classify.py "$STUDY" "$RAW/pit/state.sqlite" "$RAW/pit/out"
python3 -I -B $N/analyse_queue.py "$STUDY" data/queue.json "$RAW/pit/out/strict_c4.json"
python3 -I -B $N/collect_event.py "$RAW/event"                    # Gamma, data API, CLOB, Polygon logs; resumable
python3 -I -B $N/analyse_timeline.py "$RAW/event" "$STUDY" data/queue.json data
python3 -I -B $N/export_public.py "$RAW/event" data
```

`pit_classify.py` stops unless its block-aware link builder, fed with the frozen description, returns exactly the
frozen study's 2,441 links and its `C4` and `C5` flags. Each script has a `selftest`.

## Limits

See REPORT.md, "Missing data" and "What this does not show". The archive endpoints answer for blocks of 2024 to 2026
today; another endpoint may serve different nodes, and every answer is kept with its endpoint in `state.sqlite`.
