"""triagent start|stop|restart|status|doctor|logs|test|pause|resume|kill|retry|run|inventory|backtest"""
from __future__ import annotations

import csv
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import config as config_mod
from . import detector, inventory, polymarket
from .config import CODE_DIR
from .store import Store, now
from .util import ProviderError, get_json, http

LABEL = "com.benjamin.triagent"
PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"


def launchctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["launchctl", *args], capture_output=True, text=True)


def domain() -> str:
    return f"gui/{os.getuid()}"


def service_state() -> dict:
    out = launchctl("print", f"{domain()}/{LABEL}")
    if out.returncode != 0:
        return {"loaded": False}
    info = {"loaded": True}
    for line in out.stdout.splitlines():
        line = line.strip()
        for key in ("state", "pid", "last exit code", "runs"):
            if line.startswith(key + " ="):
                info[key] = line.split("=", 1)[1].strip()
    return info


def cmd_start(cfg, _args):
    if cfg.kill_file.exists():
        cfg.kill_file.unlink()
        print("kill switch removed (explicit start)")
    if not PLIST.is_file():
        sys.exit(f"{PLIST} missing: run install.sh first")
    if not service_state()["loaded"]:
        r = launchctl("bootstrap", domain(), str(PLIST))
        if r.returncode != 0:
            sys.exit(f"launchctl bootstrap failed: {r.stderr.strip()}")
    launchctl("kickstart", f"{domain()}/{LABEL}")
    time.sleep(2)
    print(json.dumps(service_state()))


def cmd_stop(cfg, _args):
    r = launchctl("bootout", f"{domain()}/{LABEL}")
    print("stopped" if r.returncode == 0 else f"not running ({r.stderr.strip()})")
    running = Store(cfg.db_path).jobs("status='running'")
    if running:
        print(f"{len(running)} Claude mission(s) keep running and will be adopted at next start; "
              "`triagent kill` stops them too.")


def cmd_restart(cfg, args):
    if not service_state()["loaded"]:
        return cmd_start(cfg, args)
    launchctl("kickstart", "-k", f"{domain()}/{LABEL}")
    time.sleep(2)
    print(json.dumps(service_state()))


def cmd_status(cfg, _args):
    store = Store(cfg.db_path)
    st = service_state()
    health = None
    try:
        _, raw = http(f"http://127.0.0.1:{cfg.get('HTTP_PORT')}/health", timeout=3,
                      headers={"Host": f"127.0.0.1:{cfg.get('HTTP_PORT')}"})
        health = json.loads(raw)
    except ProviderError as exc:
        health = {"error": str(exc)[:120]}
    day = now() - now() % 86400
    holds = {p: json.loads(store.get_kv(f"hold_{p}") or "{}") for p in ("claude", "openai", "xai")}
    print(json.dumps({
        "service": st, "health": health, "mode": cfg.get("RUN_MODE"), "paused": store.get_kv("paused") == "1",
        "kill_switch": cfg.kill_file.exists(), "jobs": store.counts(),
        "last_collect_ok": store.get_kv("last_collect_ok"), "collector_last": store.get_kv("collector_last"),
        "alerts": store.query("SELECT count(*) n FROM alerts")[0]["n"],
        "spend_today": {p: store.spent(p, day) for p in ("claude", "openai", "xai")},
        "holds": {p: h for p, h in holds.items() if h and h.get("until", 0) > now()},
        "ui": f"http://127.0.0.1:{cfg.get('HTTP_PORT')}/",
    }, indent=1, default=str))


