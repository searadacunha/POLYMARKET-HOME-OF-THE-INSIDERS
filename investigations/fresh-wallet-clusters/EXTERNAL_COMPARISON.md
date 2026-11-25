# External comparison

Read on 25 November 2026. Repository metadata came from the public GitHub API. Method descriptions are taken from READMEs and from this repository's earlier benchmark (`research_notes/competitor-benchmark-2026-11-20/REPORT.md`). No external code was copied and none was executed. Where a repository states no licence, it was treated as all rights reserved.

| Repository | Licence seen | What it adds relative to this run |
|---|---|---|
| [veeradittya/polymarket-insider-detection](https://github.com/veeradittya/polymarket-insider-detection) | none stated | Dates first public mention from GDELT, with an outlet list. That is ahead of this run, which records no announcement clock. It was not adopted: this run has no news archive, and the confirmatory question is financial linkage rather than lead time against a headline. |
| [vsbtc/polymarket-insider-detection](https://github.com/vsbtc/polymarket-insider-detection) | MIT | One hop to a first funder, plus a wallet ranking. The first-funder idea is the depth-1 case of the trace used here. The ranking conditions on results across wallets; it is not a test of a pre-registered cluster. |
| [orcalayer/polymarket-insider-score-backtest](https://github.com/orcalayer/polymarket-insider-score-backtest) | CC-BY-4.0 for data, charts and text; the README does not put the same licence on the script | A large out-of-time score backtest on a private database. The public artefact is aggregate. The chronological split in this study follows the same discipline. Their same-day control is a design this repository's earlier benchmark already judged ahead of ours on that one point; H2 is this run's matched-market control. |
| [pselamy/polymarket-insider-tracker](https://github.com/pselamy/polymarket-insider-tracker) | MIT | Live alerts. Funding can walk three hops inside a short block window and is not part of the score. This run uses the hop for the test, not for a live score. |
| [Geriogerg/PolyTracker](https://github.com/Geriogerg/PolyTracker) | none stated | Clusters wallets by shared funders, transfers between them, shared cash-out addresses and synchronised bets, then scores the record against chance. That is the same family of question as H1 and H3. The README's demo plants synthetic rings; this run's offline tests plant a shared funder and require the shuffle to call it rare. Their code was not reused. |
| [suislanchez/polymarket-insider-detector](https://github.com/suislanchez/polymarket-insider-detector) | none stated | Binomial tests of win rate, and trades in the last minutes before resolution. A high win rate is computed after the outcome. This study does not use it as a test, because selecting or scoring on the resolution answers a different question and favours wallets that won. |
| [Benja-Pauls/polymarket-insider-detection](https://github.com/Benja-Pauls/polymarket-insider-detection) | none stated | Builds labels from allegations. Useful as a list of leads, not as a denominator. |
| [0xinsider/research](https://github.com/0xinsider/research) | CC-BY-4.0 | Commits the SQL and the bootstrap output. On sports and esports, the top grade's edge over price in the published 23 October 2026 run is about two points. That population is this study's control family, not its information family. The habit of shipping the query output with the claim is the reason `data/stats.json` sits next to the findings. |

## Inca Digital

Inca Digital's public briefing "Insider Trading on Prediction Markets: A Polymarket Analysis" (https://inca.digital/intelligence/polymarket-insider-report/) describes a screen of 488 wallets with at most ten markets and at least $30,000 of profit, and a shortlist of 39. A later briefing, "Polymarket Mole Hunt" (https://nothingescapesinca.com/p/polymarket-mole-hunt), discusses five wallets on an Israel/Iran contract. Both start from wallets that won. This study does not start from profit, so it cannot confirm or deny that shortlist. The screen is a lead generator. It is not a rate of fresh cofunded groups among markets that were not chosen for their outcome.

## Bubblemaps

Press accounts of Bubblemaps' 2026 notes (The Block, 28 February 2026; Cointelegraph, 19 May 2026; Decrypt) describe fresh Polymarket wallets that bought military contracts shortly before public news, often funded through exchanges. Bubblemaps' own quoted caveat is that the pattern does not prove who controlled the wallets or that they held non-public information. Exchange funding is, under this study's rules, a shared service and stops the trace. Those notes are case leads. They are not reused here as labels.

## DOJ and CFTC

The CFTC's 3 January 2022 order against Blockratize, Inc. d/b/a Polymarket (Docket No. 22-09) is a registration case about offering event contracts without a registered facility. It is not a finding about wallet clusters.

On 23 April 2026 the U.S. Attorney's Office for the Southern District of New York unsealed charges, and the CFTC filed a parallel complaint, alleging that one soldier used non-public military information to trade Polymarket contracts tied to Venezuela and Nicolás Maduro. Secondary accounts of the charging documents describe a single trader and a profit on the order of $400,000. An allegation in a charging document is not a finding of this study, and it is not evidence about any other wallet. This run does not re-identify that trader and does not treat the indictment as a positive control.

## What was adopted

The matched-market comparison (H2), the month-wise label shuffle (H1, H3), the refusal to score a service as a person, and the refusal to treat a win rate as proof. No external source code was vendored.
