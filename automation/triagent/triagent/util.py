"""HTTP with failure classification, JSON extraction and a small JSON-Schema validator."""
from __future__ import annotations

import json
import re
import socket
import time
import urllib.error
import urllib.request
from typing import Any

USER_AGENT = "triagent-research/1.0 (read-only)"


class ProviderError(Exception):
    """kind: transient (safe to retry), uncertain (may have run and been billed),
    auth (missing/expired credential), permanent (bad request or bad data)."""

    def __init__(self, kind: str, message: str, status: int | None = None, retry_after: float | None = None):
        super().__init__(message)
        self.kind, self.status, self.retry_after = kind, status, retry_after


def http(url: str, *, method: str = "GET", body: Any = None, headers: dict | None = None,
         timeout: float = 60, max_bytes: int = 20_000_000) -> tuple[int, bytes]:
    data = None if body is None else json.dumps(body).encode()
    hdr = {"accept": "application/json", "user-agent": USER_AGENT, **(headers or {})}
    if data is not None:
        hdr["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=hdr)
    sent = False
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            sent = True
            return resp.status, resp.read(max_bytes)
    except urllib.error.HTTPError as exc:
        payload = exc.read(4000).decode("utf-8", "replace")
        retry = exc.headers.get("Retry-After") if exc.headers else None
        try:
            retry_s = float(retry) if retry else None
        except ValueError:
            retry_s = None
        if exc.code in (401, 403):
            raise ProviderError("auth", f"HTTP {exc.code}: {payload[:300]}", exc.code) from None
        if exc.code in (408, 429, 503):
            raise ProviderError("transient", f"HTTP {exc.code}: {payload[:300]}", exc.code, retry_s) from None
        if exc.code >= 500:
            raise ProviderError("uncertain", f"HTTP {exc.code}: {payload[:300]}", exc.code, retry_s) from None
        raise ProviderError("permanent", f"HTTP {exc.code}: {payload[:300]}", exc.code) from None
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, (ConnectionRefusedError, socket.gaierror)):
            raise ProviderError("transient", f"network: {reason}") from None
        raise ProviderError("uncertain" if data is not None else "transient", f"network: {reason}") from None
    except (TimeoutError, socket.timeout, ConnectionResetError) as exc:
        # A POST that timed out may still be processed (and billed) by the provider.
        raise ProviderError("uncertain" if (data is not None or sent) else "transient", f"timeout: {exc}") from None


def get_json(url: str, *, retries: int = 3, timeout: float = 30, **kw) -> Any:
    """Idempotent GET with bounded exponential backoff on transient failures."""
    for attempt in range(retries + 1):
        try:
            status, raw = http(url, timeout=timeout, **kw)
            return json.loads(raw)
        except ProviderError as exc:
            if exc.kind not in ("transient", "uncertain") or attempt == retries:
                raise
            time.sleep(min(60.0, exc.retry_after or 2.0 * 2 ** attempt))
        except json.JSONDecodeError as exc:
            raise ProviderError("permanent", f"invalid JSON from {url.split('?')[0]}: {exc}") from None


def extract_json(text: str) -> dict:
    """Parse a JSON object from model text; accepts a fenced block or surrounding prose."""
    text = (text or "").strip()
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    for candidate in [*fenced, text]:
        try:
            value = json.loads(candidate)
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        value = json.loads(text[start:end + 1])
        if isinstance(value, dict):
            return value
    raise ValueError("no JSON object in text")


_TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}


def validate(value: Any, schema: dict, path: str = "$") -> list[str]:
    """Validate the JSON-Schema subset used by our strict schemas. Returns error strings."""
    errors: list[str] = []
    types = schema.get("type")
    if types:
        allowed = types if isinstance(types, list) else [types]
        ok = any((t == "null" and value is None) or
                 (t != "null" and isinstance(value, _TYPES[t]) and not (t in ("integer", "number") and isinstance(value, bool)))
                 for t in allowed)
        if not ok:
            return [f"{path}: expected {allowed}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in enum")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    if isinstance(value, str) and "maxLength" in schema and len(value) > schema["maxLength"]:
        errors.append(f"{path}: too long")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}.{req}: missing")
        if schema.get("additionalProperties") is False:
            errors += [f"{path}.{k}: not allowed" for k in value if k not in props]
        for k, v in value.items():
            if k in props:
                errors += validate(v, props[k], f"{path}.{k}")
    if isinstance(value, list):
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: too many items")
        if "items" in schema:
            for i, item in enumerate(value):
                errors += validate(item, schema["items"], f"{path}[{i}]")
    return errors


SECRET_PATTERNS = [re.compile(p) for p in (
    r"sk-[A-Za-z0-9_\-]{16,}", r"xai-[A-Za-z0-9_\-]{16,}", r"sk-ant-[A-Za-z0-9_\-]{16,}",
    r"(?i)(api[_-]?key|apikey|token|secret|passphrase)=([^&\s]+)", r"(?i)bearer\s+[A-Za-z0-9._\-]{12,}")]


def redact(text: str, secrets: list[str] | None = None) -> str:
    """Remove known secret values and common key shapes from text bound for logs or models."""
    out = str(text)
    for value in secrets or []:
        if value and len(value) >= 8:
            out = out.replace(value, "[REDACTED]")
    for pat in SECRET_PATTERNS:
        out = pat.sub(lambda m: (m.group(1) + "=[REDACTED]") if m.lastindex and m.lastindex >= 2 else "[REDACTED]", out)
    return out
