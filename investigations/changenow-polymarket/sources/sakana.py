#!/usr/bin/env python3
"""
Sakana Fugu client (Responses API) — Claude = hands, Fugu = brain.

Reads SAKANA_API_KEY / SAKANA_BASE_URL from ~/Downloads/.env (or env).
Default model fugu-ultra (multi-agent conductor) at reasoning.effort=xhigh.
Built-in web_search tool enabled by default (mandate: no invented addresses, cite sources).

CLI:
  python sakana.py --in case.md [--system sys.txt] [--model fugu-ultra]
                   [--effort xhigh] [--no-web] [--out out.json] [--timeout 900]
Prints the assistant text to stdout; full structured response saved to --out.
"""
import os, sys, json, time, argparse, urllib.request, urllib.error

ENV_PATH = os.path.expanduser("~/Downloads/.env")

def load_env():
    cfg = {}
    try:
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    key = os.environ.get("SAKANA_API_KEY") or cfg.get("SAKANA_API_KEY")
    base = os.environ.get("SAKANA_BASE_URL") or cfg.get("SAKANA_BASE_URL") or "https://api.sakana.ai/v1"
    if not key:
        raise SystemExit("SAKANA_API_KEY not found in env or .env")
    return key, base.rstrip("/")

def respond(input_text, model="fugu-ultra", effort="xhigh", web_search=True,
            system=None, timeout=900, max_retries=3, verbose=True):
    key, base = load_env()
    url = f"{base}/responses"
    body = {"model": model, "input": input_text, "reasoning": {"effort": effort}}
    if system:
        body["instructions"] = system
    if web_search:
        body["tools"] = [{"type": "web_search"}]
    data = json.dumps(body).encode()
    last_err = None
    for attempt in range(1, max_retries + 1):
        t0 = time.time()
        try:
            req = urllib.request.Request(url, data=data, method="POST", headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode()
            obj = json.loads(raw)
            if verbose:
                dt = time.time() - t0
                u = obj.get("usage", {})
                sys.stderr.write(f"[sakana {model} effort={effort} {dt:.1f}s "
                                 f"in={u.get('input_tokens','?')} out={u.get('output_tokens','?')}]\n")
            return obj
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()[:800]
            last_err = f"HTTP {e.code}: {err_body}"
            # 4xx (except 429) are not retryable
            if 400 <= e.code < 500 and e.code != 429:
                raise SystemExit(f"[sakana fatal] {last_err}")
            sys.stderr.write(f"[sakana retry {attempt}/{max_retries}] {last_err}\n")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = repr(e)
            sys.stderr.write(f"[sakana retry {attempt}/{max_retries}] {last_err}\n")
        time.sleep(min(30, 5 * attempt))
    raise SystemExit(f"[sakana failed after {max_retries}] {last_err}")

def extract(obj):
    """Return dict: text, reasoning_summaries[], web_searches[], usage."""
    text_parts, reasoning, searches = [], [], []
    for item in obj.get("output", []):
        t = item.get("type")
        if t == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    text_parts.append(c.get("text", ""))
        elif t == "reasoning":
            for s in item.get("summary", []):
                if s.get("type") == "summary_text":
                    reasoning.append(s.get("text", ""))
        elif t == "web_search_call":
            act = item.get("action", {})
            searches.append(act.get("query") or act.get("queries"))
    return {
        "text": "\n".join(text_parts).strip(),
        "reasoning_summaries": reasoning,
        "web_searches": searches,
        "usage": obj.get("usage", {}),
        "id": obj.get("id"),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True)
    ap.add_argument("--system", dest="sysfile", default=None)
    ap.add_argument("--model", default="fugu-ultra")
    ap.add_argument("--effort", default="xhigh")
    ap.add_argument("--no-web", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()
    with open(a.infile) as f:
        inp = f.read()
    system = None
    if a.sysfile:
        with open(a.sysfile) as f:
            system = f.read()
    obj = respond(inp, model=a.model, effort=a.effort, web_search=not a.no_web,
                  system=system, timeout=a.timeout)
    ex = extract(obj)
    if a.out:
        with open(a.out, "w") as f:
            json.dump({"request_model": a.model, "effort": a.effort,
                       "parsed": ex, "raw": obj}, f, indent=2)
        sys.stderr.write(f"[saved {a.out}]\n")
    if ex["web_searches"]:
        sys.stderr.write(f"[web_searches: {json.dumps(ex['web_searches'])[:500]}]\n")
    print(ex["text"])

if __name__ == "__main__":
    main()