def run_quiet(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, str(exc)


def cmd_doctor(cfg, args):
    checks: list[tuple[str, bool, str]] = []

    def add(name, ok, detail=""):
        checks.append((name, bool(ok), str(detail)[:300]))
    add("macOS", platform.system() == "Darwin", f"{platform.mac_ver()[0]} {platform.machine()}")
    add("python >= 3.11", sys.version_info >= (3, 11), sys.executable + " " + platform.python_version())
    add("git", shutil.which("git"), run_quiet(["git", "--version"])[1])
    code, out = run_quiet([cfg.get("CLAUDE_BIN"), "--version"])
    add("claude code", code == 0, out)
    if cfg.get("CLAUDE_AUTH") == "api":
        add("claude auth (api key, --bare)", cfg.secret("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY present" if cfg.secret("ANTHROPIC_API_KEY") else "missing")
    else:
        code, out = run_quiet([cfg.get("CLAUDE_BIN"), "auth", "status"])
        logged = '"loggedIn": true' in out
        add("claude auth (subscription, --safe-mode)", logged, "logged in" if logged else out[:120])
    code, out = run_quiet([cfg.get("GROK_BIN"), "--version"])
    add("grok cli (optional)", code == 0, out)
    if cfg.get("GROK_MODE") == "grok_cli":
        code, out = run_quiet([cfg.get("GROK_BIN"), "models"], 30)
        add("grok cli auth", "not authenticated" not in out.lower() and code == 0, out.splitlines()[0] if out else "")
    need = {"xai_api": ["XAI_API_KEY"], "bot": ["GROK_BOT_WEBHOOK_KEY", "GROK_CALLBACK_SECRET"], "grok_cli": []}
    for name in ["OPENAI_API_KEY", *need.get(cfg.get("GROK_MODE"), [])]:
        add(f"secret {name}", cfg.secret(name), "present" if cfg.secret(name) else "missing")
    if cfg.get("GROK_MODE") == "bot":
        add("grok bot public callback URL", cfg.get("PUBLIC_CALLBACK_URL").startswith("https://"), cfg.get("PUBLIC_CALLBACK_URL") or "missing")
    sec = cfg.config_dir / "secrets.env"
    add("secrets.env mode 600", sec.is_file() and (sec.stat().st_mode & 0o077) == 0,
        oct(sec.stat().st_mode & 0o777) if sec.is_file() else "missing")
    head = run_quiet(["git", "-C", str(cfg.repo_dir), "rev-parse", "--short", "HEAD"])
    add("research checkout (origin/main)", head[0] == 0, f"{cfg.repo_dir} @ {head[1]}")
    free = shutil.disk_usage(cfg.state_dir).free / 1e9
    add(f"disk free >= {cfg.get('DISK_MIN_FREE_GB')} GB", free >= cfg.float("DISK_MIN_FREE_GB"), f"{free:.2f} GB")
    add("external disk TravailExterne (optional)", Path("/Volumes/TravailExterne").is_dir(), "mounted" if Path("/Volumes/TravailExterne").is_dir() else "not mounted")
    store = Store(cfg.db_path)
    add("database", store.integrity_ok(), f"schema v{store.schema_version()} {cfg.db_path}")
    add("launchd agent", service_state()["loaded"], json.dumps(service_state()))
    _, ps = run_quiet(["ps", "-axo", "pid,command"])
    others = [l.strip()[:140] for l in ps.splitlines() if any(k in l.lower() for k in
              ("polysentinel", "phi-backup", "collector", "forensic", "codex exec")) and "triagent" not in l]
    add("other research processes (info)", True, f"{len(others)}: " + " | ".join(others[:4]))
    if "--online" in args:
        try:
            page = get_json("https://data-api.polymarket.com/v2/trades?limit=1", retries=1)
            add("online: Polymarket data-api v2", isinstance(page.get("data"), list), f"{len(page['data'])} row")
        except ProviderError as exc:
            add("online: Polymarket data-api v2", False, exc)
        try:
            head_block, _ = polymarket.rpc(cfg, "eth_blockNumber", [])
            add("online: Polygon RPC", head_block, int(head_block, 16))
        except ProviderError as exc:
            add("online: Polygon RPC", False, exc)
        for name, url, key in (("OpenAI", "https://api.openai.com/v1/models", "OPENAI_API_KEY"),
                               ("xAI", "https://api.x.ai/v1/models", "XAI_API_KEY")):
            if not cfg.secret(key):
                add(f"online: {name} API", False, f"{key} missing")
                continue
            try:
                _, raw = http(url, headers={"Authorization": f"Bearer {cfg.secret(key)}"}, timeout=20)
                ids = [m.get("id") for m in json.loads(raw).get("data", [])]
                want = cfg.get("OPENAI_MODEL" if name == "OpenAI" else "XAI_MODEL")
                add(f"online: {name} API (model {want})", want in ids, f"{len(ids)} models visible")
            except ProviderError as exc:
                add(f"online: {name} API", False, f"{exc.kind}: {exc}")
    width = max(len(c[0]) for c in checks)
    for name, ok, detail in checks:
        print(f"{'OK ' if ok else 'NO '} {name.ljust(width)}  {detail}")
    return 0 if all(ok for name, ok, _ in checks if "optional" not in name and "info" not in name) else 1


def cmd_logs(cfg, args):
    log = cfg.state_dir / "logs" / "service.log"
    if not log.is_file():
        sys.exit(f"no log yet at {log}")
    os.execvp("tail", ["tail", "-n", "200", *(["-f"] if "-f" in args else []), str(log)])


def cmd_test(cfg, _args):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("TRIAGENT_STATE", None)
    return subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", str(CODE_DIR / "tests"), "-t",
                            str(CODE_DIR), "-v"], cwd=CODE_DIR, env=env)


