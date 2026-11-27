"""What this repository has already published, read-only: investigations, findings, tables, checks and archived alerts.

Everything is read from the checkout given as `root` (see `repository_root`), with the repository's own parsers
(scripts/phi_lib.py, scripts/run_all_checks.py, scripts/build_dataset_catalog.py, loaded from their files), so this
view and the generated reports cannot disagree. It shows what the files say. It does not verify a finding again; a
file that mentions an address shows that the repository cites it, not who controls it; an archived alert is a
pattern of trades that a study's rule flagged, and comes with that study's verdict, which never supported it.

Nothing is written. The one function that runs code, `run_check`, runs only a step of the committed CI workflow.
"""
import csv
import gzip
import importlib.util
import json
import os
import shutil
import signal
import subprocess
import time
from collections import Counter
from functools import lru_cache

from . import sources
from .ledger import amount, units
from .text import clean_text

WORKFLOW = ".github/workflows/repository-integrity.yml"
CATALOG = "datasets/catalog.json"
READABLE = {"csv", "csv.gz", "tsv", "jsonl", "jsonl.gz"}
MAX_ROWS = 500
TAIL = 40
EARLY = "research_notes/early-detection-2026-11-13/study/derived"
REALTIME_ALERTS = "research_notes/realtime-intelligence-2026-11-14/data/study_export/alerts.jsonl"
REALTIME_VERDICT = "research_notes/realtime-intelligence-2026-11-14/study/derived/verdict.json"
EARLY_KINDS = ("LONELY_THIN", "LONELY", "THIN")
EARLY_FIELDS = ("initiator", "condition_id", "event_slug", "side", "t_alert", "p_alert", "lonely", "thin", "lonely_thin", "eval_set", "win")
REALTIME_FIELDS = ("population", "class", "event", "t", "price", "win")
ALERT_READING = ("An alert is a trade pattern that a frozen study's rule flagged, kept here with the outcome of its market. Neither "
                 "study found that its alerts win more often than their price implied, so an alert is not a validated signal. It "
                 "shows trades, not who is behind a wallet, and it is not evidence of inside information: public news, the "
                 "trader's own analysis, hedging, liquidity provision and chance at low prices explain the same trades.")


