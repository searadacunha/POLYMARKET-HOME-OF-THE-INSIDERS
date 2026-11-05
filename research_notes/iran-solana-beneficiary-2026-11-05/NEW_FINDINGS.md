# New findings, 5 November 2026: Iran cluster E beneficiary

Full detail, limits and rejected leads are in [REPORT.md](REPORT.md). Each figure is recomputed offline by `verify.py` from `evidence/`.

## 1. Two more Polymarket accounts paid the common Solana beneficiary

- **Established:**
  - oveiStheair (`0x97e490d61b530d5078348d76143a25c43a47164d`) and aaamsaasa (`0x0a142164f48dab6448872f0abac310d03e305316`) sent 32,210.572027 and 27,150.675873 USDC.e through five Relay orders on 28 February 2026 to `4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy`.
  - That is the same beneficiary as BlueElephant666 and SemiconductorIT, and their share is 84.7 % of the 70,065.262869 USDC.e it received.
- **Decisive evidence:** for each of the 11 orders, three records agree:
  - the Relay request names the account as `user` and the beneficiary as `recipient`;
  - the Polygon receipt shows the proxy wallet's USDC.e Transfer to the Relay Depository for the exact amount;
  - the Solana credit carries the Relay order identifier as its memo.
- **Consequence:**
  - The beneficiary links four Polymarket accounts, not two.
  - Both new accounts bet "US strikes Iran by February 28" Yes before the 05:28 window used by phase 2, which is why that phase missed them.
  - Both were funded days in advance: from BSC through Relay, and from Crypto.com.

## 2. The beneficiary's money went to one Bybit customer deposit address

- **Established:**
  - 842.687802663 SOL, 98.35 % of the beneficiary's 856.840698827 SOL, went in 11 transfers to `Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV`. Only 12.4478221 SOL went to Privacy Cash and 1.7 SOL to an unlabeled wallet.
  - After SemiconductorIT's last credit at 16:20:47, there is a single outflow: 69.068480977 SOL to that address at 16:21:06.
  - The address is labelled Bybit Deposit (Agnhk). Bybit's gas distributor tops it up, and its SOL is swept to Bybit Hot Wallet 10 (842.691342663 SOL on 28 February).
- **Decisive evidence:**
  - the complete 66-transaction history, with a continuous balance from 0 to 0;
  - service behaviour verified independently of the label: one gas wallet funds 17 addresses in a single slot, and the hot wallet has 242 senders in two hours.
- **Consequence:**
  - The trace ends at a custodial frontier that can be resolved: Bybit knows the customer of this deposit address.
  - The address has been in use since July 2025, with withdrawals from Binance, Kraken and an exchange labelled Crypto.com, so it is a durable customer account, not a single-use cash-out.

## 3. A Privacy Cash withdrawal credited that same Bybit deposit address

- **Established:**
  - At 14:55:19, 29 seconds after the beneficiary's 12.3288002 SOL deposit, Privacy Cash paid 0.9905 SOL out of 1 SOL withdrawn (decoded `ext_amount` −990,500,000) to the Bybit deposit address.
  - There was no other Privacy Cash interaction by either address, and no deposit after SemiconductorIT's credits.
- **Decisive evidence:** the decoded instruction, the pool's −1,000,000,000 lamport change and the recipient's +990,500,000 in signature `2kkJqk86KfZ1bmMqxEAMpndtSTAFyBQRp4dNy5vQryHWiKtdXJWoMp8biX2VXmyrtWzHTUQDpSbJouiMWp6y9pdh`.
- **Consequence:**
  - The pool's proof prevents matching this withdrawal to the beneficiary's deposits.
  - The withdrawer nonetheless chose the beneficiary's own exit account: this is a supported financial relation, not a demonstrated round trip.

## 4. Role of the recurring addresses and of the other exits

- `0x519fa16e9897132b7633f634b76306a327839e06` is an unlabeled transit wallet that forwards each inflow to Binance hot wallets.
- `0xa6c221448af73af8350291c5cdcd877b39683766` forwards to `0x852dc1c875f0117ea0808610010893e4c576b6a9`, an unlabeled, very active EOA. That EOA also paid `0x519fa16e…` once in June 2025.
- aaamsaasa's remaining 8,995.497557 USDC went to a Crypto.com customer deposit address, `CCQQKc4vw527ehZZhQidZZT9LEzKr4Ca7bZNwJv6BmBR`.
- The Polygon receipt missing from the earlier audit (`0xc0a30b3c70070cf81c6a48bbf5e0206413523b3113fb41cf557dd81978cd3a6b`) is now archived: 1,000 USDC.e from BlueElephant666, status 1.

## What this does not establish

- **Common control.** The four accounts were processed one after another on 28 February and forwarded by one key to one exchange account. That is a hypothesis of coordination and common control, not a demonstration.
- **Inside information.** It is not demonstrated. Among 115 wallets that bought at least 1,000 USDC of Yes between 00:00 and 06:15 UTC, the accounts rank 77th to 103rd by first buy; this exploratory comparator shows the bet timing is not distinctive. The distinctive fact is the shared exit.
