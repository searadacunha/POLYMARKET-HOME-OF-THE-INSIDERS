# Funding links: how a payer has to be read, and what the study found

"Linked" on this page means one thing: a transfer of USDC, USDC.e or pUSD read on Polygon, from a key to a wallet.
It does not say who controls the key or the wallet, and an address is not a person.

## How the payer of a deposit has to be read

Three readings that look natural are wrong often enough to change a count.

1. **The payer in the deposit's receipt is often a contract.** When a wallet's deposit is its own money swapped into
   the collateral token, the receipt shows a pool, a settler or a ramp as the payer. On the documented Nobel 2025
   account `0xa430506774f9efaf39903ee7e0db1351f66891ca` the receipt names a Uniswap pool; the key that sent the money,
   `0xe206961002feebd9edb152eed9b630a351874043`, is in a transaction 39 blocks earlier. The study therefore reads the
   collateral the wallet received in the 10,000 blocks (about four hours) before every deposit paid by a contract
   (`study/code/col_40_funding.py`, phase E).
2. **The activity listing does not show every deposit.** Its DEPOSIT rows cover some ways of funding a wallet only.
   The share of wallets whose first trade has no deposit row before it was 1.6 % or less until October 2025 and 26 % in
   August 2026 (pre-freeze audit, `study/audit/sfh_collecteurs_20261114.txt`). The study reads the collateral received
   on the chain instead (`study/code/col_41_inflows.py`), and leaves out what is not funding: Polymarket's own
   transfers (exchanges, conditional tokens, adapters, ramps, Wrapped Collateral, addresses tagged as Polymarket),
   transfers in the same second as a trade, a redemption, a reward or a withdrawal of the wallet, pUSD minted from the
   wallet's own money, and amounts under 1 USD. A first version that counted every other sender as funding was found by
   the second pre-freeze audit to count redemptions and rewards as fresh money (`study/audit/sfh2_code_corrige_20261114.txt`).
3. **A service never links two wallets.** A contract, an address with a public name tag, a key with 1,000 transactions
   or more, or a key that had paid more than ten wallets of the dataset at the time is a service: bridges, exchanges and
   relayers pay thousands of unrelated people. Only a plain key can be a link, and a pass-through key (five
   transactions or fewer) is read one hop further, over the window of each payment it made.

## What the study found

The payer was traced for 20,070 entries (thin or dormant wallets with fresh money). 2,099 of
them have a plain key behind a deposit, 1,839 distinct keys. **2 keys** are behind two
wallets or more. Every transfer below was read again from its own transaction receipt by
`scripts/recheck_links.py` (12 confirmed, 0 not served, 0 not confirmed, read on 2026-11-14 17:22:18 UTC,
`data/links_recheck.json`).

**Key `0xe206961002feebd9edb152eed9b630a351874043`**: 8 wallets in this dataset, 230,000.00 USD sent to them in the transfers below.

