# Public reports of suspected informed trading on Polymarket

Read on 2026-11-02. **A public accusation is a lead, never ground truth.** Figures below are what each page says, not what this investigation verified. Usernames were resolved to addresses from the rows of Polymarket's own API (`results/discovery/`), and a username can change or be reused.

| Market or topic | Date of the report | Author | What it says | Status of the claim | URL |
|---|---|---|---|---|---|
| Maduro and Venezuela markets | 2026-04-23 | US Attorney SDNY, indictment 26 Cr. 156 | 13 purchases of about $33,934, profit of about $409,881, about 437,859 USDC.e sent to a foreign vault | **Accusation before a court, no verdict known** | https://www.justice.gov/usao-sdny/media/1437781/dl |
| Same | 2026-04-23 | US DOJ press release | Charges announced. The page was saved, sha256 in `results/control_federal_case/` | Accusation | https://www.justice.gov/opa/pr/us-soldier-charged-using-classified-information-profit-prediction-market-bets |
| Same | 2026-04-24 | DL News | Username Burdensome-Mix, CFTC civil complaint, more than $404,000 | Press report of charges | https://www.dlnews.com/articles/regulation/doj-charges-soldier-with-polymarket-betting-on-classified-information-of-maduro-capture/ |
| Same | 2026-01-07 | Four Pillars | Names address `0x31a56e9E690c621eD21De08Cb559e9524Cdb8eD9`, net +$404,221, three months before the charges | Analysis, no charge at that date | https://research.4pillars.io/en/research/unmasking-the-maduro-insider-on-polymarket |
| US strikes Iran by February 28, 2026 | 2026-02-28 | The Block, citing Bubblemaps and Lookonchain | Six wallets, $989,191 net from profile figures: Planktonbets, Dicedicedice, Neodbs, nothingeverhappens911, Anon, and `0x1caA6a7ad0c6916aeF7b67946De2e57Ad24846a0` as largest | "Suspected insiders", no charge | https://www.theblock.co/post/391650/fresh-accounts-netted-1-million-on-polymarket-hours-before-us-airstrikes-on-iran-bubblemaps |
| Iran strike, Khamenei, ceasefire | 2026-05-19 | Cointelegraph, citing Bubblemaps | Nine accounts, $2.4M, 98% win rate, funded through exchanges. Bubblemaps itself says it has no definitive proof. No address on the page | Allegation | https://cointelegraph.com/news/bubblemaps-polymarket-cluster-win-military-bets |
| Same | 2026-05-19 | CryptoDiffer | Same cluster, more than 80 bets | Second-hand | https://cryptodiffer.com/project-updates/bubblemaps-uncovers-suspected-insider-trading-ring-on-polymarket |
| US x Iran ceasefire by April 7 | 2026-04-09 | Euronews, with AP, Dune data | New accounts, one about $72,000 at $0.088, another joined the day before, won over $125,500. No address on the page | Press, congressional concern, no charge | https://www.euronews.com/2026/04/09/newly-made-polymarket-accounts-won-massively-on-us-iran-ceasefire-bets |
| Nobel Peace Prize 2025, Machado | 2025-10-10 | The Block | At least three accounts, about $90,000. Trader 6741 about $53,500. Inquiry by the Nobel Institute reported | Official inquiry reported, no finding known | https://www.theblock.co/post/374199/officials-probe-polymarket-over-suspicious-trades-predicting-nobel-peace-prize-winner-reports |
| Same | 2025-10-11 | Covers | Three accounts | Press | https://covers.com/industry/probe-into-polymarket-nobel-peace-prize-bets-oct-11-2025 |
| Same | 2025-10 | Decrypt | Nobel organizers looking into it | Press | https://decrypt.co/343840/nobel-peace-prize-organizers-intestigating-polymarket-insider-trades |
| ZachXBT Axiom investigation | 2026-02-27 | Cointelegraph, Dune data | Eight wallets about $1.2M, more than 50 losing wallets about $1.23M. "Likely insider addresses" from one researcher. No address on the page | Allegation. The market was not found in the public search under the names tried, so it is not in the catalogue | https://cointelegraph.com/news/suspected-insider-1-2m-zachxbt-axiom-expose |
| Biden pardons | not read | Bubblemaps, headline only | $300,000 profit | The page failed to load twice: headline only, not verified | https://www.pulse.bot/big-data/news/analytics-firm-bubblemaps-uncovers-300000-polymarket-profit-from-biden-pardons-via-blockchain-data-9b2dea87-5626-406f-878e-5ab18ac7f290/ |
| US military markets | 2026-08 | Reported research on 152 wallets, $8M | Title only: the PDF body could not be read as text. **Not verified** | Unknown | https://skbi.smu.edu.sg/sites/skbi.smu.edu.sg/files/%5Bcurrent-domain%3Amachine_name%5D/news_room/20260821_Inkl_Polymarket%20faces%20fresh%20insider%20trading%20scrutiny%20after%20152%20wallets%20allegedly%20made%20%248%20million%20betting%20on%20US%20military%20markets_%20report.pdf |
| Population level | 2026-05-01 | arXiv 2605.00459, M. Nechepurenko | 12,708 markets from 2020 to 2026, 88 with computable leakage scores | Research, names no one | https://arxiv.org/abs/2605.00459 |
| Population level | 2026 | Mitts and Ofir, reported by AOL and others | 210,000 flagged trades, $143M "anomalous" profit. Coverage reports a statistician questioning the ranking, which leans on profitability | Research. Selected on profit, so it cannot show skill before the outcome | https://www.aol.com/articles/informed-traders-polymarket-netted-143-082601427.html |

## What the catalogue does not hold

- Israel: press mentions arrests and two charges in February 2026 over classified information and bets. No primary document was read, and no market identified.
- Google Year in Search: searched, no report found under the names tried.
- A report absent from this table is unknown here. It does not mean nothing happened.
- Press usernames that the tapes did not resolve in the window read: GHPT (Nobel), nothingeverhappens911 and Anon (Iran). A name can differ between display and pseudonym, or the entry can fall outside the window. Not concluded.

## Markets in the catalogue

`markets.json` holds the six market ids, windows and public event times, and says where each event time comes from. Two event times are approximate and marked so: Khamenei and the Biden pardons. Catalogue markets are selected on suspicion and on outcome. They can illustrate a method, and they cannot validate one.
