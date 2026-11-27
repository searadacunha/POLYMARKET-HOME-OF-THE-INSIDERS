"""Model Context Protocol server core: JSON-RPC 2.0 over stdio, standard library only.

One process serves both protocol eras, as the 2026-07-28 revision allows: a request carrying the per-request
`_meta` protocol fields is answered statelessly, and an `initialize` request selects the legacy handshake
(2025-11-25 and earlier) for the rest of the process.

The core knows nothing about Polymarket. It validates arguments against each tool's JSON Schema, rate-limits
calls, refuses oversized results instead of truncating them and turns handler failures into tool errors, so a
tool is a plain function from a dict of arguments to a JSON object.
"""
import json
import re
import sys
import time
import traceback

from ..text import clean_text

MODERN = "2026-07-28"
LEGACY = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
META_VERSION = "io.modelcontextprotocol/protocolVersion"
META_CAPABILITIES = "io.modelcontextprotocol/clientCapabilities"
META_SERVER = "io.modelcontextprotocol/serverInfo"

PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL_ERROR = -32700, -32600, -32601, -32602, -32603
UNSUPPORTED_VERSION, LEGACY_RESOURCE_NOT_FOUND = -32022, -32002

METHODS = {
    "initialize": "_initialize", "ping": "_ping", "server/discover": "_server_discover",
    "tools/list": "_tools_list", "tools/call": "_tools_call",
    "resources/list": "_resources_list", "resources/templates/list": "_resources_templates_list", "resources/read": "_resources_read",
    "prompts/list": "_prompts_list", "prompts/get": "_prompts_get", "logging/setLevel": "_logging_setLevel",
}
MAX_LINE_BYTES = 1_000_000
_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int, "number": (int, float)}


class ToolError(Exception):
    """An expected failure a tool reports to the caller: bad target, upstream refusal, nothing found."""


class RpcError(Exception):
    def __init__(self, code, message, data=None):
        super().__init__(message)
        self.code, self.message, self.data = code, message, data


