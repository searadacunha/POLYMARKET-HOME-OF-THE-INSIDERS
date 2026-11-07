"""Automatic inventory of the investigations already in the repository, so that missions
look for gaps instead of repeating finished work."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .config import Config
from .store import Store, now, sha256_bytes

ADDRESS = re.compile(r"\b0x[0-9a-fA-F]{40}\b")
FIELD = re.compile(r"^- \*\*(?P<k>[^*]+)\*\*: (?P<v>.*)$")


def refresh_repo(cfg: Config) -> str:
    """Move the detached, sparse research checkout (made by install.sh) to the latest origin/main.
    Never touches a session's branch; a modified checkout is left alone."""
    repo = cfg.repo_dir
    if not (repo / ".git").exists():
        raise RuntimeError(f"research checkout {repo} missing; run install.sh")
    dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout
    if dirty.strip():
        return "dirty: left unchanged"
    subprocess.run(["git", "-C", str(repo), "fetch", "-q", "origin", "main"], check=True, capture_output=True, timeout=120)
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--detach", "origin/main"], check=True, capture_output=True)
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()


def parse_inventory(text: str) -> list[dict]:
    items, current = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            current = {"id": line[3:].strip(), "fields": {}}
            items.append(current)
        elif current is not None:
            m = FIELD.match(line.strip())
            if m:
                current["fields"][m["k"].strip().lower()] = m["v"].strip()
    return items


def heading_of(text: str) -> str:
    return next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), "untitled")


def first_heading(path: Path) -> str:
    return heading_of(path.read_text(encoding="utf-8", errors="replace"))


def limits_of(path: Path) -> str:
    return limits_text(path.read_text(encoding="utf-8", errors="replace"))


def unmerged_reports(repo: Path) -> list[tuple[str, str, str]]:
    """REPORT.md / FINDINGS.md added on research branches not yet merged into main (open PRs),
    so that missions do not redo work that exists only on a branch."""
    git = ["git", "-C", str(repo)]
    refs = subprocess.run([*git, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/research",
                           "refs/remotes/origin/investigation"], capture_output=True, text=True).stdout.split()
    out = []
    for ref in refs:
        names = subprocess.run([*git, "diff", "--name-only", "--diff-filter=AM", f"origin/main...{ref}", "--",
                                "*REPORT.md", "*FINDINGS.md"], capture_output=True, text=True).stdout.split()
        for name in names[:20]:
            text = subprocess.run([*git, "show", f"{ref}:{name}"], capture_output=True, text=True).stdout
            if text:
                out.append((ref.removeprefix("origin/"), name, text[:200_000]))
    return out


def limits_text(text: str) -> str:
    """The 'limits / open questions / next' sections of a report, which carry the open gaps."""
    out, keep = [], False
    for line in text.splitlines():
        if line.startswith("#"):
            keep = bool(re.search(r"limit|open|unresolved|next|not (demonstrated|established)|caveat", line, re.I))
            continue
        if keep and line.strip():
            out.append(line.strip())
    return " ".join(out)[:1500]


def build(cfg: Config, store: Store) -> dict:
    repo = cfg.repo_dir
    rows = []
    inv = repo / "INVENTORY.md"
    if inv.is_file():
        for item in parse_inventory(inv.read_text(encoding="utf-8")):
            f = item["fields"]
            if not f.get("title"):
                continue  # a section of the document, not an investigation
            rows.append((item["id"], f"investigations/{item['id']}", f.get("title"), f.get("actual state"),
                         f.get("objective"), f.get("conclusions"), f.get("limits")))
    for report in sorted((repo / "research_notes").rglob("REPORT.md")):
        rel = str(report.parent.relative_to(repo))
        if any(r[1] == rel for r in rows):
            continue
        rows.append(("note:" + rel.split("/", 1)[1], rel, first_heading(report), "research note", "", "",
                     limits_of(report)))
    branch_texts = unmerged_reports(repo)
    copies = cfg.state_dir / "branch-reports"
    for branch, path, text in branch_texts:
        target = copies / branch / path  # readable by missions: these reports exist only on PR branches
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        rows.append((f"branch:{branch}:{path.rsplit('/', 1)[0]}", f"branch-reports/{branch}/{path}", heading_of(text),
                     "unmerged research branch (open PR)", "", "", limits_text(text)))
    with store.conn(immediate=True) as c:
        for r in rows:
            digest = sha256_bytes("|".join(str(x) for x in r).encode())
            c.execute("""INSERT INTO inventory(id,path,title,state,objective,conclusions,limits,sha256,scanned_at)
                         VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET path=excluded.path,
                         title=excluded.title, state=excluded.state, objective=excluded.objective,
                         conclusions=excluded.conclusions, limits=excluded.limits, sha256=excluded.sha256,
                         scanned_at=excluded.scanned_at""", (*r, digest, now()))
    known = 0
    with store.conn(immediate=True) as c:
        for base in ("investigations", "research_notes"):
            for path in (repo / base).rglob("*"):
                if path.suffix not in (".md", ".csv", ".json") or not path.is_file() or path.stat().st_size > 5_000_000:
                    continue
                rel = str(path.relative_to(repo))
                found = {a.lower() for a in ADDRESS.findall(path.read_text(encoding="utf-8", errors="replace"))}
                for a in found:
                    known += c.execute("INSERT OR IGNORE INTO known_addresses(address,source_path) VALUES (?,?)",
                                       (a, rel)).rowcount
        for branch, path, text in branch_texts:
            for a in {a.lower() for a in ADDRESS.findall(text)}:
                known += c.execute("INSERT OR IGNORE INTO known_addresses(address,source_path) VALUES (?,?)",
                                   (a, f"{branch}:{path}")).rowcount
    store.set_kv("inventory_built", now())
    return {"investigations": len(rows), "new_known_address_refs": known}


def digest(store: Store, limit_chars: int = 14000) -> str:
    lines = []
    for r in store.query("SELECT * FROM inventory ORDER BY id"):
        lines.append(f"- {r['id']} [{r['state']}] {r['title']}. Conclusions: {(r['conclusions'] or '')[:400]} "
                     f"Limits: {(r['limits'] or '')[:400]} (repo:{r['path']})")
    return "\n".join(lines)[:limit_chars]
