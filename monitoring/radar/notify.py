"""Optional notification of a newly sealed alert: a JSON POST to a webhook, or a Telegram message. Off unless an
environment variable is set (RADAR_WEBHOOK_URL, or RADAR_TELEGRAM_TOKEN and RADAR_TELEGRAM_CHAT). The message says
what the record says: an anomaly and its class's out-of-sample result, never an accusation. Only records sealed within
an hour of their trigger are sent (a first run over an old engine file sends nothing). A failed notification is
reported, not retried, and never blocks sealing."""
import json, os, urllib.request


def text(rec):
    o = rec["controls"]["out_of_sample"] or {}
    return (f"Radar {rec['risk']['class']} at {rec['trigger_utc']}: {rec['market']['question']} / {rec['market']['outcome']} "
            f"at {rec['price_and_depth']['price_at_alert']}. Anomaly in public data, not a finding about a person. "
            f"Class out of sample: {o.get('study_verdict') or o.get('status')}. Record {rec['id']}.")


def targets(env=None):
    env = os.environ if env is None else env
    out = []
    if env.get("RADAR_WEBHOOK_URL", "").startswith("https://"):          # a plain-http webhook is never used
        out.append(("webhook", env["RADAR_WEBHOOK_URL"]))
    if env.get("RADAR_TELEGRAM_TOKEN") and env.get("RADAR_TELEGRAM_CHAT"):
        out.append(("telegram", f"https://api.telegram.org/bot{env['RADAR_TELEGRAM_TOKEN']}/sendMessage"))
    return out


def send(rec, env=None, post=None):
    """[(target kind, 'sent' or error text)]; an empty list when nothing is configured."""
    env = os.environ if env is None else env
    post = post or (lambda url, body: urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(body).encode(),
                                                             headers={"Content-Type": "application/json"}), timeout=15).read())
    res = []
    for kind, url in targets(env):
        body = {"text": text(rec), "record_id": rec["id"]} if kind == "webhook" else {"chat_id": env["RADAR_TELEGRAM_CHAT"], "text": text(rec)}
        try:
            post(url, body); res.append((kind, "sent"))
        except Exception as e:                      # never blocks sealing; the token never appears in the error text
            res.append((kind, type(e).__name__))
    return res
