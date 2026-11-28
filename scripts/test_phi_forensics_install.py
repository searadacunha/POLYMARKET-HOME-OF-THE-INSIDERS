#!/usr/bin/env python3
"""Build the phi-forensics wheel, install it in a fresh virtual environment and use it from outside the checkout.

    python3 scripts/test_phi_forensics_install.py [--python python3.11]

Only the build needs the network: pip fetches the build backend (setuptools) from PyPI unless its cache holds it.
Installing the wheel, the command line and the MCP exchange run offline. The checkout is copied first, so the build
leaves no build/ or *.egg-info/ in it. Exit code 0 only if every check passes.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("pyproject.toml", "MANIFEST.in", "LICENSE", "phi_forensics", "monitoring")
PACKAGES = ("phi_forensics", "phi_forensics/mcp", "monitoring", "monitoring/phi_monitor", "monitoring/livecollect")
MAX_WHEEL_BYTES = 1_000_000
TOOLS = 21


def run(command, cwd, env=None, stdin=None):
    done = subprocess.run(command, cwd=cwd, env=env, input=stdin, capture_output=True, text=True, timeout=600)
    return done.returncode, done.stdout, done.stderr


def build(python, work):
    source = work / "source"
    for name in SOURCES:
        if (ROOT / name).is_dir():
            shutil.copytree(ROOT / name, source / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        elif (ROOT / name).exists():
            source.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, source / name)
    code, out, err = run([python, "-m", "pip", "wheel", "--no-deps", "-q", "-w", str(work / "dist"), str(source)], work)
    if code:
        raise SystemExit(f"build failed:\n{out}\n{err}")
    return next((work / "dist").glob("phi_forensics-*.whl"))


def wheel_problems(wheel):
    names = zipfile.ZipFile(wheel).namelist()
    expected = {p.relative_to(ROOT).as_posix() for d in PACKAGES for p in (ROOT / d).glob("*.py")}
    expected |= {p.relative_to(ROOT).as_posix() for p in (ROOT / "phi_forensics" / "data").glob("*.json")}
    expected.add("phi_forensics/README.md")  # the long description, which setuptools also ships as package data
    problems = [f"missing from the wheel: {n}" for n in sorted(expected - set(names))]
    problems += [f"not a file of the package: {n}" for n in names if ".dist-info/" not in n and n not in expected]
    problems += [f"package without __init__.py: {d}" for d in PACKAGES if f"{d}/__init__.py" not in names]
    if wheel.stat().st_size > MAX_WHEEL_BYTES:
        problems.append(f"wheel of {wheel.stat().st_size} bytes, more than {MAX_WHEEL_BYTES}")
    return names, problems


def exchange(command, cwd, env):
    """initialize, tools/list and two tools/call with raw newline-delimited JSON-RPC over the server's stdio."""
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "install-test", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "server_status", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "list_investigations", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "investigate_wallet", "arguments": {"wallet": "0x1"}}},
    ]
    code, out, err = run([command], cwd, env, "".join(json.dumps(m) + "\n" for m in messages))
    replies = {r["id"]: r for r in map(json.loads, out.splitlines())}
    return code, replies, err


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", default=sys.executable, help="interpreter that builds the wheel and creates the environment")
    python = parser.parse_args().python
    checks = []

    def check(name, ok, detail=""):
        checks.append(ok)
        print(("PASS " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))

    with tempfile.TemporaryDirectory(prefix="phi-install-") as tmp:
        work = Path(tmp)
        wheel = build(python, work)
        names, problems = wheel_problems(wheel)
        print(f"wheel {wheel.name}: {wheel.stat().st_size} bytes, {len(names)} files")
        check("the wheel holds the package, its data and nothing else", not problems, "; ".join(problems))

        code, out, err = run([python, "-m", "venv", str(work / "venv")], work)
        check("virtual environment created", code == 0, err)
        bin_dir = work / "venv" / ("Scripts" if os.name == "nt" else "bin")
        code, out, err = run([str(bin_dir / "python"), "-m", "pip", "install", "-q", "--no-index", "--no-deps", str(wheel)], work)
        check("wheel installed offline", code == 0, err)

        elsewhere = work / "elsewhere"
        elsewhere.mkdir()
        env = {k: v for k, v in os.environ.items() if k not in ("PHI_REPO_ROOT", "PYTHONPATH")}
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        code, out, err = run([str(bin_dir / "python"), "-c", "import phi_forensics, phi_forensics.mcp.server, phi_forensics.registry as r; "
                              "print(phi_forensics.__file__, len(r.protocol_contracts()), len(r.service_labels()))"], elsewhere, env)
        check("the installed package is imported, not the checkout, and reads its data files",
              code == 0 and str(ROOT) not in out and "site-packages" in out, out + err)

        code, out, err = run([str(bin_dir / "phi-forensics"), "tools"], elsewhere, env)
        listed = json.loads(out) if code == 0 else []
        check(f"phi-forensics tools lists {TOOLS} tools", len(listed) == TOOLS, f"exit {code}, {len(listed)} tools, {err}")

        code, out, err = run([str(bin_dir / "phi-forensics"), "server_status"], elsewhere, env)
        status = json.loads(out) if code == 0 else {}
        check("phi-forensics server_status: read-only, no checkout, archive tools unavailable",
              status.get("read_only") is True and status.get("repository_checkout") is None and status.get("archive_tools_available") is False,
              f"exit {code}, {out[:300]} {err[:300]}")

        code, out, err = run([str(bin_dir / "phi-forensics"), "list_investigations"], elsewhere, env)
        check("an archive tool outside the checkout fails and names PHI_REPO_ROOT", code == 1 and "PHI_REPO_ROOT" in err, f"exit {code}, {err}")

        code, replies, err = exchange(str(bin_dir / "phi-forensics-mcp"), elsewhere, env)
        init = replies.get(1, {}).get("result", {})
        check("MCP initialize", init.get("protocolVersion") == "2025-11-25" and init.get("serverInfo", {}).get("name") == "phi-forensics",
              json.dumps(replies.get(1))[:300])
        tools = replies.get(2, {}).get("result", {}).get("tools", [])
        check(f"MCP tools/list returns {TOOLS} read-only tools",
              len(tools) == TOOLS and all(t["annotations"]["readOnlyHint"] is True and t["inputSchema"]["type"] == "object" for t in tools),
              f"{len(tools)} tools")
        called = replies.get(3, {}).get("result", {})
        check("MCP tools/call server_status", called.get("isError") is False and called["structuredContent"]["read_only"] is True
              and json.loads(called["content"][0]["text"]) == called["structuredContent"], json.dumps(replies.get(3))[:300])
        refused = replies.get(4, {}).get("result", {})
        check("MCP archive tool without checkout is a tool error naming PHI_REPO_ROOT",
              refused.get("isError") is True and "PHI_REPO_ROOT" in refused["content"][0]["text"], json.dumps(replies.get(4))[:300])
        invalid = replies.get(5, {}).get("result", {})
        check("MCP live tool is served and validates its arguments without the network",
              invalid.get("isError") is True and invalid["content"][0]["text"].startswith("invalid arguments"), json.dumps(replies.get(5))[:300])
        check("MCP server exits 0 at end of input", code == 0, err[-500:])

    print(f"{sum(checks)}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
