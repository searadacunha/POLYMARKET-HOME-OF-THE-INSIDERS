"""Who paid a deposit: read from the Transfer logs of the deposit transaction only. Pure functions, no I/O.

A deposit credits a trading wallet with a collateral token (USDC, USDC.e, or pUSD since 2026). The payer is the address
the money came from inside that transaction: directly, or through the wrapping of USDC into pUSD, or through contracts
that pass the same amount along. Nothing here names a person: a payer is an address, and a bridge, an exchange wallet or
a relayer pays for thousands of unrelated people.
"""
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 40
USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
USDC_E = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
PUSD = "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"
STABLES = {USDC, USDC_E, PUSD}
# Polymarket's own contracts (docs.polymarket.com/resources/contracts, read 2026-11-14): never a payer.
INFRA = {PUSD, ZERO,
         "0x93070a847efef7f70739046a929d47a521f5b8ee",   # CollateralOnramp
         "0x2957922eb93258b93368531d39facca3b4dc5854",   # CollateralOfframp
         "0xebc2459ec962869ca4c0bd1e06368272732bcb08",   # PermissionedRamp
         "0xada100db00ca00073811820692005400218fce1f",   # CtfCollateralAdapter
         "0xada2005600dec949baf300f4c6120000bdb6eaab",   # NegRiskCtfCollateralAdapter
         "0xe111180000d2663c0091e4f400237545b87b996b",   # CTF Exchange
         "0xe2222d279d744050d28e00520010520000310f59",   # Neg Risk CTF Exchange
         "0xe3333700ca9d93003f00f0f71f8515005f6c00aa",   # ExchangeV3
         "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",   # earlier CTF Exchange
         "0xc5d563a36ae78145c45a50134d48a1215220f80a",   # earlier Neg Risk CTF Exchange
         "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",   # Conditional Tokens
         "0xd91e80cf2e7be2e162c6513ced06f1dd0da35296",   # Neg Risk Adapter
         "0x006f54f7f9a22e0000cc2ab60031000000ae9fef",   # PositionManager
         "0x12121212006e4cd160d18e3f00711da5c3372600"}   # Router


def transfers(logs):
    """ERC-20 transfers of the collateral tokens in a receipt, in log order: {token, from, to, value, log_index}."""
    out = []
    for log in logs:
        t = log.get("topics") or []
        if len(t) == 3 and t[0] == TRANSFER and log.get("address", "").lower() in STABLES and not log.get("removed"):
            out.append({"token": log["address"].lower(), "from": "0x" + t[1][-40:].lower(), "to": "0x" + t[2][-40:].lower(),
                        "value": int(log.get("data") or "0x0", 16), "log_index": int(log["logIndex"], 16) if log.get("logIndex") else None})
    return out


def payer_of_deposit(logs, wallet):
    """Payer of the money credited to `wallet` in this transaction, or None when no collateral reaches the wallet.
    Returns {payer, via, token, value, path}: via is 'direct' or 'wrapped' (USDC turned into pUSD for the wallet);
    path lists the contracts that only passed the same amount along. The largest credit is the one explained."""
    wallet = wallet.lower(); tr = transfers(logs)
    credits = [t for t in tr if t["to"] == wallet and t["value"] > 0]
    if not credits:
        return None
    c = max(credits, key=lambda t: t["value"])
    if c["from"] == ZERO or c["from"] in INFRA:                       # minted or released by the collateral system: find what was paid in
        src = next((t for t in tr if t["token"] in (USDC, USDC_E) and t["to"] in INFRA and t["from"] not in INFRA and t["value"] == c["value"]), None)
        if src is None:
            return {"payer": None, "via": "wrapped_unmatched", "token": c["token"], "value": c["value"], "path": []}
        found = {"payer": src["from"], "via": "wrapped", "token": src["token"], "value": src["value"], "path": []}
    else:
        found = {"payer": c["from"], "via": "direct", "token": c["token"], "value": c["value"], "path": []}
    for _ in range(6):                                                # contracts that received the same amount in this transaction
        prev = next((t for t in tr if t["to"] == found["payer"] and t["from"] != found["payer"] and t["value"] == found["value"]
                     and t["from"] not in INFRA and t["from"] != wallet), None)
        if prev is None:
            break
        found["path"].append(found["payer"]); found["payer"] = prev["from"]
    return found


def _log(token, src, dst, value, i=0):
    pad = lambda a: "0x" + "0" * 24 + a[2:]
    return {"address": token, "topics": [TRANSFER, pad(src), pad(dst)], "data": hex(value), "logIndex": hex(i)}


def _selftest():
    W, A, R = "0x" + "11" * 20, "0x" + "aa" * 20, "0x" + "bb" * 20
    assert payer_of_deposit([_log(USDC_E, A, W, 5_000_000)], W) == {"payer": A, "via": "direct", "token": USDC_E, "value": 5_000_000, "path": []}
    relay = [_log(USDC_E, A, R, 7, 0), _log(USDC_E, R, W, 7, 1)]
    assert payer_of_deposit(relay, W) == {"payer": A, "via": "direct", "token": USDC_E, "value": 7, "path": [R]}
    onramp = "0x93070a847efef7f70739046a929d47a521f5b8ee"
    wrapped = [_log(USDC, A, onramp, 9, 0), _log(PUSD, ZERO, W, 9, 1)]
    assert payer_of_deposit(wrapped, W) == {"payer": A, "via": "wrapped", "token": USDC, "value": 9, "path": []}
    assert payer_of_deposit([_log(PUSD, ZERO, W, 9, 1)], W)["via"] == "wrapped_unmatched"
    assert payer_of_deposit([_log(USDC, A, R, 9)], W) is None                           # nothing reaches the wallet
    other = "0x" + "99" * 20
    assert payer_of_deposit([_log(other, A, W, 9)], W) is None                          # look-alike token: ignored
    two = [_log(USDC_E, A, W, 1, 0), _log(USDC_E, R, W, 50, 1)]
    assert payer_of_deposit(two, W)["payer"] == R                                       # the largest credit is the deposit
    print("chainfund selftest ok")


if __name__ == "__main__":
    _selftest()
