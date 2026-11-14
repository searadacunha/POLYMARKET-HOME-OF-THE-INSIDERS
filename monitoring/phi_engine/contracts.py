"""Contracts the engine reads, from docs.polymarket.com/resources/contracts (read 2026-11-14) and from live logs.

Three exchanges emit the same OrderFilled event. The third, ExchangeV3 of Polymarket Protocol V2, already carried about
1 % of the fills on 14 November 2026, and new markets move to it from 23 November 2026 (official rollout page). A
monitor that lists only the first two goes blind without any error: `unknown_emitters` exists to notice the next one."""
ORDER_FILLED = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee"
EXCHANGES = {
    "0xe111180000d2663c0091e4f400237545b87b996b": "CTF Exchange",
    "0xe2222d279d744050d28e00520010520000310f59": "Neg Risk CTF Exchange",
    "0xe3333700ca9d93003f00f0f71f8515005f6c00aa": "ExchangeV3 (Polymarket Protocol V2)",
}
EXCHANGE_V3 = "0xe3333700ca9d93003f00f0f71f8515005f6c00aa"
COMBINATORIAL_MODULE = 3        # top byte of a Protocol V2 position id: 1 binary, 2 negative risk, 3 combinatorial


def is_combo(exchange, token_id):
    """A position of the CombinatorialModule: several outcomes in one token, not a side of one market. On 14 November 2026
    every fill of ExchangeV3 was one (210 of 210 in 15 minutes), and the catalogue does not list them as markets."""
    return exchange == EXCHANGE_V3 and (int(token_id) >> 248) == COMBINATORIAL_MODULE


MIN_ENTRY_USD = 1000.0          # an entry is a first BUY fill of this size or more on one side of one market
PRICE_MAX = 0.90                # above: the outcome is treated as publicly settled
EXCLUDED_TAGS = {"games", "esports", "crypto-prices", "hit-price", "up-or-down", "multi-strikes", "weather", "tweets-markets",
                 "mention-markets"}          # outcomes produced in public view: never an entry
PUBLIC_PROCESS_TAGS = {"sports", "soccer", "nfl", "nba", "basketball", "golf", "tennis", "formula1", "f1", "football", "hockey",
                       "olympics", "fifa-world-cup", "2026-fifa-world-cup", "world-cup", "pga", "pga-tour", "baseball", "mlb", "nhl",
                       "ufc", "boxing", "cricket", "chess", "equities", "stocks", "commodities", "pre-market", "monthly-hit",
                       "youtube", "mrbeast", "box-office"}   # kept apart: nobody can hold these outcomes in advance


def family(tags):
    """EXCLUDED, PUBLIC_PROCESS or INFO, from the tags of the event. Same lists as the frozen study."""
    t = set(tags or [])
    return "EXCLUDED" if t & EXCLUDED_TAGS else ("PUBLIC_PROCESS" if t & PUBLIC_PROCESS_TAGS else "INFO")


def unknown_emitters(logs):
    """Addresses that emit OrderFilled and are not in EXCHANGES: {address: number of logs}."""
    out = {}
    for log in logs:
        a = log.get("address", "").lower()
        if (log.get("topics") or [None])[0] == ORDER_FILLED and a not in EXCHANGES:
            out[a] = out.get(a, 0) + 1
    return out
