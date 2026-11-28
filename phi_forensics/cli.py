"""Command line of the toolkit. Every tool of the MCP server is a sub-command with the same arguments.

    python3 -m phi_forensics tools
    python3 -m phi_forensics investigate_wallet --wallet 0x...
    python3 -m phi_forensics reconstruct_positions --wallet 0x... --exact
    python3 -m phi_forensics mcp                    # serve the same tools to an AI agent over stdio
    python3 -m phi_forensics graph build links.json funding.json graph.html   # offline graph page (phi_forensics.viz)

Answers are JSON on standard output. The exit code is 1 when a tool reports an error.
"""
import argparse
import json
import sys

from .mcp import protocol, server


def _argument(parser, name, schema, required):
    kind = schema.get("type")
    if kind == "boolean":
        parser.add_argument(f"--{name}", action="store_true", help=schema.get("description"))
    elif kind == "array":
        parser.add_argument(f"--{name}", nargs="+", required=required, help=schema.get("description"))
    elif kind == "object":
        parser.add_argument(f"--{name}", type=json.loads, required=required, help=(schema.get("description") or "") + " Given as JSON.")
    else:
        parser.add_argument(f"--{name}", type=int if kind == "integer" else str, required=required, choices=schema.get("enum"),
                            help=schema.get("description"))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["graph"]:
        from . import viz
        return viz.main(argv[1:])
    tools = server.tools()
    parser = argparse.ArgumentParser(prog="phi-forensics", description="Read-only forensic investigation of Polymarket wallets and markets.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("mcp", help="serve the tools to an AI agent (Model Context Protocol, stdio)")
    commands.add_parser("graph", help="offline HTML graph of JSON answers: graph build|serve ...")
    commands.add_parser("tools", help="list the tools")
    for tool in tools:
        sub = commands.add_parser(tool.name, help=tool.title, description=tool.description)
        for name, schema in tool.schema["properties"].items():
            _argument(sub, name, schema, name in tool.schema["required"])
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    if command == "mcp":
        return server.main()
    if command == "tools":
        print(json.dumps([{"name": t.name, "title": t.title, "description": t.description} for t in tools], indent=1))
        return 0
    tool = next(t for t in tools if t.name == command)
    arguments = {k: v for k, v in args.items() if v is not None and v is not False}  # 0 is an argument
    problems = protocol.validate(arguments, tool.schema)
    if problems:
        print("invalid arguments: " + "; ".join(problems), file=sys.stderr)
        return 1
    try:
        answer = tool.handler(arguments)
    except protocol.ToolError as err:
        print(str(err), file=sys.stderr)
        return 1
    if isinstance(answer.get("report"), str) and answer.get("format") == "markdown":
        print(answer["report"])
    else:
        print(json.dumps(answer, indent=1, ensure_ascii=False, default=str))
    return 0
