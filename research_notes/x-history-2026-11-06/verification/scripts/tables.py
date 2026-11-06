"""Derived tables from raw objects kept outside git: data/x_posts.csv and data/profiles.csv.

X posts: ID, author, time, edit history, quoted post, sha256 of the embed object and of its images, and a short
paraphrase (the post text itself is third-party content and is not copied). Profiles: address, name, creation time,
declared X username and sha256 (no other profile field).
"""
import csv, hashlib, json, os
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RAW = Path(os.environ.get("XLEADS_RAW", Path.home() / "Projects/Polymarket-x-leads-raw-20261106/raw"))
CLAIMS = {
    "2111149784858042762": "Ranking Kane 1, Mbappé 2, Yamal 3, Rodri 4, Messi 5, labelled as the author's prediction; image with the same order",
    "2112913244058755159": "Says Kane will win, that he profited on Yamal Yes near 23% before the insiders got in, then starts on potential insiders (truncated)",
    "2104609132737114240": "Thread start: argues for Yamal, entered at 22%",
    "2115072247618531466": "Says they were insiders, that he called the top 5 in order early, and closed his positions before the end",
    "2110285369748963671": "Expects a surprising result and points to someone who bought 66k shares; images: Mbappé-or-Yamal chart and the Thin-Disclaimer-Life profile (66,799.6 Mbappé, 3,916.4 Rodri). Long text truncated in the embed",
    "2007351724185461007": "Lists three wallets: SBET365 0x6baf05d1..., PURE698 0x2a1a80e7..., JamWil23 0xfddfd657... (reply in a thread)",
    "2034030676589351244": "Claims one person made $2.14M with 38 accounts on a US strike on Iran; image lists 38 profile names with PnL",
    "2034374844746526837": "Claims the top PnL account of the US-strikes-Iran market (+$500k) probably belongs to the same person",
    "2027633061949501704": "Automated whale alert: cashy buys Yes on US strikes Iran by February 28, 2026",
    "1935769781669437727": "flydartball all-in $573k on US to attack Iran by July; image shows an unrealized loss",
    "2021095225393873035": "Correction: the account highlighted by PredictFolio was not an insider and is down $160K; image shows thesecondhighlander",
    "2020936742937952644": "PredictFolio: a returning trader bet $100K that the US strikes Iran today",
}
PROFILES_EXTRA = ["0xab05ffa436861ebb59e16f407703e009fe78e30f", "0x51633638f2f26deab4a9b2264ea4563406722b55", "0x8a93f77d5baeffeae691bb8b8c641b0341f841b2",
                  "0xfd74d4504299cce1c537464bdd932f8a0e6ba2a7", "0x805a922574d7d6b158b7bbb49a6fa8925eb60635", "0x1caa6a7ad0c6916aef7b67946de2e57ad24846a0"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def x_posts():
    rows = []
    for tid, claim in CLAIMS.items():
        p = RAW / "x/embed" / f"{tid}.json"
        t = json.loads(p.read_bytes())
        meta = json.loads((RAW / "x/embed" / f"{tid}.meta.json").read_text())
        media = [m["media_url_https"].rsplit("/", 1)[1] for m in t.get("mediaDetails") or [] if m.get("type") == "photo"]
        ec = t.get("edit_control") or {}
        rows.append({"post_id": tid, "author": t["user"]["screen_name"], "created_at_utc": t["created_at"],
                     "edit_tweet_ids": "|".join(ec.get("edit_tweet_ids", [])), "never_edited": ec.get("edit_tweet_ids") == [tid],
                     "long_text_truncated": "note_tweet" in t, "quoted_post": (t.get("quoted_tweet") or {}).get("id_str", ""),
                     "reply_to": t.get("in_reply_to_status_id_str") or "", "embed_sha256": sha(p), "embed_fetched_utc": meta["fetched_utc"],
                     "media": "|".join(f"{m}:{sha(RAW / 'x/media' / m)}" for m in media if (RAW / "x/media" / m).exists()),
                     "claim_paraphrased": claim})
    with open(HERE / "data/x_posts.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return len(rows)


def profiles():
    want = [l.strip() for l in (HERE / "data/g38_resolved_proxies.txt").read_text().splitlines() if l.strip()]
    want += [r["proxy"] for r in csv.DictReader(open(HERE / "data/focus_wallets.csv"))] + PROFILES_EXTRA
    rows = []
    for a in dict.fromkeys(want):
        p = next((c for c in (RAW / "polymarket" / a / "profile.json", RAW / "profiles" / f"{a}.json") if c.exists()), None)
        if not p:
            rows.append({"proxy": a, "name": "", "created_at": "", "x_username": "", "profile_sha256": "", "status": "NOT_SERVED_OR_NOT_FETCHED"}); continue
        d = json.loads(p.read_bytes())
        rows.append({"proxy": a, "name": d.get("name", ""), "created_at": d.get("createdAt", ""), "x_username": d.get("xUsername", ""),
                     "profile_sha256": sha(p), "status": "OK"})
    with open(HERE / "data/profiles.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return len(rows)


if __name__ == "__main__":
    print(x_posts(), "posts,", profiles(), "profiles")
