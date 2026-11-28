#!/usr/bin/env python3
"""Drive phi-forensics-mcp with the official MCP Python SDK, in the handshake and the per-request protocol forms.

    python3 -m venv /tmp/mcp-sdk && /tmp/mcp-sdk/bin/pip install mcp
    /tmp/mcp-sdk/bin/python scripts/test_mcp_client.py transcript.json            # offline: archive tools of this checkout
    PHI_LIVE=1 /tmp/mcp-sdk/bin/python scripts/test_mcp_client.py transcript.json  # also the live tools (network)

The SDK is a test tool only: phi_forensics never imports it. The server is this checkout run with the interpreter
given by --python (default: python3), or an installed command given by --command. The transcript records each call:
its arguments, the size of the answer and the verdict, never the answer itself. Exit code 0 only if every check passes.
"""
import argparse
import asyncio
import json
import os
import shutil
import sys
import time
from pathlib import Path

import mcp
import mcp.types as types
from mcp import Client, StdioServerParameters
from mcp.shared.exceptions import MCPError

ROOT = Path(__file__).resolve().parents[1]
TOOLS = 21
CHECK = "Recheck the phase 8 wallet-age sensitivity note offline"
LIVE = ("investigate_wallet", "reconstruct_positions", "trace_funding", "trace_address", "find_related_wallets", "link_wallets",
        "verify_transfer", "verify_fill", "generate_report", "investigate_market", "compare_traders", "profile_behaviour")


class Run:
    def __init__(self, client, mode, record):
        self.client, self.mode, self.record = client, mode, record

    def check(self, step, ok, **detail):
        self.record.append({"mode": self.mode, "step": step, "verdict": "pass" if ok else "fail", **detail})
        print(f"{'PASS' if ok else 'FAIL'} [{self.mode}] {step}" + ("" if ok else f": {json.dumps(detail, default=str)[:400]}"))
        return ok

    async def call(self, name, arguments, expect_error=False):
        """One tools/call; returns its structured content, or None when it failed."""
        start = time.monotonic()
        try:
            result = await self.client.call_tool(name, arguments)
        except MCPError as err:
            self.check(f"call {name}", False, arguments=arguments, error={"code": err.error.code, "message": err.error.message})
            return None
        text = "".join(c.text for c in result.content if isinstance(c, types.TextContent))
        detail = {"arguments": arguments, "is_error": result.is_error, "bytes": len(text.encode()), "seconds": round(time.monotonic() - start, 2)}
        if expect_error:
            self.check(f"{name} refuses {json.dumps(arguments)}", result.is_error is True and result.structured_content is None,
                       **detail, message=text[:200])
            return None
        same = result.structured_content is not None and json.loads(text) == result.structured_content
        if not self.check(f"call {name}", result.is_error is False and same, **detail, message=text[:300] if result.is_error else None):
            return None
        return result.structured_content


