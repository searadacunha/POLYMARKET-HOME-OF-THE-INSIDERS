# Provenance of `pusd_first_transfer.jsonl`

- **What it is.** One JSON line per wallet of the phase 8 funding sample (1,506 lines, the wallets of
  `investigations/maduro-iran/sources/phase8/wallet_features.csv`). Each line holds the earliest pUSD transfer
  touching the wallet, in either direction: `pusd_first_ts` (Unix seconds), `from`, `to`, `value` (raw, 6 decimals)
  and `tx`. `pusd_first_ts` is `null` when the lookup returned no pUSD transfer. No line records a lookup error.
- **Token.** pUSD on Polygon, `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb`.
- **How it was collected.** On 19 November 2026, one Etherscan V2 `account/tokentx` call per wallet (chain 137,
  `contractaddress` = pUSD, `sort=asc`, `offset=1`), the same endpoint family as `p8_funding.py`. A failed call was
  written as an error and retried, never as "no transfer". Only the parsed fields above were kept; the raw API
  responses were not archived.
- **Copied unchanged** from the session's restore folder. SHA-256 in [`SHA256SUMS`](SHA256SUMS)
  (`1ae6443e...e616`), the same hash recorded by the audit.
- **Not verified here.** The file is network-derived and was not re-fetched: this note runs without network. A
  40-wallet positive control of the same Etherscan lookup against the published `first_any` was scripted during the
  audit session; its output is not among the files this note publishes, so its outcome is not claimed here.
- **What it does not show.** A first pUSD transfer from the zero address is a mint. It is not shown to be outside
  funding, and nothing in this file says who controls a wallet.
