# Fixtures

Real responses captured on 2026-11-07 from `data-api.polymarket.com/v2/trades` (`filter_type=CASH&filter_amount=5000`),
`/v2/activity` and `eth_getTransactionReceipt` on Polygon (drpc.org), so the parsers are tested on production shapes.

Field names, types, contract addresses, event signatures, amounts, timestamps and condition ids are unchanged.
Wallet addresses and transaction/block hashes were replaced by deterministic SHA-256 derived values, and the
`name`, `pseudonym`, `bio` and profile image fields were emptied: these files describe API shapes, not people.
`expected.json` gives the replaced proxy, funder and withdrawal destination used by the receipt tests.
