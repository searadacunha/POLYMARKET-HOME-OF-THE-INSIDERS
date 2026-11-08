"""Configuration: plain KEY=VALUE files, secrets kept apart and never logged."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

HOME = Path.home()
CODE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_STATE = HOME / ".local/state/triagent"
DEFAULT_CONFIG = HOME / ".config/triagent"

SECRET_NAMES = ("OPENAI_API_KEY", "XAI_API_KEY", "ANTHROPIC_API_KEY", "GROK_BOT_WEBHOOK_KEY",
                "GROK_CALLBACK_SECRET", "BROKER_TOKEN", "N8N_WAKE_TOKEN", "UI_TOKEN")

DEFAULTS = {
    "RUN_MODE": "dryrun",               # dryrun | live
    "CLAUDE_AUTH": "subscription",      # subscription (--safe-mode, OAuth) | api (--bare, ANTHROPIC_API_KEY)
    "CLAUDE_BIN": str(HOME / ".local/bin/claude"),
    "CLAUDE_MODEL": "sonnet",
    "CLAUDE_MAX_TURNS": "30",
    "CLAUDE_TIMEOUT_S": "2700",
    "CLAUDE_MAX_USD_PER_MISSION": "3",
    "CLAUDE_MAX_MISSIONS_DAY": "6",
    "CLAUDE_MAX_USD_DAY": "15",
    # api (OPENAI_API_KEY, billed per token) | codex_cli (official Codex CLI on the ChatGPT subscription; this
    # is NOT the ChatGPT browser) | chatgpt_gui (blocked, never used: see README). No mode falls back to another.
    "OPENAI_MODE": "api",
    "CODEX_BIN": str(HOME / ".local/bin/codex"),
    "CODEX_MODEL": "",                  # empty = the Codex default for the signed-in ChatGPT plan
    "CODEX_TIMEOUT_S": "900",
    "GROK_CLI_MODEL": "",               # empty = the Grok CLI default (`grok models`); XAI_MODEL is for the API
    "OPENAI_MODEL": "gpt-6.1-sol",
    "OPENAI_USD_PER_MTOK_IN": "2",
    "OPENAI_USD_PER_MTOK_OUT": "10",
    "OPENAI_MAX_USD_DAY": "3",
    "OPENAI_MAX_CALLS_DAY": "40",
    "GROK_MODE": "xai_api",             # xai_api | grok_cli | bot
    "GROK_BIN": str(HOME / ".grok/bin/grok"),
    "XAI_MODEL": "grok-4.7",
    "XAI_USD_PER_MTOK_IN": "2",
    "XAI_USD_PER_MTOK_OUT": "6",
    "XAI_USD_PER_POST": "0.005",
    "XAI_USD_PER_USER": "0.01",
    "XAI_MAX_USD_DAY": "3",
    "GROK_MAX_MISSIONS_DAY": "6",
    "GROK_TIMEOUT_S": "600",
    "GROK_BOT_WEBHOOK_URL": "",
    "PUBLIC_CALLBACK_URL": "",
    "GROK_BOT_DEADLINE_S": "21600",
    "MAX_DEPTH": "4",
    "MAX_CHILDREN": "2",
    "MIN_NOVELTY_FOLLOWUP": "3",
    "STOP_AFTER_LOW_NOVELTY": "2",
    "DISCOVERY_SECONDS": "43200",
    "COLLECT_SECONDS": "60",
    "COLLECT_FAST_SECONDS": "15",       # used while the trade feed has a backlog (checkpoint not reached)
    "ACCOUNTS_SHADOW": "0",             # 1 = record new accounts and their first payer (never alerts)
    "ACCOUNTS_PER_TICK": "15",          # first-deposit lookups per minute (~700 accounts are created per hour)
    # internal = the supervisor's own 10 s scheduler starts missions (historical) | n8n = only n8n starts them,
    # through the broker below; the supervisor then only watches processes, collects and alerts
    "ORCHESTRATOR": "internal",
    "BROKER_PORT": "8791",
    "BROKER_AUTH_HEADER": "X-TriAgent-Key",
    "N8N_WAKE_URL": "http://127.0.0.1:5678/webhook/triagent-v2-wake",
    "N8N_WAKE_HEADER": "X-TriAgent-Wake",
    "LEASE_TTL_S": "120",
    "STALL_AFTER_S": "1200",            # no file progress for this long: label suspected_stalled, never kill
    "ALERT_MIN_USDC": "5000",
    "ALERT_MIN_FLAGS": "3",
    "ALERT_HIGH_FLAGS": "5",            # level HIGH from this many flags, WATCH below (flag counts, not probabilities)
    "ALERT_NOTIFY_MIN_FLAGS": "4",      # macOS notification threshold, chosen on alert load (README), not calibrated
    "ALERT_NOTIFY_MAX_DAY": "6",
    "ALERT_NOTIFY_COOLDOWN_S": "21600",
    "PROFILES_PER_TICK": "3",
    "BACKFILL_MAX_PAGES": "20",
    "CONFIRMATIONS": "64",
    "SERVICE_FANOUT": "25",
    "ALERT_MISSIONS_DAY": "3",
    "DISK_MIN_FREE_GB": "13.5",
    "HTTP_PORT": "8790",
    # Investigation center (dashboard settings override these through kv "pref.<KEY>")
    "DAILY_REPORT_TIME": "19:00",       # local time of the daily digest
    "DAILY_REPORT_TZ": "Europe/Lisbon",
    "NOTIFY_ENABLED": "1",              # macOS notifications for major reports, verified links, blockages
    "NOTIFY_MAX_DAY": "8",
    "NOTIFY_COOLDOWN_S": "1800",        # per notification kind
    "BLOCKED_NOTIFY_AFTER_S": "3600",   # a blockage is notified once it has lasted this long
    # Historical campaign (triagent campaign start) and its draft PRs
    "CAMPAIGN_TRIAGE_BATCH": "12",      # leads per GPT triage session
    "PUBLISH_ENABLED": "1",             # 1 = audited dossiers become draft PRs once every check passes
    "PUBLISH_MAX_OPEN": "3",            # campaign draft PRs open at once; later dossiers wait
    "PUBLISH_REMOTE": "",               # empty = the research checkout's origin
    "GH_BIN": "",                       # empty = gh on PATH, else ~/.local/bin/gh
    "POLYGON_RPC": "https://polygon.drpc.org,https://polygon-bor-rpc.publicnode.com",
}


def read_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


@dataclass
class Config:
    state_dir: Path
    config_dir: Path
    values: dict[str, str]
    secrets: dict[str, str] = field(repr=False)

    def get(self, key: str) -> str:
        return self.values.get(key, DEFAULTS.get(key, ""))

    def int(self, key: str) -> int:
        return int(float(self.get(key)))

    def float(self, key: str) -> float:
        return float(self.get(key))

    def secret(self, key: str) -> str:
        return self.secrets.get(key, "")

    @property
    def live(self) -> bool:
        return self.get("RUN_MODE").lower() == "live"

    @property
    def db_path(self) -> Path:
        return self.state_dir / "triagent.sqlite3"

    @property
    def missions_dir(self) -> Path:
        return self.state_dir / "missions"

    @property
    def evidence_dir(self) -> Path:
        return self.state_dir / "evidence"

    @property
    def repo_dir(self) -> Path:
        """Detached read-only checkout of origin/main used as research context."""
        return Path(self.get("REPO_PATH") or self.state_dir / "research-repo")

    @property
    def kill_file(self) -> Path:
        return self.config_dir / "KILL"


def load(state_dir: Path | None = None, config_dir: Path | None = None) -> Config:
    state = Path(state_dir or os.getenv("TRIAGENT_STATE") or DEFAULT_STATE)
    conf = Path(config_dir or os.getenv("TRIAGENT_CONFIG") or DEFAULT_CONFIG)
    values = dict(DEFAULTS)
    values.update(read_env_file(conf / "config.env"))
    secrets = read_env_file(conf / "secrets.env")
    for name in SECRET_NAMES:  # an explicit environment variable wins (tests, one-off runs)
        if os.getenv(name):
            secrets[name] = os.environ[name]
    for key in DEFAULTS:
        if os.getenv("TRIAGENT_" + key):
            values[key] = os.environ["TRIAGENT_" + key]
    for k in list(values):
        if k in SECRET_NAMES:  # a secret put in config.env by mistake is moved, never displayed
            secrets.setdefault(k, values.pop(k))
    state.mkdir(parents=True, exist_ok=True)
    return Config(state, conf, values, secrets)