def cmd_pause(cfg, _args):
    Store(cfg.db_path).set_kv("paused", "1")
    print("paused: no new provider call or collection; running missions finish and are stored")


def cmd_resume(cfg, _args):
    Store(cfg.db_path).set_kv("paused", "0")
    print("resumed")


def cmd_kill(cfg, _args):
    cfg.config_dir.mkdir(parents=True, exist_ok=True)
    cfg.kill_file.write_text(f"kill switch set {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    from .providers import kill_group
    store = Store(cfg.db_path)
    for job in store.jobs("status='running'"):
        kill_group(job["pid"])
        store.set_status(job["id"], "blocked", "stopped by kill switch")
    launchctl("bootout", f"{domain()}/{LABEL}")
    print(f"kill switch set ({cfg.kill_file}); service stopped; `triagent start` clears it")


def cmd_retry(cfg, args):
    if not args:
        sys.exit("usage: triagent retry <job_id>")
    store = Store(cfg.db_path)
    ok = store.set_status(args[0], "queued", "requeued by operator", expect=("blocked", "failed", "paused"))
    print("requeued" if ok else "job not found or not blocked/failed")


def cmd_inventory(cfg, _args):
    print(json.dumps(inventory.build(cfg, Store(cfg.db_path))))


def cmd_backtest(cfg, args):
    """CSV columns: address,t,label,event_ts,trade_usdc. Activity is cached; features never see data >= t."""
    if not args:
        sys.exit("usage: triagent backtest cases.csv [split_ts]")
    cases = [detector.Case(r["address"].lower(), int(r["t"]), int(r["label"]), int(r["event_ts"]),
                           float(r["trade_usdc"])) for r in csv.DictReader(open(args[0]))]
    cache = cfg.state_dir / "backtest_cache"
    cache.mkdir(exist_ok=True)

    def activity_for(address):
        path = cache / f"{address}.json"
        if not path.is_file():
            rows, truncated = polymarket.activity(address)
            path.write_text(json.dumps({"rows": rows, "truncated": truncated}))
            time.sleep(0.5)
        return json.loads(path.read_text())["rows"]
    split = int(args[1]) if len(args) > 1 else sorted(c.t for c in cases)[len(cases) // 2]
    print(json.dumps({"evaluation": detector.evaluate(cases, activity_for, split),
                      "placebo": detector.placebo(cases, activity_for)}, indent=1))


def cmd_run(cfg, _args):
    from .service import run
    log = cfg.state_dir / "logs" / "service.log"
    if log.is_file() and log.stat().st_size > 20_000_000:
        log.rename(log.with_suffix(".log.1"))
    return run(cfg)


COMMANDS = {"start": cmd_start, "stop": cmd_stop, "restart": cmd_restart, "status": cmd_status,
            "doctor": cmd_doctor, "logs": cmd_logs, "test": cmd_test, "pause": cmd_pause, "resume": cmd_resume,
            "kill": cmd_kill, "retry": cmd_retry, "run": cmd_run, "inventory": cmd_inventory,
            "backtest": cmd_backtest}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in COMMANDS:
        print(__doc__)
        return 2
    cfg = config_mod.load()
    return COMMANDS[argv[0]](cfg, argv[1:]) or 0