| Wallet | Funding transaction | Block | USD | First large purchase (UTC) | Event | Side, price | Re-read from the receipt |
|---|---|---:|---:|---|---|---|---|
| `0xa430506774f9efaf39903ee7e0db1351f66891ca` | `0xe4dd2102d6dd649611557415aa28457e792c5abaac963e5a6fbb7a3b6f3e2516` | 77472527 | 40,000.00 | 2025-10-09 22:45:07 | nobel-peace-prize-winner-2025 | No at 0.67 | confirmed |
| `0xa430506774f9efaf39903ee7e0db1351f66891ca` | `0xe4dd2102d6dd649611557415aa28457e792c5abaac963e5a6fbb7a3b6f3e2516` | 77472527 | 40,000.00 | 2025-10-09 22:46:49 | nobel-peace-prize-winner-2025 | Yes at 0.1 | confirmed |
| `0x1973177faa69b94b4afab818e612a7c05b3c01a9` | `0xfd981aca74f1b9ae6e9cdb9a726c82d7d3d3a65876ca34b8ae4290562209b838` | 77476224 | 30,000.00 | 2025-10-10 00:55:11 | nobel-peace-prize-winner-2025 | Yes at 0.4936 | confirmed |
| `0x03f8aae7ae1687ef7e2d55e4429e72e9a95d8541` | `0x8ccc80d84f4cb1002fd9af6a96da6403fbc718602ee8703e78ddd379068efe36` | 77476845 | 30,000.00 | 2025-10-10 01:07:25 | nobel-peace-prize-winner-2025 | Yes at 0.4946 | confirmed |
| `0xa9c57a20cb8433a269976bb35eb872bd11380bd9` | `0xc463fe747ae655f8af92bedfcc1d00c3beb2e44ec68c0b14dbe4af4a9171c962` | 77477036 | 25,000.00 | 2025-10-10 01:12:41 | nobel-peace-prize-winner-2025 | Yes at 0.5659 | confirmed |
| `0x4bac00c61a02275d681f3857cdc5ae315f1f7075` | `0xf3366b67b279de1cfea9927defe085b6a8a2706e164361a2c2af529163b12251` | 77477691 | 30,000.00 | 2025-10-10 01:33:49 | nobel-peace-prize-winner-2025 | Yes at 0.6523 | confirmed |
| `0x4bac00c61a02275d681f3857cdc5ae315f1f7075` | `0xf3366b67b279de1cfea9927defe085b6a8a2706e164361a2c2af529163b12251` | 77477691 | 30,000.00 | 2025-10-10 01:55:53 | nobel-peace-prize-winner-2025 | No at 0.8 | confirmed |
| `0x8507124d416dd181ea552e01a0dfed19ab0b1086` | `0x36a7fc28b0ade3f6a56b48e716ddaf6a574ff671836919e1df6452875760b1d6` | 77478106 | 30,000.00 | 2025-10-10 02:00:21 | nobel-peace-prize-winner-2025 | Yes at 0.6949 | confirmed |
| `0x2612496ab8f1d774f116f28b50769971936c92de` | `0x78b680338af0a0a3a1f30ee7df88bf863dd4f1fa49505a4a83dbf95d021baff1` | 77480675 | 25,000.00 | 2025-10-10 03:23:29 | nobel-peace-prize-winner-2025 | Yes at 0.6547 | confirmed |
| `0x234cc49e43dff8b3207bbd3a8a2579f339cb9867` | `0x1b6836d22eb515b8eba1f8a5cb9c7c0909ded9519d4b47f63a63d1a6dce12d9e` | 77481110 | 20,000.00 | 2025-10-10 03:29:19 | nobel-peace-prize-winner-2025 | Yes at 0.6771 | confirmed |

**Key `0x6ae40b5bada52b0c4f6efc1653848e136b600392`**: 2 wallets in this dataset, 150,087.71 USD sent to them in the transfers below.

| Wallet | Funding transaction | Block | USD | First large purchase (UTC) | Event | Side, price | Re-read from the receipt |
|---|---|---:|---:|---|---|---|---|
| `0x1489046ca0f9980fc2d9a950d103d3bec02c1307` | `0x61e1f7880d00eac2ebec7863754eff2a2a6c96f33eb07184e347c4cef5152f1a` | 76938292 | 150,000.00 | 2025-09-26 20:48:51 | israel-withdraws-from-gaza-in-2025 | No at 0.8642 | confirmed |
| `0x796590ec48bca1d8fd773bf52a66bf82e21409d9` | `0x6f74d6cc9e5661689be351bece707bf279680bcc12e4c6149961bb27f1bead8d` | 77637548 | 87.71 | 2025-10-13 18:39:01 | new-york-city-mayoral-election | Yes at 0.8916 | confirmed |

The first key is the documented Nobel 2025 case: one key paying eight new accounts whose first large purchases fall
between 22:45 UTC on 9 October 2025 and 03:29 UTC on 10 October, all but one of them on the Yes side of the same
market. The group class `C4` fires on it 11.3 hours
before the market closed, when the second account enters ([RESULTS.md](RESULTS.md)). It was in this repository before
the study and was used to check the reader, so it says nothing about how often such a group exists or wins.

The second key paid 150,000 USD to one wallet in the 24 hours before its first large purchase, on 26 September 2025,
and 87.71 USD to another before its purchase on 13 October 2025, on two unrelated events. `C5` fires on the second wallet. The amount is small and nothing else connects the two wallets.

**On the validation events (April to October 2026), no key paid two wallets of this dataset.** The structure of the
Nobel case, one plain key funding several new accounts that buy the same event, was not met again in the population
the study could read.

## What this reading does not see

- A link two hops away or more. The second network of the Nobel 2025 case, two accounts that share a key further up
  (`investigations/followup-20261113/`), is not seen as a group: their deposits go back to two different keys.
- Money that reached a wallet more than about four hours before a deposit paid by a contract, or by a route that is not
  a transfer of the collateral tokens.
- A key that became busy or tagged after the purchase: descriptions are read today, which can only remove links.
- Wallets outside the screen of the study (more than two other markets, or a busy history) are not traced.
