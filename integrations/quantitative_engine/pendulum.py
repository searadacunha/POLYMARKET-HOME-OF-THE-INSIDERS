"""Read a targeted Pendulum hour into the engine's event records.

DuckDB is imported only when this function runs. Unit tests do not need it.
The preview hours used here are CC BY-NC 4.0. Credit pendulumflow.
"""

from __future__ import annotations

from decimal import Decimal


def _scaled(text, places: int):
    if text is None:
        return None
    value = Decimal(text)
    return int(value * (10 ** places))


def _levels(raw, price_places=4, size_places=6):
    levels = []
    for level in raw or ():
        price = level["price"] if isinstance(level, dict) else level[0]
        size = level["size"] if isinstance(level, dict) else level[1]
        levels.append((_scaled(str(price), price_places), _scaled(str(size), size_places)))
    return levels


def load_events(path: str, hour: str, split: str, category: str) -> list[dict]:
    import duckdb

    connection = duckdb.connect()
    rows = connection.execute(
        """
        SELECT event_type, epoch_ms(timestamp), row_ordinal,
               hex(market), hex(asset_id),
               cast(best_bid AS VARCHAR), cast(best_ask AS VARCHAR),
               bids, asks,
               cast(price AS VARCHAR), cast(size AS VARCHAR), side,
               hex(transaction_hash), source_witness
        FROM read_parquet(?)
        WHERE event_type IN ('book', 'best_bid_ask', 'last_trade_price')
        """,
        [path],
    ).fetchall()
    events = []
    for row in rows:
        kind = {"book": "BOOK", "best_bid_ask": "QUOTE", "last_trade_price": "PRINT"}[row[0]]
        events.append({
            "kind": kind,
            "ts": int(row[1]),
            "ordinal": int(row[2]),
            "market": row[3],
            "asset": row[4],
            "best_bid": _scaled(row[5], 4),
            "best_ask": _scaled(row[6], 4),
            "bids": _levels(row[7]),
            "asks": _levels(row[8]),
            "price": _scaled(row[9], 4),
            "size": _scaled(row[10], 6),
            "side": row[11],
            "tx": row[12],
            "witness": row[13],
            "hour": hour,
            "split": split,
            "category": category,
        })
    return events
