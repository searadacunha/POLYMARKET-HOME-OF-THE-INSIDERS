"""The protocol core, offline: both eras, every refusal, the stdio framing."""
import io
import json
import unittest

from phi_forensics.mcp import protocol as p

MODERN_META = {p.META_VERSION: p.MODERN, p.META_CAPABILITIES: {}}
ADDRESS = {"type": "string", "pattern": "0x[0-9a-fA-F]{40}"}


def boom(args):
    raise RuntimeError("secret path /Users/someone/.env")


def server(**kw):
    s = p.Server("test-server", "1.2.3", instructions="read me", log=lambda text: None, **kw)
    s.add_tool(p.Tool("echo", "Return the wallet.", lambda a: {"wallet": a["wallet"], "limit": a.get("limit", 5)},
                      {"wallet": ADDRESS, "limit": {"type": "integer", "minimum": 1, "maximum": 50}}, required=["wallet"]))
    s.add_tool(p.Tool("refuse", "Always refuses.", lambda a: (_ for _ in ()).throw(p.ToolError("nothing found\x00‮"))))
    s.add_tool(p.Tool("boom", "Always crashes.", boom))
    s.add_tool(p.Tool("big", "Too much.", lambda a: {"rows": ["x" * 100] * 100}))
    s.add_tool(p.Tool("scalar", "Not an object.", lambda a: [1, 2]))
    s.add_resource("phi://doc", "doc", "A document.", lambda: "# Title")
    s.add_prompt("ask", "A prompt.", [{"name": "wallet", "description": "address", "required": True}], lambda a: f"Investigate {a['wallet']}")
    return s


def call(s, method, params=None, ident=1):
    message = {"jsonrpc": "2.0", "id": ident, "method": method}
    if params is not None:
        message["params"] = params
    return s.handle(message)