async def session(mode, params, record, live):
    async with Client(params, mode=mode, read_timeout_seconds=900) as client:
        run = Run(client, mode, record)
        expected = "2026-07-28" if mode == "auto" else types.version.LATEST_HANDSHAKE_VERSION
        run.check("connect", client.protocol_version == expected and client.server_info.name == "phi-forensics" and bool(client.instructions),
                  protocol_version=client.protocol_version, server=client.server_info.model_dump(exclude_none=True))

        listed = (await client.list_tools()).tools
        bad = [t.name for t in listed if t.input_schema.get("type") != "object" or not t.annotations or t.annotations.read_only_hint is not True
               or t.annotations.destructive_hint is not False]
        run.check(f"list_tools: {TOOLS} tools, each with an object input schema and read-only annotations", len(listed) == TOOLS and not bad,
                  tools=len(listed), without_read_only_schema=bad)

        status = await run.call("server_status", {})
        run.check("server_status sees the checkout", bool(status) and status["read_only"] is True and status["archive_tools_available"] is True,
                  repository_checkout=status and status["repository_checkout"])

        found = await run.call("list_investigations", {})
        run.check("list_investigations is not empty", bool(found and found["investigations"]), count=found and len(found["investigations"]))
        await run.call("search_findings", {"level": "CONFIRMED", "limit": 3})
        alerts = await run.call("query_alerts", {"limit": 3})
        rows = [r for table in (alerts or {}).get("tables", []) for r in table["alerts"] if r.get("initiator")]
        wallet = rows[0]["initiator"] if rows else None
        mentions = await run.call("find_address", {"address": wallet}) if wallet else None
        run.check("find_address finds the files that cite an archived alert's wallet", bool(mentions and mentions["files_total"]), wallet=wallet)
        tables = await run.call("list_datasets", {"text": "changenow", "limit": 50})
        csv = next((e["path"] for e in (tables or {}).get("datasets", []) if e["format"] == "csv" and e["rows"]), None)
        rows_back = await run.call("query_dataset", {"path": csv, "limit": 3}) if csv else None
        run.check("query_dataset returns rows of a catalogued CSV", bool(rows_back and rows_back["rows"]), path=csv)
        checks = await run.call("list_checks", {})
        run.check("list_checks names the check this test reproduces", bool(checks) and CHECK in [c["name"] for c in checks["checks"]])
        reproduced = await run.call("reproduce_check", {"name": CHECK})
        run.check("reproduce_check passes", bool(reproduced and reproduced["passed"]), seconds=reproduced and reproduced["seconds"])

        await run.call("find_address", {"address": "not-an-address"}, expect_error=True)
        await run.call("find_address", {}, expect_error=True)
        await run.call("server_status", {"unknown": 1}, expect_error=True)
        await run.call("trace_address", {"address": "0x" + "0" * 40, "direction": "sideways", "at_block": 1}, expect_error=True)
        try:
            await client.call_tool("no_such_tool", {})
            run.check("unknown tool is a JSON-RPC error -32602", False, answer="a result")
        except MCPError as err:
            run.check("unknown tool is a JSON-RPC error -32602", err.error.code == types.INVALID_PARAMS, code=err.error.code,
                      message=err.error.message)

        if live and wallet:
            other = next((r["initiator"] for r in rows if r["initiator"] != wallet), wallet)
            condition = rows[0].get("condition_id")
            await run.call("investigate_wallet", {"wallet": wallet})
            await run.call("reconstruct_positions", {"wallet": wallet, "limit": 5})
            flows = await run.call("trace_funding", {"wallet": wallet})
            await run.call("find_related_wallets", {"wallet": wallet})
            await run.call("link_wallets", {"wallets": [wallet, other]})
            await run.call("compare_traders", {"wallets": [wallet, other]})
            await run.call("generate_report", {"wallet": wallet})
            await run.call("profile_behaviour", {"wallet": wallet})
            market = await run.call("investigate_market", {"condition": condition, "limit": 5}) if condition else None
            run.check("investigate_market had a condition from the archive", market is not None, condition=condition)
            payments = (flows or {}).get("deposits", {}).get("rows", []) + (flows or {}).get("withdrawals", {}).get("rows", [])
            payment = next((p for p in payments if p.get("tx") and p.get("block")), None)
            run.check("trace_funding gave a transaction and a block to verify", payment is not None, keys=sorted(payments[0]) if payments else None)
            if payment:
                await run.call("trace_address", {"address": wallet, "direction": "upstream", "at_block": int(payment["block"]), "hops": 1})
                # No tool returns a fill hash, so verify_fill reads the same payment: its verdict is recorded, not judged.
                for name, extra in (("verify_transfer", {}), ("verify_fill", {"wallet": wallet})):
                    answer = await run.call(name, {"transaction": payment["tx"], **extra})
                    run.check(f"{name} returns a verdict", bool(answer and answer.get("verdict")), verdict=answer and answer.get("verdict"))


async def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("transcript", type=Path, help="where to write the JSON transcript")
    parser.add_argument("--python", default="python3", help="interpreter that runs the server from this checkout")
    parser.add_argument("--command", help="an installed phi-forensics-mcp to test instead of the checkout")
    args = parser.parse_args()
    live = os.environ.get("PHI_LIVE") == "1"
    env = {"PHI_REPO_ROOT": os.environ.get("PHI_REPO_ROOT", str(ROOT)), "PYTHONDONTWRITEBYTECODE": "1"}
    if args.command:
        params = StdioServerParameters(command=args.command, env=env, cwd=str(ROOT))
    else:
        params = StdioServerParameters(command=shutil.which(args.python) or args.python, args=["-m", "phi_forensics", "mcp"],
                                       env={**env, "PYTHONPATH": str(ROOT)}, cwd=str(ROOT))
    record = []
    for mode in ("legacy", "auto"):
        try:
            await session(mode, params, record, live)
        except Exception as err:  # the SDK refusing the server is a finding, kept in the transcript
            record.append({"mode": mode, "step": "session", "verdict": "fail", "error": f"{type(err).__name__}: {err}"[:2000]})
            print(f"FAIL [{mode}] session: {type(err).__name__}: {err}")
    failed = [r for r in record if r["verdict"] == "fail"]
    transcript = {"sdk": {"package": "mcp", "version": getattr(mcp, "__version__", None) or _version("mcp"),
                          "known_protocol_versions": list(types.version.KNOWN_PROTOCOL_VERSIONS)},
                  "server": params.command if args.command else f"{params.command} -m phi_forensics mcp", "live": live,
                  "checks": len(record), "failed": len(failed), "calls": record}
    args.transcript.write_text(json.dumps(transcript, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"{len(record) - len(failed)}/{len(record)} checks passed; transcript {args.transcript}")
    return 1 if failed else 0


def _version(name):
    from importlib.metadata import version
    return version(name)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