def validate(value, schema, path="arguments"):
    """Errors of `value` against the subset of JSON Schema the tools use. An empty list means valid."""
    kind = schema.get("type")
    if kind:
        ok = isinstance(value, _TYPES[kind]) and not (kind in ("integer", "number") and isinstance(value, bool))
        if not ok:
            return [f"{path}: expected {kind}"]
    errors = []
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: must be one of {schema['enum']}")
    if isinstance(value, str):
        if len(value) > schema.get("maxLength", 10_000) or len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: length out of bounds")
        elif "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            errors.append(f"{path}: does not match {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"] or "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: out of range")
    if isinstance(value, list):
        if len(value) > schema.get("maxItems", 1000) or len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: number of items out of bounds")
        for i, item in enumerate(value):
            errors += validate(item, schema.get("items", {}), f"{path}[{i}]")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        errors += [f"{path}.{key}: required" for key in schema.get("required", []) if key not in value]
        for key, item in value.items():
            if key in props:
                errors += validate(item, props[key], f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}.{key}: unknown argument")
    return errors


class Tool:
    def __init__(self, name, description, handler, properties=None, required=(), title=None, open_world=True):
        self.name, self.description, self.handler, self.title, self.open_world = name, description, handler, title, open_world
        self.schema = {"type": "object", "properties": properties or {}, "required": list(required), "additionalProperties": False}

    def describe(self):
        return {"name": self.name, "title": self.title or self.name, "description": self.description, "inputSchema": self.schema,
                "annotations": {"title": self.title or self.name, "readOnlyHint": True, "destructiveHint": False,
                                "idempotentHint": True, "openWorldHint": self.open_world}}


class RateLimit:
    """At most `calls` per `seconds`, sliding window. The clock is injectable so tests do not sleep."""

    def __init__(self, calls=60, seconds=60.0, clock=time.monotonic):
        self.calls, self.seconds, self.clock, self.stamps = calls, seconds, clock, []

    def wait_needed(self):
        now = self.clock()
        self.stamps = [t for t in self.stamps if now - t < self.seconds]
        if len(self.stamps) >= self.calls:
            return self.seconds - (now - self.stamps[0])
        self.stamps.append(now)
        return 0.0


class Server:
    def __init__(self, name, version, instructions="", title=None, max_result_bytes=400_000, rate=None, log=None):
        self.info = {"name": name, "title": title or name, "version": version}
        self.instructions, self.max_result_bytes = instructions, max_result_bytes
        self.rate = rate or RateLimit()
        self.log = log or (lambda text: print(text, file=sys.stderr, flush=True))
        self.tools, self.resources, self.prompts = {}, {}, {}
        self.legacy = None  # the version agreed by `initialize`, once a legacy client has opened

    # Registration

    def add_tool(self, tool):
        self.tools[tool.name] = tool

    def add_resource(self, uri, name, description, loader, mime="text/markdown"):
        self.resources[uri] = {"uri": uri, "name": name, "description": description, "mimeType": mime, "loader": loader}

    def add_prompt(self, name, description, arguments, render):
        self.prompts[name] = {"name": name, "description": description, "arguments": arguments, "render": render}

    # Protocol

    def capabilities(self):
        return {"tools": {"listChanged": False}, "resources": {"subscribe": False, "listChanged": False}, "prompts": {"listChanged": False}}

    def handle(self, message):
        """One decoded message in, one response dict out, or None when no response is due."""
        if not isinstance(message, dict):
            return _error(None, INVALID_REQUEST, "a message must be one JSON object (batches are not part of the protocol)")
        ident, method = message.get("id"), message.get("method")
        notification = "id" not in message
        if "method" not in message:
            return None  # a response to a request this server never sends
        if not notification and (isinstance(ident, bool) or not isinstance(ident, (str, int))):
            return _error(None, INVALID_REQUEST, "id must be a string or an integer")
        if message.get("jsonrpc") != "2.0" or not isinstance(method, str):
            return None if notification else _error(ident, INVALID_REQUEST, "jsonrpc must be \"2.0\" and method a string")
        if notification:
            return None  # notifications/initialized, notifications/cancelled: nothing to answer, nothing to undo
        params = message.get("params", {})
        try:
            if not isinstance(params, dict):
                raise RpcError(INVALID_PARAMS, "params must be an object")
            meta = params.get("_meta") if isinstance(params.get("_meta"), dict) else {}
            modern = META_VERSION in meta and method != "initialize"  # initialize always means the legacy handshake
            if modern:
                if meta[META_VERSION] != MODERN:
                    raise RpcError(UNSUPPORTED_VERSION, "Unsupported protocol version",
                                   {"supported": [MODERN, *LEGACY], "requested": meta[META_VERSION]})
                if not isinstance(meta.get(META_CAPABILITIES), dict):
                    raise RpcError(INVALID_PARAMS, f"_meta[{META_CAPABILITIES!r}] is required")
            elif method not in ("initialize", "ping") and self.legacy is None:
                raise RpcError(INVALID_PARAMS, f"send initialize first (protocol {LEGACY[0]} and earlier) "
                                               f"or put {META_VERSION!r} in _meta (protocol {MODERN})")
            if method not in METHODS:
                raise RpcError(METHOD_NOT_FOUND, f"Method not found: {clean_text(method, 80)}")
            result = getattr(self, METHODS[method])(params, modern)
            if modern:
                result = {"resultType": "complete", **result}
            return {"jsonrpc": "2.0", "id": ident, "result": result}
        except RpcError as err:
            return _error(ident, err.code, err.message, err.data)
        except Exception:  # a defect in the server: say so without leaking internals, keep serving
            self.log(traceback.format_exc())
            return _error(ident, INTERNAL_ERROR, "internal error")

    def _initialize(self, params, modern):
        asked = params.get("protocolVersion")
        self.legacy = asked if asked in LEGACY else LEGACY[0]
        return {"protocolVersion": self.legacy, "capabilities": self.capabilities(), "serverInfo": self.info,
                "instructions": self.instructions}

    def _ping(self, params, modern):
        return {}

    def _server_discover(self, params, modern):
        return {"supportedVersions": [MODERN, *LEGACY], "capabilities": self.capabilities(), "instructions": self.instructions,
                "_meta": {META_SERVER: self.info}, **_cache(True)}

    def _tools_list(self, params, modern):
        _no_cursor(params)
        return {"tools": [tool.describe() for tool in self.tools.values()], **_cache(modern)}

    def _tools_call(self, params, modern):
        tool = self.tools.get(params.get("name")) if isinstance(params.get("name"), str) else None
        if tool is None:
            raise RpcError(INVALID_PARAMS, f"Unknown tool: {clean_text(params.get('name'), 80)}")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            raise RpcError(INVALID_PARAMS, "Invalid params for tools/call: 'arguments' must be an object")
        problems = validate(arguments, tool.schema)
        if problems:
            return _tool_error("invalid arguments: " + "; ".join(problems[:8]))
        wait = self.rate.wait_needed()
        if wait > 0:
            return _tool_error(f"rate limit reached, retry in {wait:.0f} s")
        try:
            result = tool.handler(arguments)
            if not isinstance(result, dict):
                result = {"result": result}  # structured content is an object in every protocol version
            text = json.dumps(result, ensure_ascii=False, sort_keys=True)
        except ToolError as err:
            return _tool_error(clean_text(err, 600))
        except Exception as err:  # never let one failing tool end the session, never hand back a traceback
            self.log(traceback.format_exc())
            return _tool_error(f"the tool failed ({type(err).__name__}); nothing was returned")
        if len(text.encode("utf-8")) > self.max_result_bytes:
            return _tool_error(f"result of {len(text.encode('utf-8'))} bytes exceeds the limit of {self.max_result_bytes}; "
                               "narrow the request (smaller limit, shorter period) rather than receive a cut answer")
        return {"content": [{"type": "text", "text": text}], "structuredContent": result, "isError": False}

    def _resources_list(self, params, modern):
        _no_cursor(params)
        listed = [{k: v for k, v in r.items() if k != "loader"} for r in self.resources.values()]
        return {"resources": listed, **_cache(modern)}

    def _resources_templates_list(self, params, modern):
        _no_cursor(params)
        return {"resourceTemplates": [], **_cache(modern)}

    def _resources_read(self, params, modern):
        resource = self.resources.get(params.get("uri")) if isinstance(params.get("uri"), str) else None
        if resource is None:
            raise RpcError(INVALID_PARAMS if modern else LEGACY_RESOURCE_NOT_FOUND, "Resource not found")
        return {"contents": [{"uri": resource["uri"], "mimeType": resource["mimeType"], "text": resource["loader"]()}], **_cache(modern)}

    def _prompts_list(self, params, modern):
        _no_cursor(params)
        listed = [{k: v for k, v in p.items() if k != "render"} for p in self.prompts.values()]
        return {"prompts": listed, **_cache(modern)}

    def _prompts_get(self, params, modern):
        prompt = self.prompts.get(params.get("name")) if isinstance(params.get("name"), str) else None
        if prompt is None:
            raise RpcError(INVALID_PARAMS, f"Unknown prompt: {clean_text(params.get('name'), 80)}")
        given = params.get("arguments", {})
        if not isinstance(given, dict) or any(not isinstance(v, str) for v in given.values()):
            raise RpcError(INVALID_PARAMS, "prompt arguments must be an object of strings")
        missing = [a["name"] for a in prompt["arguments"] if a.get("required") and a["name"] not in given]
        if missing:
            raise RpcError(INVALID_PARAMS, f"Missing required arguments: {', '.join(missing)}")
        known = {a["name"] for a in prompt["arguments"]}
        text = prompt["render"]({k: clean_text(v, 200) for k, v in given.items() if k in known})
        return {"description": prompt["description"], "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}

    def _logging_setLevel(self, params, modern):
        return {}  # legacy clients may send it; this server logs to stderr only

    # Transport

    def serve(self, stdin=None, stdout=None):
        """Newline-delimited JSON on stdin and stdout until end of file. Only protocol messages reach stdout."""
        stdin, stdout = stdin or sys.stdin.buffer, stdout or sys.stdout.buffer
        while True:
            line = stdin.readline(MAX_LINE_BYTES + 1)
            if not line:
                return
            if len(line) > MAX_LINE_BYTES:
                while line and not line.endswith(b"\n"):  # drop the rest of the oversized line
                    line = stdin.readline(MAX_LINE_BYTES)
                response = _error(None, INVALID_REQUEST, "message too large")
            elif not line.strip():
                continue
            else:
                try:
                    response = self.handle(json.loads(line.decode("utf-8")))
                except (UnicodeDecodeError, ValueError):
                    response = _error(None, PARSE_ERROR, "Parse error")
            if response is not None:
                stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n")
                stdout.flush()


def _error(ident, code, message, data=None):
    body = {"code": code, "message": message}
    if data is not None:
        body["data"] = data
    return {"jsonrpc": "2.0", "id": ident, "error": body}


def _tool_error(text):
    return {"content": [{"type": "text", "text": text}], "isError": True}


def _cache(modern):
    return {"ttlMs": 300_000, "cacheScope": "public"} if modern else {}


def _no_cursor(params):
    if params.get("cursor") not in (None, ""):
        raise RpcError(INVALID_PARAMS, "Invalid cursor: this list has one page")
