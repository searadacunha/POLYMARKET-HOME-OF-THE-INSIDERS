import gzip
import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
SNAP = HOME / "snapshot"
UTC = timezone.utc
ZERO = "0x" + "0" * 40
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
WITHDRAWAL = "0xe9e508bad6d4c3227e881ca19068f099da81b5164dd6d62b2eaf1e8bc6c34931"
F2020 = "0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423"
CN22 = "0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a"
CN_HOT = {"0x975d9bd9928f398c7e01f6ba236816fa558cd94b", "0xa96be652a08d9905f15b7fbe2255708709becd09"}
TOKENS = {
    "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": ("USDC.e", 6),
    "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": ("USDC", 6),
    "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": ("USDT0", 6),
}
POOLS = {
    "0x1e34a77868e19a6647b1f2f47b51ed72dede95dd": 100,
    "0xdf231d99ff8b6c6cbf4e9b9a945cbacef9339178": 1000,
    "0xaf4c0b70b2ea9fb7487c7cbb37ada259579fe040": 10000,
    "0xa5c2254e4253490c54cef0a4347fddb8f75a4998": 100000,
}
STREAMS = ("changenow", "tornado")
LEVELS = ("CONFIRMED_DIRECT", "SUPPORTED_INDIRECT", "POSSIBLE", "UNKNOWN", "REFUTED")
SERVICES = {"changenow": "ChangeNOW", "tornado": "Tornado Cash"}
RPC = "https://polygon.gateway.tenderly.co"
PUBLICNODE = "https://polygon-bor-rpc.publicnode.com"


def week_date(s):
    if not re.fullmatch(r"[0-9]{4}-W[0-9]{2}", s):
        raise ValueError(f"invalid ISO week {s}")
    return date.fromisocalendar(int(s[:4]), int(s[-2:]), 1)


def week_of(t):
    return datetime.fromtimestamp(t, UTC).date().strftime("%G-W%V")


def bounds(w):
    start = int(datetime.combine(week_date(w), datetime.min.time(), UTC).timestamp())
    return start, start + 604800


def weeks(a, b):
    d, last = week_date(a), week_date(b)
    if d > last:
        raise ValueError("reversed week range")
    while d <= last:
        yield d.strftime("%G-W%V")
        d += timedelta(days=7)


def read(path):
    data = Path(path).read_bytes()
    if str(path).endswith(".gz"):
        data = gzip.decompress(data)
    return json.loads(data)


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        tmp = f.name
        try:
            f.write(data)
        except BaseException:
            os.unlink(tmp)
            raise
    os.replace(tmp, path)


def save(path, obj):
    data = (json.dumps(obj, separators=(",", ":"), ensure_ascii=True, sort_keys=True) + "\n").encode()
    atomic(path, gzip.compress(data, mtime=0) if str(path).endswith(".gz") else data)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hexstr(x, n):
    if not isinstance(x, str) or not re.fullmatch(rf"0x[0-9a-fA-F]{{{n}}}", x):
        raise ValueError(f"invalid {n}-nybble hex value")
    return x.lower()


def address_word(w):
    if w[:24] != "0" * 24:
        raise ValueError("invalid ABI address padding")
    return hexstr("0x" + w[24:], 40)


def addr_topic(a):
    return "0x" + "0" * 24 + hexstr(a, 40)[2:]


def query(stream):
    if stream == "tornado":
        return {"address": sorted(POOLS), "topics": [WITHDRAWAL]}
    if stream != "changenow":
        raise ValueError("unknown stream")
    senders = sorted(CN_HOT | {F2020, CN22})
    return {"address": sorted(TOKENS), "topics": [TRANSFER, [addr_topic(a) for a in senders]]}


ETH_RPC = "https://ethereum-rpc.publicnode.com"
ETH_GATEWAY = "https://mainnet.gateway.tenderly.co"
ETH_HOT = {"0xdd3d72c53ff982ff59853da71158bf1538b3ceee", "0xeba88149813bec1cccccfdb0dacefaaa5de94cb1"}
ETH_TOKENS = {
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": ("USDC", 6),
    "0xdac17f958d2ee523a2206206994597c13d831ec7": ("USDT", 6),
    "0x6b175474e89094c44da98b954eedeac495271d0f": ("DAI", 18),
}
ETH_POOLS = {
    "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc": ("native", 10**17),
    "0x47ce0c6ed5b0ce3d3a51fdb1c52dc66a7c3c2936": ("native", 10**18),
    "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf": ("native", 10**19),
    "0xa160cdab225685da1d56aa342ad8841c3b53f291": ("native", 10**20),
    "0x4736dcf1b7a3d580672cce6e7c65cd5cc9cfba9d": (
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        100 * 10**6,
    ),
    "0xd96f2b1c14db8458374d9aca76e26c3d18364307": (
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        1000 * 10**6,
    ),
}


def network_query(chain, stream):
    if chain == 137:
        return query(stream)
    if chain != 1 or stream not in STREAMS:
        raise ValueError("unregistered stream")
    if stream == "tornado":
        return {"address": sorted(ETH_POOLS), "topics": [WITHDRAWAL]}
    return {
        "address": sorted(ETH_TOKENS),
        "topics": [TRANSFER, [addr_topic(a) for a in sorted(ETH_HOT)]],
    }