@lru_cache(maxsize=None)
def _script(root, name):
    """A module of scripts/, loaded from its file so that scripts/ never enters sys.path."""
    spec = importlib.util.spec_from_file_location(f"_phi_script_{name}", root / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    return limit


def _page(key, rows, limit):
    return {key: rows[:_limit(limit)], "matched": len(rows), "cut": len(rows) > limit}


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _git(root, *args):
    done = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if done.returncode:
        raise sources.SourceError(f"git {args[0]} failed: {done.stderr.decode('utf-8', 'replace')[:200]}", done.returncode)
    return done.stdout


# Investigations and findings


def investigations(root):
    """One entry per investigations/<id>/: title, state, date and the number of findings at each evidence level."""
    lib = _script(root, "phi_lib")
    out = []
    for folder in lib.investigation_dirs():
        status, found = folder / "STATUS.md", folder / "FINDINGS.md"
        fields = (lib.parse_status(status.read_text(encoding="utf-8"))[0] or {}) if status.exists() else {}
        levels = Counter(f["level"] for f in lib.parse_findings(found.read_text(encoding="utf-8"))[0]) if found.exists() else Counter()
        out.append({"id": folder.name, "title": fields.get("title"), "state": fields.get("state"), "updated_utc": fields.get("updated_utc"),
                    "findings": {**{level: 0 for level in lib.LEVELS}, **levels}, "path": f"investigations/{folder.name}",
                    "missing": [p.name for p in (status, found) if not p.exists()]})
    return out


def findings(root, text=None, level=None, investigation=None, limit=50):
    """Published findings, each with its sources, method and limits. `text` is a case-insensitive part of the claim."""
    lib = _script(root, "phi_lib")
    folders = lib.investigation_dirs()
    if level is not None and level not in lib.LEVELS:
        raise ValueError(f"level must be one of {', '.join(lib.LEVELS)}")
    if investigation is not None and investigation not in {f.name for f in folders}:
        raise ValueError(f"no investigation named {clean_text(investigation, 80)}")
    rows = []
    for folder in folders:
        path = folder / "FINDINGS.md"
        if investigation in (None, folder.name) and path.exists():
            for f in lib.parse_findings(path.read_text(encoding="utf-8"))[0]:
                if level in (None, f["level"]) and (text is None or text.lower() in f["claim"].lower()):
                    rows.append({"id": f["id"], "level": f["level"], "claim": f["claim"], "sources": f.get("Sources"), "method": f.get("Method"),
                                 "limits": f.get("Limits"), "links": f.get("Links"), "investigation": folder.name})
    return _page("findings", rows, limit)


def address_mentions(root, address, limit=200):
    """Tracked files that contain an address, any case, grouped by the investigation or note that holds them."""
    address, limit = sources._address(address), _limit(limit)
    done = subprocess.run(["git", "-C", str(root), "grep", "-l", "-z", "-i", "-F", "-e", address], capture_output=True)
    if done.returncode not in (0, 1):  # 1 is git grep's answer for no match
        raise sources.SourceError(f"git grep failed: {done.stderr.decode('utf-8', 'replace')[:200]}", done.returncode)
    paths = sorted(p for p in done.stdout.decode("utf-8").split("\0") if p)
    owner, groups = _script(root, "build_dataset_catalog").owner, {}
    for path in paths[:limit]:
        groups.setdefault(owner(path), []).append(path)
    return {"address": address, "files_total": len(paths), "cut": len(paths) > limit,
            "groups": [{"owner": k, "files": v} for k, v in sorted(groups.items())],
            "limits": "a file that contains an address shows that the repository cites it, not what it says about it nor who controls "
                      "it; compressed (.gz) and parquet files are not searched inside"}


# Checks


def _steps(root):
    """{name: (env, script)} of the offline steps of the workflow as committed at HEAD, never as edited in the tree."""
    runner = _script(root, "run_all_checks")
    found = runner.steps(runner.job(_git(root, "show", f"HEAD:{WORKFLOW}").decode("utf-8")))
    # The publication guard needs GitHub's event variables (steps() swaps it for a local form), and the final diff
    # only means something at the end of a whole run from a clean tree.
    return {name: (env, script) for name, env, script in found
            if script != runner.LOCAL_GUARD and "PUBLICATION_BEFORE" not in script and not script.startswith("git diff")}


def checks(root):
    """The offline verification steps of the CI workflow, in order: [{name, command, env}]."""
    return [{"name": name, "command": script, "env": env} for name, (env, script) in _steps(root).items()]


def run_check(root, name, timeout=600):
    """Run one step of `checks` exactly as CI does (bash -euo pipefail, from the root). Any other name is refused."""
    todo = _steps(root)
    if name not in todo:
        raise ValueError(f"not an offline step of {WORKFLOW}: {clean_text(name, 120)}")
    env, script = todo[name]
    caches, start = set(root.rglob("__pycache__")), time.monotonic()
    try:
        with subprocess.Popen(["bash", "-euo", "pipefail", "-c", script], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **env}, start_new_session=True) as proc:
            try:
                output, timed_out = proc.communicate(timeout=timeout)[0], False
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)  # the whole group: a killed bash would leave its python running
                output, timed_out = proc.communicate()[0] + f"\ntimed out after {timeout} s", True
    finally:
        for cache in set(root.rglob("__pycache__")) - caches:  # python3 -I ignores PYTHONDONTWRITEBYTECODE
            shutil.rmtree(cache, ignore_errors=True)
    return {"name": name, "passed": proc.returncode == 0 and not timed_out, "seconds": round(time.monotonic() - start, 1),
            "output_tail": "\n".join(output.splitlines()[-TAIL:])}


# Tables


def _catalog(root):
    return json.loads((root / CATALOG).read_text(encoding="utf-8"))["entries"]


def datasets(root, text=None, limit=200):
    """Entries of datasets/catalog.json whose path or owner title contains `text`, any case."""
    needle = (text or "").lower()
    return _page("datasets", [e for e in _catalog(root) if needle in e["path"].lower() or needle in (e["owner_title"] or "").lower()], limit)


def _clean(value):
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items() if k not in sources.PROFILE_FIELDS}
    return value


def _as_text(value):
    return value if isinstance(value, str) else json.dumps(value)