def legacy():
    s = server()
    call(s, "initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "c", "version": "0"}})
    return s


class Handshake(unittest.TestCase):
    def test_initialize_echoes_a_supported_version(self):
        for version in p.LEGACY:
            result = call(server(), "initialize", {"protocolVersion": version})["result"]
            self.assertEqual(result["protocolVersion"], version)
            self.assertEqual(result["serverInfo"], {"name": "test-server", "title": "test-server", "version": "1.2.3"})
            self.assertEqual(result["instructions"], "read me")
            self.assertIn("tools", result["capabilities"])
            self.assertNotIn("resultType", result)

    def test_initialize_answers_an_unknown_version_with_one_it_supports(self):
        for asked in ("1999-01-01", p.MODERN, None, 7):
            self.assertEqual(call(server(), "initialize", {"protocolVersion": asked})["result"]["protocolVersion"], p.LEGACY[0])

    def test_initialize_with_modern_meta_is_still_the_legacy_handshake(self):
        result = call(server(), "initialize", {"protocolVersion": "2025-11-25", "_meta": MODERN_META})["result"]
        self.assertNotIn("resultType", result)

    def test_a_request_from_neither_era_is_refused_with_both_ways_in(self):
        error = call(server(), "tools/list")["error"]
        self.assertEqual(error["code"], p.INVALID_PARAMS)
        self.assertIn("initialize", error["message"])
        self.assertIn(p.META_VERSION, error["message"])

    def test_ping_works_before_initialize(self):
        self.assertEqual(call(server(), "ping")["result"], {})

    def test_modern_request_needs_no_handshake_and_is_marked_complete(self):
        result = call(server(), "tools/list", {"_meta": MODERN_META})["result"]
        self.assertEqual((result["resultType"], result["ttlMs"], result["cacheScope"]), ("complete", 300_000, "public"))
        self.assertEqual([t["name"] for t in result["tools"]], ["echo", "refuse", "boom", "big", "scalar"])

    def test_modern_unsupported_version_names_the_supported_ones(self):
        error = call(server(), "tools/list", {"_meta": {p.META_VERSION: "1900-01-01", p.META_CAPABILITIES: {}}})["error"]
        self.assertEqual(error["code"], p.UNSUPPORTED_VERSION)
        self.assertEqual(error["data"], {"supported": [p.MODERN, *p.LEGACY], "requested": "1900-01-01"})

    def test_modern_request_without_client_capabilities_is_malformed(self):
        self.assertEqual(call(server(), "tools/list", {"_meta": {p.META_VERSION: p.MODERN}})["error"]["code"], p.INVALID_PARAMS)

    def test_discover(self):
        result = call(server(), "server/discover", {"_meta": MODERN_META})["result"]
        self.assertEqual(result["supportedVersions"][0], p.MODERN)
        self.assertEqual(result["_meta"][p.META_SERVER]["name"], "test-server")
        self.assertEqual((result["resultType"], result["cacheScope"]), ("complete", "public"))
        self.assertIn("ttlMs", result)

    def test_one_process_serves_both_eras(self):
        s = legacy()
        self.assertNotIn("resultType", call(s, "tools/list")["result"])
        self.assertEqual(call(s, "tools/list", {"_meta": MODERN_META})["result"]["resultType"], "complete")


class Envelope(unittest.TestCase):
    def test_notifications_get_no_answer(self):
        s = server()
        for method in ("notifications/initialized", "notifications/cancelled", "notifications/unknown", "tools/list", 5):
            self.assertIsNone(s.handle({"jsonrpc": "2.0", "method": method}))

    def test_a_response_from_the_client_is_ignored(self):
        self.assertIsNone(server().handle({"jsonrpc": "2.0", "id": 1, "result": {}}))

    def test_malformed_envelopes(self):
        s = legacy()
        for message in ([], "x", 3, None, [{"jsonrpc": "2.0", "id": 1, "method": "ping"}]):
            self.assertEqual(s.handle(message)["error"]["code"], p.INVALID_REQUEST)
        for ident in (None, True, 1.5, [1], {}):
            response = s.handle({"jsonrpc": "2.0", "id": ident, "method": "ping"})
            self.assertEqual((response["error"]["code"], response["id"]), (p.INVALID_REQUEST, None))
        for message in ({"id": 1, "method": "ping"}, {"jsonrpc": "1.0", "id": 1, "method": "ping"},
                        {"jsonrpc": "2.0", "id": 1, "method": 5}, {"jsonrpc": "2.0", "id": 1, "method": None},
                        {"jsonrpc": "2.0", "id": 1, "method": ["ping"]}):
            self.assertEqual(s.handle(message)["error"]["code"], p.INVALID_REQUEST)
        for params in ([], "x", 3, None):
            self.assertEqual(call(s, "tools/list", params if params is not None else [None])["error"]["code"], p.INVALID_PARAMS)

    def test_unknown_methods_are_not_found_and_private_names_are_not_reachable(self):
        s = legacy()
        for method in ("tools/delete", "handle", "serve", "__class__", "_tools_call", "tools_call", "TOOLS/LIST", ""):
            self.assertEqual(call(s, method)["error"]["code"], p.METHOD_NOT_FOUND, method)

    def test_string_ids_are_kept(self):
        self.assertEqual(call(legacy(), "ping", ident="abc")["id"], "abc")

    def test_a_cursor_is_refused_because_lists_have_one_page(self):
        self.assertEqual(call(legacy(), "tools/list", {"cursor": "next"})["error"]["code"], p.INVALID_PARAMS)
        self.assertIn("tools", call(legacy(), "tools/list", {"cursor": ""})["result"])


class Tools(unittest.TestCase):
    WALLET = "0x" + "ab" * 20

    def test_a_tool_is_described_as_read_only(self):
        tool = call(legacy(), "tools/list")["result"]["tools"][0]
        self.assertEqual(tool["annotations"]["readOnlyHint"], True)
        self.assertEqual(tool["annotations"]["destructiveHint"], False)
        self.assertEqual(tool["inputSchema"]["additionalProperties"], False)
        self.assertEqual(tool["inputSchema"]["required"], ["wallet"])

    def test_call_returns_text_and_structured_content(self):
        result = call(legacy(), "tools/call", {"name": "echo", "arguments": {"wallet": self.WALLET}})["result"]
        self.assertEqual(result["isError"], False)
        self.assertEqual(result["structuredContent"], {"wallet": self.WALLET, "limit": 5})
        self.assertEqual(json.loads(result["content"][0]["text"]), result["structuredContent"])

    def test_unknown_tool_and_bad_argument_container_are_protocol_errors(self):
        s = legacy()
        for name in ("nope", None, 5, ["echo"]):
            error = call(s, "tools/call", {"name": name})["error"]
            self.assertEqual(error["code"], p.INVALID_PARAMS)
            self.assertIn("Unknown tool", error["message"])
        self.assertEqual(call(s, "tools/call", {"name": "echo", "arguments": []})["error"]["code"], p.INVALID_PARAMS)

    def test_invalid_arguments_are_tool_errors_the_model_can_correct(self):
        s = legacy()
        for arguments in ({}, {"wallet": "0x12"}, {"wallet": self.WALLET, "limit": 0}, {"wallet": self.WALLET, "limit": "5"},
                          {"wallet": self.WALLET, "limit": True}, {"wallet": self.WALLET, "extra": 1}, {"wallet": self.WALLET + "\n"}):
            result = call(s, "tools/call", {"name": "echo", "arguments": arguments})["result"]
            self.assertTrue(result["isError"], arguments)
            self.assertIn("invalid arguments", result["content"][0]["text"])

    def test_an_expected_failure_is_reported_cleaned(self):
        result = call(legacy(), "tools/call", {"name": "refuse"})["result"]
        self.assertEqual((result["isError"], result["content"][0]["text"]), (True, "nothing found"))

    def test_a_crash_is_reported_without_internals_and_the_server_keeps_serving(self):
        logged = []
        s = server()
        s.log = logged.append
        call(s, "initialize", {"protocolVersion": "2025-11-25"})
        result = call(s, "tools/call", {"name": "boom"})["result"]
        self.assertTrue(result["isError"])
        self.assertNotIn("secret", result["content"][0]["text"])
        self.assertIn("RuntimeError", result["content"][0]["text"])
        self.assertIn("secret path", logged[0])
        self.assertEqual(call(s, "ping")["result"], {})

    def test_an_oversized_result_is_refused_whole_never_cut(self):
        s = server(max_result_bytes=2_000)
        call(s, "initialize", {"protocolVersion": "2025-11-25"})
        result = call(s, "tools/call", {"name": "big"})["result"]
        self.assertTrue(result["isError"])
        self.assertIn("exceeds the limit", result["content"][0]["text"])
        self.assertNotIn("structuredContent", result)

    def test_a_result_that_is_not_an_object_is_wrapped(self):
        self.assertEqual(call(legacy(), "tools/call", {"name": "scalar"})["result"]["structuredContent"], {"result": [1, 2]})

    def test_the_rate_limit_refuses_then_recovers(self):
        now = [0.0]
        s = server(rate=p.RateLimit(calls=2, seconds=10, clock=lambda: now[0]))
        call(s, "initialize", {"protocolVersion": "2025-11-25"})
        ask = lambda: call(s, "tools/call", {"name": "echo", "arguments": {"wallet": self.WALLET}})["result"]
        self.assertFalse(ask()["isError"])
        self.assertFalse(ask()["isError"])
        refused = ask()
        self.assertTrue(refused["isError"])
        self.assertIn("retry in 10 s", refused["content"][0]["text"])
        now[0] = 10.5
        self.assertFalse(ask()["isError"])

    def test_invalid_arguments_do_not_consume_the_rate_limit(self):
        s = server(rate=p.RateLimit(calls=1, seconds=10, clock=lambda: 0.0))
        call(s, "initialize", {"protocolVersion": "2025-11-25"})
        call(s, "tools/call", {"name": "echo", "arguments": {}})
        self.assertFalse(call(s, "tools/call", {"name": "echo", "arguments": {"wallet": self.WALLET}})["result"]["isError"])


class ResourcesAndPrompts(unittest.TestCase):
    def test_resources(self):
        s = legacy()
        self.assertEqual(call(s, "resources/list")["result"]["resources"],
                         [{"uri": "phi://doc", "name": "doc", "description": "A document.", "mimeType": "text/markdown"}])
        self.assertEqual(call(s, "resources/read", {"uri": "phi://doc"})["result"]["contents"],
                         [{"uri": "phi://doc", "mimeType": "text/markdown", "text": "# Title"}])
        self.assertEqual(call(s, "resources/templates/list")["result"], {"resourceTemplates": []})

    def test_a_missing_resource_uses_the_code_of_each_era(self):
        s = legacy()
        for uri in ("phi://nope", "file:///etc/passwd", "../../etc/passwd", None, 5):
            self.assertEqual(call(s, "resources/read", {"uri": uri})["error"]["code"], p.LEGACY_RESOURCE_NOT_FOUND)
        self.assertEqual(call(s, "resources/read", {"uri": "phi://nope", "_meta": MODERN_META})["error"]["code"], p.INVALID_PARAMS)

    def test_prompts(self):
        s = legacy()
        self.assertEqual(call(s, "prompts/list")["result"]["prompts"][0]["name"], "ask")
        got = call(s, "prompts/get", {"name": "ask", "arguments": {"wallet": "0xabc‮", "ignored": "x"}})["result"]
        self.assertEqual(got["messages"], [{"role": "user", "content": {"type": "text", "text": "Investigate 0xabc"}}])
        self.assertEqual(call(s, "prompts/get", {"name": "ask"})["error"]["code"], p.INVALID_PARAMS)
        self.assertEqual(call(s, "prompts/get", {"name": "nope"})["error"]["code"], p.INVALID_PARAMS)
        self.assertEqual(call(s, "prompts/get", {"name": "ask", "arguments": {"wallet": 5}})["error"]["code"], p.INVALID_PARAMS)


class Validation(unittest.TestCase):
    def test_types(self):
        self.assertEqual(p.validate(True, {"type": "integer"}), ["arguments: expected integer"])
        self.assertEqual(p.validate(1.5, {"type": "integer"}), ["arguments: expected integer"])
        self.assertEqual(p.validate(1, {"type": "number"}), [])
        self.assertEqual(p.validate("1", {"type": "number"}), ["arguments: expected number"])
        self.assertEqual(p.validate(None, {"type": "string"}), ["arguments: expected string"])

    def test_constraints(self):
        self.assertTrue(p.validate("c", {"type": "string", "enum": ["a", "b"]}))
        self.assertTrue(p.validate("abc", {"type": "string", "maxLength": 2}))
        self.assertTrue(p.validate("", {"type": "string", "minLength": 1}))
        self.assertTrue(p.validate("x" * 10_001, {"type": "string"}))
        self.assertTrue(p.validate(11, {"type": "integer", "maximum": 10}))
        self.assertTrue(p.validate(-1, {"type": "integer", "minimum": 0}))
        self.assertEqual(p.validate(0, {"type": "integer", "minimum": 0, "maximum": 0}), [])

    def test_patterns_match_the_whole_string(self):
        schema = {"type": "string", "pattern": "0x[0-9a-f]{4}"}
        self.assertEqual(p.validate("0xabcd", schema), [])
        for bad in ("0xabcde", " 0xabcd", "0xabcd\n", "0xABCD"):
            self.assertTrue(p.validate(bad, schema), bad)

    def test_arrays_and_nested_objects(self):
        schema = {"type": "object", "properties": {"wallets": {"type": "array", "items": ADDRESS, "minItems": 2, "maxItems": 3}},
                  "required": ["wallets"], "additionalProperties": False}
        good = "0x" + "1" * 40
        self.assertEqual(p.validate({"wallets": [good, good]}, schema), [])
        self.assertTrue(p.validate({"wallets": [good]}, schema))
        self.assertTrue(p.validate({"wallets": [good] * 4}, schema))
        self.assertEqual(p.validate({"wallets": [good, "nope"]}, schema), ["arguments.wallets[1]: does not match 0x[0-9a-fA-F]{40}"])
        self.assertEqual(p.validate({}, schema), ["arguments.wallets: required"])

    def test_clean_text(self):
        self.assertEqual(p.clean_text("a\x00b\x1bc‮d⁦e\x7f"), "abcde")
        self.assertEqual(p.clean_text("line\nnext\ttab"), "line\nnext\ttab")
        self.assertEqual(p.clean_text("x" * 500, 10), "x" * 10 + "…")
        self.assertEqual(p.clean_text(12), "12")


class Stdio(unittest.TestCase):
    def run_lines(self, lines):
        out = io.BytesIO()
        server().serve(io.BytesIO(b"".join(lines)), out)
        raw = out.getvalue()
        self.assertTrue(raw.endswith(b"\n") or raw == b"")
        return [json.loads(line) for line in raw.splitlines()]

    def test_a_session(self):
        init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}}).encode()
        note = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode()
        listing = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}).encode()
        responses = self.run_lines([init + b"\n", note + b"\n", b"\n", b"   \n", listing + b"\r\n", b"{not json\n", b"\xff\xfe\n",
                                    b'{"jsonrpc":"2.0","id":3,"method":"ping"}'])
        self.assertEqual([r.get("id") for r in responses], [1, 2, None, None, 3])
        self.assertEqual([r["error"]["code"] for r in responses[2:4]], [p.PARSE_ERROR, p.PARSE_ERROR])
        self.assertEqual(responses[4]["result"], {})

    def test_every_response_is_one_line_even_when_text_holds_newlines(self):
        out = io.BytesIO()
        s = server()
        s.add_tool(p.Tool("multi", "Lines.", lambda a: {"text": "a\nb\r\nc d"}))
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "multi", "_meta": MODERN_META}}
        s.serve(io.BytesIO(json.dumps(request).encode() + b"\n"), out)
        self.assertEqual(out.getvalue().count(b"\n"), 1)
        self.assertEqual(json.loads(out.getvalue())["result"]["structuredContent"]["text"], "a\nb\r\nc d")

    def test_an_oversized_line_is_refused_and_the_next_one_is_served(self):
        huge = b'{"jsonrpc":"2.0","id":1,"method":"ping","params":{"x":"' + b"a" * (p.MAX_LINE_BYTES + 10) + b'"}}\n'
        responses = self.run_lines([huge, b'{"jsonrpc":"2.0","id":2,"method":"ping"}\n'])
        self.assertEqual(responses[0]["error"]["code"], p.INVALID_REQUEST)
        self.assertEqual(responses[1], {"jsonrpc": "2.0", "id": 2, "result": {}})

    def test_end_of_input_ends_the_server(self):
        self.assertEqual(self.run_lines([]), [])


if __name__ == "__main__":
    unittest.main()
