"""Minimal RFC 6455 WebSocket client, Python standard library only (socket + ssl).
Handshake, masked client frames, ping/pong, fragmented messages, close, reconnect with backoff.
Only the public market channel is used with it. The authenticated user channel shows one's own orders only and is never opened.
Self-test (offline): tests/test_units.py replays recorded frames from fixtures/ws_frames.json.
"""
import base64, hashlib, json, os, socket, ssl, struct, sys, time, urllib.parse

GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
OP_CONT, OP_TEXT, OP_BIN, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA


class WSError(Exception):
    pass


def encode_frame(opcode, payload=b"", fin=True, mask=True):
    """Build one frame. Client frames MUST be masked (RFC 6455 5.3)."""
    b0 = (0x80 if fin else 0) | opcode
    n = len(payload)
    m = 0x80 if mask else 0
    if n < 126:
        head = struct.pack("!BB", b0, m | n)
    elif n < 65536:
        head = struct.pack("!BBH", b0, m | 126, n)
    else:
        head = struct.pack("!BBQ", b0, m | 127, n)
    if not mask:
        return head + payload
    key = os.urandom(4)
    return head + key + bytes(b ^ key[i & 3] for i, b in enumerate(payload))


def parse_frame(buf):
    """Return (fin, opcode, payload, consumed) or None when buf holds an incomplete frame."""
    if len(buf) < 2:
        return None
    b0, b1 = buf[0], buf[1]
    fin, opcode, masked, n, pos = bool(b0 & 0x80), b0 & 0x0F, bool(b1 & 0x80), b1 & 0x7F, 2
    if n == 126:
        if len(buf) < 4: return None
        n = struct.unpack("!H", buf[2:4])[0]; pos = 4
    elif n == 127:
        if len(buf) < 10: return None
        n = struct.unpack("!Q", buf[2:10])[0]; pos = 10
    key = b""
    if masked:
        if len(buf) < pos + 4: return None
        key = buf[pos:pos + 4]; pos += 4
    if len(buf) < pos + n:
        return None
    payload = bytes(buf[pos:pos + n])
    if masked:
        payload = bytes(b ^ key[i & 3] for i, b in enumerate(payload))
    return fin, opcode, payload, pos + n