def query_dataset(root, path, where=None, columns=None, limit=100, max_scan=2_000_000):
    """Rows of one catalogued CSV, TSV or JSON-lines table, gzipped or not, filtered by {column: value}.

    Values are compared as text, any case (JSON values as JSON: true, null, 3.5). At most `limit` rows are returned,
    500 at most; every scanned row is counted, and `scan_complete` is False when `max_scan` stopped the reading.
    Values are as the file writes them, free text cleaned and bounded, profile fields left out.
    """
    limit, max_scan = min(_limit(limit), MAX_ROWS), _limit(max_scan)
    if not isinstance(path, str) or path.startswith("/") or ".." in path.split("/"):
        raise ValueError("path must be a repository path without '..', as datasets() lists it")
    entry = next((e for e in _catalog(root) if e["path"] == path), None)
    if entry is None:
        raise ValueError(f"not a table of {CATALOG}: {clean_text(path, 200)}")
    if entry["format"] not in READABLE:
        raise ValueError(f"{entry['format']} cannot be read with the standard library: {path}")
    if not (root / path).resolve().is_relative_to(root.resolve()):
        raise ValueError(f"{path} points outside the repository")
    asked = list(where or {}) + list(columns or [])
    if set(asked) & sources.PROFILE_FIELDS:
        raise ValueError("profile fields are never returned")
    if asked and (entry["columns"] is None or set(asked) - set(entry["columns"])):
        raise ValueError(f"columns of {path}: {entry['columns'] if entry['columns'] is not None else 'none (lines are arrays)'}")
    wanted = {k: _as_text(v).lower() for k, v in (where or {}).items()}
    rows, scanned, matched, complete = [], 0, 0, True
    with (gzip.open if path.endswith(".gz") else open)(root / path, "rt", encoding="utf-8-sig", newline="") as handle:
        if entry["format"].startswith("jsonl"):
            records = (json.loads(line) for line in handle if line.strip())
        else:
            records = csv.DictReader(handle, delimiter="\t" if entry["format"] == "tsv" else ",")
        for record in records:
            if scanned == max_scan:
                complete = False
                break
            scanned += 1
            if all(_as_text(record.get(k)).lower() == v for k, v in wanted.items()):
                matched += 1
                if len(rows) < limit:
                    rows.append(_clean({c: record.get(c) for c in columns} if columns else record))
    return {"path": path, "format": entry["format"], "owner": entry["owner"], "rows": rows, "rows_scanned": scanned, "rows_matched": matched,
            "cut": matched > len(rows), "scan_complete": complete, "limit": limit}


# Archived alerts


def alerts(root, wallet=None, condition=None, kind=None, limit=50):
    """Alerts archived by the two frozen studies, each table with its study's verdict.

    Table a (early detection, 13 November) holds one row per price ignition, with the wallet that led the buying;
    `kind` LONELY_THIN, LONELY or THIN keeps the rows of that flag. Table b (large purchases, 14 November) has no
    wallet and no condition id, only an event id; `kind` is one of its classes. A filter a table cannot honour
    leaves that table out and says why. `limit` applies to each table.
    """
    wallet = sources._address(wallet) if wallet is not None else None
    if condition is not None and not (isinstance(condition, str) and sources.HASH.fullmatch(condition)):
        raise ValueError("condition must be a 32-byte hex id")
    condition = condition.lower() if condition else None
    late = json.loads((root / REALTIME_VERDICT).read_text(encoding="utf-8"))
    if kind is not None and kind not in EARLY_KINDS and kind not in late["classes"]:
        raise ValueError(f"kind must be one of {', '.join(EARLY_KINDS + tuple(late['classes']))}")
    tables, excluded = [], []
    early_table = f"{EARLY}/analytic_table.jsonl"
    if kind is None or kind in EARLY_KINDS:
        rows = [{**{k: r[k] for k in EARLY_FIELDS}, "event_slug": clean_text(r["event_slug"], 300)} for r in _jsonl(root / early_table)
                if wallet in (None, r["initiator"].lower()) and condition in (None, r["condition_id"].lower())
                and (kind is None or r[kind.lower()])]
        tables.append({"table": early_table, "verdict": json.loads((root / EARLY / "verdict.json").read_text(encoding="utf-8")),
                       "verdict_scope": "the class LONELY_THIN on VALIDATION events; DISCOVERY rows are worked cases, never tested; LONELY "
                                        "and THIN alone are secondary tests (study/derived/results_tests.json)",
                       **_page("alerts", rows, limit)})
    else:
        excluded.append({"table": early_table, "reasons": [f"{kind} is not a class of this study"]})
    reasons = [r for r in (wallet and "its rows carry no wallet address", condition and "its rows carry an event id, not a condition id",
                           kind in EARLY_KINDS and f"{kind} is not a class of this study") if r]
    if reasons:
        excluded.append({"table": REALTIME_ALERTS, "reasons": reasons})
    else:
        rows = [{**{k: r[k] for k in REALTIME_FIELDS}, "entry_usd": amount(units(r["entry_usd"]))} for r in _jsonl(root / REALTIME_ALERTS)
                if kind in (None, r["class"])]
        tables.append({"table": REALTIME_ALERTS, "verdict": {"comparisons_on_real_data": late["comparisons_on_real_data"],
                                                            "alpha_corrected": late["alpha_corrected"],
                                                            "classes": {c: late["classes"][c] for c in sorted({r["class"] for r in rows})}},
                       "verdict_scope": "each class on the population validation_info; alerts of other populations were not tested",
                       **_page("alerts", rows, limit)})
    return {"tables": tables, "excluded": excluded, "reading": ALERT_READING}
