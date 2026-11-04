# Resolved Relay exit from the owner key of Polymarket account 0xa8e6

Date: 4 November 2026. Targeted follow-up to the existing Ballon d'Or flow investigation.

## Result

The previously unresolved Ethereum payment of **2,969.568353 mUSD** was bridged through Relay to **Monad (chain 143)**. In the destination transaction, the same raw amount is routed into the vmUSD vault and **2,904.308540 vmUSD shares** are minted to:

`0xea1a3f324c5ee313bb04d9e642c39c8b29e7454b`

This resolves a specific exit recorded in the older report. It supplies a concrete destination address for further tracing. It does not establish that this beneficiary and the source key have the same operator, or that the payment consists entirely of Polymarket winnings.

## Connection to the existing case

The archived [wallet evidence](../../investigations/ballon-dor-wallets/sources/evidence/contre_verification_20261102/wallet_0xa8e6.json) identifies `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d` as the owner key of Polymarket account `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5`. The existing [flow follow-ups](../../investigations/ballon-dor-flow-trace/sources/state/followups.json) and reports left the subsequent mUSD route unresolved. These older files are preserved unchanged.

## Transaction-level evidence

| Step | UTC, 29 October 2026 | Evidence |
|---|---|---|
| Ethereum debit | 16:35:35 | 2,969.568353 mUSD from `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d` to Relay Depository `0x4cd00e387622c35bddb9b4c962c136462338bc31` |
| Monad execution | 16:36:04 | 2,969.568353 mUSD routed through `0x0729e2a4716d9f7dd17858d5d504426d228697f7`, then `0xea1a3f324c5ee313bb04d9e642c39c8b29e7454b`, into vault `0x1c8a336051d2024e318a229d01f9f6cf96efd316` |
| Vault shares | Same Monad transaction | Mint of 2,904.308540 vmUSD to `0xea1a3f324c5ee313bb04d9e642c39c8b29e7454b`; Transfer log 0x91 and Enter log 0x92 |

- Ethereum transaction: [`0xd5e6ec811be960624614224adf9e353d56403eabec8f93ba2b89c10a9119407b`](https://etherscan.io/tx/0xd5e6ec811be960624614224adf9e353d56403eabec8f93ba2b89c10a9119407b), block **26,299,631**.
- Monad transaction: [`0xda3f8b4c662299b4d3ec6a6a7fda1e4d99e33e2e608ad4f2a7d0155574d6bfe2`](https://monadscan.com/tx/0xda3f8b4c662299b4d3ec6a6a7fda1e4d99e33e2e608ad4f2a7d0155574d6bfe2), block **117,661,422**.
- Relay request: `0x17932917340327ffe83c69f04e56e8cc28e6cd326e706b09ee2c57bae405df95`, status `success`.
- Relay order: `0xca6ecf2d1ba60c83ca6b9bfad7677802ff00c67e9eb854804ef9771b00b8a945`.

Relay explicitly associates the two transaction hashes within one request; this link is not inferred from timing or amount alone. The two transactions are **29 seconds apart**. Both receipts succeed, and their token-transfer logs agree with the amounts in the Relay response.

## Distinguish the addresses

The root Relay field `recipient` repeats `0x48ec...`. Its metadata names `0x0729...`, the router. Neither field alone identifies the final owner of the received asset. The destination receipt shows the actual **vmUSD beneficiary is `0xea1a...`**.

The vmUSD contract has six decimals and returns symbol `vmUSD` through `eth_call`. [Immersve's primary integration documentation](https://docs.immersve.com/guides/vmusd/) lists this exact Monad contract as MetaMask's vault-share token. A vmUSD share is not one mUSD; the difference between token counts is not a measured loss or fee.

At the time of the follow-up, `eth_getCode` on Monad returns an EIP-7702 delegation designator for `0xea1a...`. This does not identify its human controller. Shared delegation software or the same service must not be used as ownership evidence.

## Collection and reproducibility

The raw JSON responses and matching `.meta.json` files are included in this directory. Metadata records the exact endpoint/request, retrieval time and SHA-256. No API key or private account was used.

- `relay_request.json`: public Relay lookup by the exact origin transaction hash.
- `ethereum_tenderly.json`: successful Ethereum receipt from a public RPC.
- `ethereum_blockscout.json`: independently confirms the Ethereum transaction, timestamp and token transfer.
- `monad_receipt.json`: public Monad RPC receipt, chain ID, token decimals/symbol and code queries.
- `ethereum_receipt.json`: the first Ethereum provider returned a null receipt. This discordant observation is retained; it was not treated as proof that the transaction did not exist. The successful alternate receipt and Blockscout record are the positive evidence.

Run the read-only check from this directory:

```bash
python3 verify.py
```

It checks capture hashes, successful receipts, chain IDs, transaction/block agreement, the exact mUSD transfer route, the vmUSD mint and the vault Enter event. It makes no network request and does not rewrite evidence.

## Boundaries and next question

This is a newly resolved path relative to the archived report, not a finding of insider trading. No new ownership inference, link to another named bettor, comprehensive destination history or current token balance is established here. The next bounded question is whether the beneficiary's independently verified incoming/outgoing transfers intersect other case addresses, after excluding shared services and standard contract implementations.
