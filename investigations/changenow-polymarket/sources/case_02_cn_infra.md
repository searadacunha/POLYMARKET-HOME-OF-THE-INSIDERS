# TASK: enumerate published ChangeNOW (CN) on-chain infrastructure on POLYGON, with citations

Use your web search tool. I need up-to-date, PUBLICLY-DOCUMENTED ChangeNOW infrastructure
addresses on Polygon (chainid 137), for forensic attribution of CN-funded wallets. STRICT
RULES:
- NO invented addresses. Every address you output MUST be backed by a cited source
  (chain-analysis report, Arkham/Nansen/Etherscan public label, ChangeNOW docs, GitHub,
  forum, block explorer "Name Tag"). If you cannot cite it, do NOT output it — instead list
  it as "unknown / not publicly documented".
- For each address give: the address, what it is (hot-wallet / payout hub / deposit
  aggregator / gas funder / router), the chain, and the SOURCE URL.
- Distinguish CONFIRMED-labeled vs INFERRED-by-source.

Specifically search for:
1. ChangeNOW hot wallets / payout addresses on Polygon (USDC.e / USDC / USDT payouts).
2. ChangeNOW deposit aggregator or router contracts.
3. Any address publicly tagged "ChangeNOW" on Polygonscan / Arkham / Etherscan name tags.
4. Known ChangeNOW gas-funding ("gaser") wallets that fund native MATIC to payout fleets.
5. Cross-reference: a CN EVM payout hub I have already verified on-chain is
   0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423 (born ~2026-04-14, pays USDC.e to many
   wallets). Search whether THIS address is publicly labeled/associated with ChangeNOW or any
   exchange/bridge, and what its upstream funder 0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a
   is labeled as. Report findings with sources (or "no public label found").

OUTPUT: a markdown table {address, role, chain, confirmed_or_inferred, source_url} plus a
short notes section on coverage/uncertainty. Concise. If the public record is thin (likely),
SAY SO explicitly rather than padding with guesses.