class WS:
    """One connection. recv() returns (kind, data, t_local) with kind in text|binary|close|timeout."""

    def __init__(self, url, headers=None, connect_timeout=15, read_timeout=1.0):
        self.url, self.headers, self.ct, self.rt = url, headers or {}, connect_timeout, read_timeout
        self.sock, self.buf, self.frag, self.frag_op, self.closed = None, bytearray(), bytearray(), None, False
        self.handshake_headers = {}

    def connect(self):
        u = urllib.parse.urlparse(self.url)
        host, port = u.hostname, u.port or (443 if u.scheme == "wss" else 80)
        raw = socket.create_connection((host, port), timeout=self.ct)
        self.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=host) if u.scheme == "wss" else raw
        key = base64.b64encode(os.urandom(16)).decode()
        path = (u.path or "/") + ("?" + u.query if u.query else "")
        req = (f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n"
               f"User-Agent: Mozilla/5.0 (compatible; research-client/1.0)\r\n"
               + "".join(f"{k}: {v}\r\n" for k, v in self.headers.items()) + "\r\n")
        self.sock.sendall(req.encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = self.sock.recv(4096)
            if not chunk: raise WSError("closed during handshake")
            resp += chunk
            if len(resp) > 65536: raise WSError("handshake too large")
        head, _, rest = resp.partition(b"\r\n\r\n")
        lines = head.decode("latin1").split("\r\n")
        if " 101 " not in lines[0] + " ": raise WSError("handshake refused: " + lines[0])
        hdr = {l.split(":", 1)[0].strip().lower(): l.split(":", 1)[1].strip() for l in lines[1:] if ":" in l}
        want = base64.b64encode(hashlib.sha1(key.encode() + GUID).digest()).decode()
        if hdr.get("sec-websocket-accept") != want: raise WSError("bad Sec-WebSocket-Accept")
        self.handshake_headers, self.buf, self.closed = hdr, bytearray(rest), False
        self.sock.settimeout(self.rt)
        return hdr

    def send(self, text_or_bytes, opcode=None):
        data = text_or_bytes.encode() if isinstance(text_or_bytes, str) else text_or_bytes
        op = opcode if opcode is not None else (OP_TEXT if isinstance(text_or_bytes, str) else OP_BIN)
        self.sock.sendall(encode_frame(op, data))

    def ping(self, payload=b""):
        self.sock.sendall(encode_frame(OP_PING, payload))

    def close(self, code=1000):
        try:
            if not self.closed: self.sock.sendall(encode_frame(OP_CLOSE, struct.pack("!H", code)))
        except OSError:
            pass
        self.closed = True
        try: self.sock.close()
        except OSError: pass

    def recv(self):
        """Next complete message. Answers ping with pong, reassembles fragments."""
        while True:
            fr = parse_frame(self.buf)
            if fr is None:
                try:
                    chunk = self.sock.recv(65536)
                except (socket.timeout, ssl.SSLWantReadError):
                    return "timeout", None, time.time()
                if not chunk:
                    self.closed = True
                    return "close", b"eof without close frame", time.time()
                self.buf += chunk
                continue
            fin, op, payload, used = fr
            del self.buf[:used]
            t = time.time()
            if op == OP_PING:
                self.sock.sendall(encode_frame(OP_PONG, payload)); continue
            if op == OP_PONG:
                return "pong", payload, t
            if op == OP_CLOSE:
                self.closed = True
                try: self.sock.sendall(encode_frame(OP_CLOSE, payload[:2]))
                except OSError: pass
                return "close", payload, t
            if op in (OP_TEXT, OP_BIN):
                if fin: return ("text" if op == OP_TEXT else "binary"), payload, t
                self.frag, self.frag_op = bytearray(payload), op; continue
            if op == OP_CONT:
                if self.frag_op is None: raise WSError("continuation without start")
                self.frag += payload
                if fin:
                    data, o = bytes(self.frag), self.frag_op
                    self.frag, self.frag_op = bytearray(), None
                    return ("text" if o == OP_TEXT else "binary"), data, t
                continue
            raise WSError(f"unknown opcode {op}")


def run_forever(url, on_open, on_msg, stop_at, ping_every=None, ping_text="PING", headers=None, log=print, silence_timeout=None, ping_frames=False):
    """Connect, call on_open(ws), feed on_msg(kind, data, t) until stop_at (epoch). Reconnect with exponential
    backoff (1,2,4,... capped 30 s). silence_timeout: reconnect when no frame at all arrived for that many seconds (a server can
    stall without closing the TCP connection). ping_frames: also send RFC 6455 protocol ping frames every ping_every seconds.
    Returns the list of connection events [(t, event, detail)]."""
    events, backoff = [], 1.0
    while time.time() < stop_at:
        ws = WS(url, headers)
        try:
            ws.connect(); events.append((time.time(), "connected", ws.handshake_headers.get("date", "")))
            backoff = 1.0
            on_open(ws)
            last_ping = last_rx = time.time()
            while time.time() < stop_at:
                kind, data, t = ws.recv()
                if kind == "close":
                    events.append((t, "close", repr(data[:60]))); break
                if kind != "timeout":
                    on_msg(kind, data, t)
                    if kind == "text" and data[:1] in (b"{", b"["): last_rx = time.time()   # keep-alive replies do not count as delivery
                if ping_every and time.time() - last_ping >= ping_every:
                    ws.send(ping_text)
                    if ping_frames: ws.ping(b"hb")
                    last_ping = time.time()
                if silence_timeout and time.time() - last_rx > silence_timeout:
                    events.append((time.time(), "silence_reconnect", silence_timeout)); break
        except (OSError, WSError, ssl.SSLError) as e:
            events.append((time.time(), "error", repr(e)))
        finally:
            ws.close()
        if time.time() < stop_at:
            events.append((time.time(), "reconnect_wait", backoff))
            time.sleep(min(backoff, max(0, stop_at - time.time()))); backoff = min(backoff * 2, 30)
    return events


# ---------------- offline self-test ----------------
class _FakeSock:
    def __init__(self, chunks): self.chunks, self.sent = list(chunks), []
    def recv(self, n):
        if not self.chunks: return b""
        return self.chunks.pop(0)
    def sendall(self, b): self.sent.append(bytes(b))
    def close(self): pass


def _selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "fixtures", "ws_frames.json")) as f:
        fx = json.load(f)
    # 1. RFC 6455 section 5.7 examples: masked "Hello", unmasked "Hello"
    assert parse_frame(bytes.fromhex("818537fa213d7f9f4d5158"))[2] == b"Hello"
    assert parse_frame(bytes.fromhex("810548656c6c6f"))[2] == b"Hello"
    # 2. our encoder -> our parser round trip, all three length classes
    for n in (5, 300, 70000):
        p = os.urandom(n)
        f = parse_frame(encode_frame(OP_BIN, p))
        assert f[2] == p and f[1] == OP_BIN and f[0]
        assert encode_frame(OP_BIN, p)[1] & 0x80, "client frame must be masked"
    # 3. recorded frames from a live capture, split at awkward byte boundaries, with ping + fragmentation
    recorded = [bytes.fromhex(h) for h in fx["server_frames_hex"]]   # unmasked server frames, as captured
    ping = encode_frame(OP_PING, b"hb", mask=False)
    frag1 = encode_frame(OP_TEXT, b'{"a":', fin=False, mask=False)
    frag2 = encode_frame(OP_CONT, b'1}', fin=True, mask=False)
    stream = recorded[0] + frag1 + ping + frag2 + recorded[1] + encode_frame(OP_CLOSE, struct.pack("!H", 1000), mask=False)
    ws = WS("wss://x/y"); ws.sock = _FakeSock([stream[i:i + 7] for i in range(0, len(stream), 7)])
    out = []
    while True:
        k, d, _ = ws.recv(); out.append((k, d))
        if k == "close": break
    assert out[0] == ("text", bytes.fromhex(fx["server_payload_hex"][0])), out[0]
    assert out[1] == ("text", b'{"a":1}'), out[1]   # fragmented message with a ping in the middle
    assert out[2] == ("text", bytes.fromhex(fx["server_payload_hex"][1])), out[2]
    assert out[3][0] == "close"
    pong = ws.sock.sent[0]
    assert parse_frame(pong)[1] == OP_PONG and parse_frame(pong)[2] == b"hb" and pong[1] & 0x80, "pong must echo and be masked"
    assert any(parse_frame(s)[1] == OP_CLOSE for s in ws.sock.sent), "close must be echoed"
    # 4. handshake accept key from RFC 6455 section 1.3
    assert base64.b64encode(hashlib.sha1(b"dGhlIHNhbXBsZSBub25jZQ==" + GUID).digest()) == b"s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
    return len(recorded)


if __name__ == "__main__":
    _selftest()
