"""USD value at the time of each transaction, from DeFiLlama's public price history. No stablecoin is set to 1 by rule.

A token is recognised when DeFiLlama prices its contract with confidence 0.9 or more; look-alike tokens that copy a
symbol have no such price and are counted apart, never valued. Every price used is kept with its own timestamp.
"""
import json
import os
import time
import urllib.parse
from pathlib import Path

from phi_monitor import net

from . import chainio as io

API = "https://coins.llama.fi"
NATIVE = {"ETH": "coingecko:ethereum", "POL": "coingecko:polygon-ecosystem-token", "BNB": "coingecko:binancecoin", "AVAX": "coingecko:avalanche-2"}
MIN_CONFIDENCE = 0.9
SEARCH = "1h"              # a price further than this from the transaction is refused


def coin(chain, token):
    return NATIVE[io.CHAINS[chain]["native"]] if token == "native" else f"{io.CHAINS[chain]['llama']}:{token}"


class Book:
    """Price cache on disk: recognised tokens and every (coin, timestamp) price served."""

    def __init__(self, path):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text()) if self.path.exists() else dict(tokens={}, points={})

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data))
        os.replace(tmp, self.path)

    def recognise(self, chain, tokens):
        """{token: dict(symbol, decimals)} for the tokens DeFiLlama prices with confidence; others are absent."""
        want = [t for t in tokens if coin(chain, t) not in self.data["tokens"]]
        for part in io.chunks(sorted(want), 60):
            got = net.get_json(f"{API}/prices/current/" + ",".join(coin(chain, t) for t in part))["coins"]
            time.sleep(0.3)
            for t in part:
                c = got.get(coin(chain, t))
                ok = c is not None and c.get("confidence", 0) >= MIN_CONFIDENCE
                self.data["tokens"][coin(chain, t)] = dict(symbol=c.get("symbol"), decimals=18 if t == "native" else c.get("decimals")) if ok else None
        self.save()
        return {t: self.data["tokens"][coin(chain, t)] for t in tokens if self.data["tokens"].get(coin(chain, t))}

    def at(self, chain, token, ts):
        """(price, price_timestamp) nearest to `ts` within the search width. Raises when no price is served."""
        key = f"{coin(chain, token)}@{int(ts)}"
        if key not in self.data["points"]:
            got = net.get_json(f"{API}/prices/historical/{int(ts)}/{coin(chain, token)}?searchWidth={SEARCH}")["coins"].get(coin(chain, token))
            time.sleep(0.2)
            if not got or got.get("confidence", 0) < MIN_CONFIDENCE:
                raise net.SourceError(f"no price for {coin(chain, token)} at {ts}")
            self.data["points"][key] = [got["price"], got["timestamp"]]
            self.save()
        return tuple(self.data["points"][key])

    def hourly(self, chain, tokens, start, end):
        """{token: {hour_start: price}} for population totals, one price an hour. A token without a point for an hour
        has no entry for it, and the transfers of that hour stay unvalued and counted."""
        hours = list(range(start - start % 3600, end, 3600))
        out = {}
        for t in tokens:
            c = coin(chain, t)
            have = self.data["points"]
            missing = [h for h in hours if f"{c}@h{h}" not in have]
            for part in io.chunks(missing, 80):
                q = urllib.parse.quote(json.dumps({c: part}))
                got = net.get_json(f"{API}/batchHistorical?coins={q}&searchWidth=1800")["coins"].get(c, {}).get("prices", [])
                time.sleep(0.3)
                for h in part:
                    near = min(got, key=lambda p: abs(p["timestamp"] - h), default=None)
                    have[f"{c}@h{h}"] = [near["price"], near["timestamp"]] if near and abs(near["timestamp"] - h) <= 1800 else None
            out[t] = {h: have[f"{c}@h{h}"][0] for h in hours if have.get(f"{c}@h{h}")}
        self.save()
        return out
