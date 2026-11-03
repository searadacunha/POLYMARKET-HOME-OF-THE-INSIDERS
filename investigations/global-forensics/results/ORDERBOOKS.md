# Historical order books

Read on 2026-11-03 by HTTP ranges from the public hourly archive at `r2.pmxt.dev` and `r2v2.pmxt.dev`, without a key. The index page `archive.pmxt.dev` did not answer in three tries, so file names were tested by HEAD. The archive is one third party's capture. Its terms of use were not confirmed, its repository `pmxt-dev/pmxt` is MIT, and that license was not shown to cover the data. A file's server date can be weeks after its hour, so capture in real time is not shown. Vike Data and Pendulum Flow: no repository or page found.

## Coverage measured

| Hour tested | Old host | New host |
|---|---|---|
| 2025-10-10T00 | no | no |
| 2025-12-31T00 | no | no |
| 2026-01-03T05 | no | no |
| 2026-01-20T00 | no | no |
| 2026-02-01T00 | no | no |
| 2026-02-15T00 | no | no |
| 2026-02-20T00 | no | no |
| 2026-02-24T00 | yes | no |
| 2026-02-26T22 | yes | no |
| 2026-02-27T06 | yes | no |
| 2026-02-27T20 | yes | no |
| 2026-02-28T06 | yes | no |
| 2026-03-01T00 | yes | no |
| 2026-04-07T22 | yes | no |
| 2026-05-01T00 | no | yes |
| 2026-06-01T00 | no | yes |
| 2026-04-15T00 | yes | yes |
| 2026-04-25T00 | no | yes |
| 2026-08-01T00 | no | yes |
| 2026-08-31T00 | no | no |
| 2026-09-15T00 | no | no |
| 2026-09-30T00 | no | no |
| 2026-10-13T18 | no | no |
| 2026-10-23T15 | no | no |
| 2026-11-01T00 | no | no |

So the books of Maduro (January 3), Nobel (October 2025) and the Ballon d'Or (October 2026) are **not available here**, at the hours tested. The hours between those tested were not all probed. No current book replaces them: missing stays missing.

## Markets read

| Market | Hours read | Rows | Bytes fetched | Entries in the capture | Entries outside |
|---|---:|---:|---:|---:|---:|
| iran-strike-feb28 | 20, then 17 more | 552,406, then 162,620 | 2,995,246,497, then 1,792,317,937 | 39 | 21 |
| khamenei-out-mar31 | 25, then 10 more | 226,694, then 26,498 | 4,715,370,031, then 1,101,015,516 | 41 | 19 |
| ceasefire-apr7 | 18 | 0 | 3,749,135,189 | 0 | 60 |

The ceasefire market gave 0 rows across 18 hours on 2026-04-07, while the files hold thousands of other markets: not captured in those files, by this reading. So nothing is said about its book.

The second reads, on 2026-11-03, took only the hours of chosen entries from 2026-02-24, when this archive starts, so those hours are not contiguous. An entry counts as inside the capture only with a quote at most 900 s old. The older table below stays as first written; the new rows are in `results/orderbooks/`.

## Three entries of the September file's network

Read from `results/orderbooks/iran-strike-feb28.json`. On February 26, three accounts the September file links by money bought Yes in the Iran strike market:

| Account | UTC | USD | Paid | Bid / ask before | Ask depth within 2 cents | Mid 5 min before | Mid 5 min after |
|---|---|---:|---:|---|---:|---:|---:|
| mrs-joker | 2026-02-26 21:43:24 | 6,000 | 0.092 | 0.08 / 0.10 | $27,168 | 0.085 | 0.095 |
| planktonbets | 2026-02-26 21:44:48 | 6,000 | 0.100 | 0.09 / 0.10 | $28,355 | 0.085 | 0.095 |
| neodbs | 2026-02-26 22:53:50 | 9,883.75 | 0.100 | 0.09 / 0.10 | $21,566 | 0.095 | 0.095 |

They paid the visible ask or less, against resting depth that could take the size, and the mid moved a cent or less over five minutes around them. Depth is one token's side, as noted below. So these entries did not push the price in a visible way. Nothing here says what any of them knew, and this table holds no comparison with other buyers of the same day.

## What the largest entries met

Both tokens, chosen by size and timing only, from `results/discovery/`. The state at entry comes from captures one second or more before the trade. The later mid is description, and it selects nothing. All columns are in `results/orderbooks/`.

| Market | UTC | Outcome | USD | Paid | Bid / ask | Paid minus ask | Mid 5 min before | Mid 5 min after | Hours before event |
|---|---|---|---:|---:|---|---:|---:|---:|---:|
| iran-strike-feb28 | 2026-02-28 03:35:45 | No | 66,000 | 0.855 | 0.84 / 0.86 | -0.0053 | 0.845 | 0.855 | 2.7 |
| iran-strike-feb28 | 2026-02-27 17:21:21 | No | 20,081 | 0.820 | 0.81 / 0.82 | 0.0 | 0.815 | 0.815 | 12.9 |
| iran-strike-feb28 | 2026-02-28 03:10:33 | No | 19,870 | 0.840 | 0.83 / 0.84 | 0.0 | 0.835 | 0.835 | 3.1 |
| iran-strike-feb28 | 2026-02-27 22:52:49 | Yes | 15,000 | 0.197 | 0.18 / 0.2 | -0.0027 | 0.185 | 0.195 | 7.4 |
| iran-strike-feb28 | 2026-02-28 00:07:15 | Yes | 11,272 | 0.200 | 0.2 / 0.21 | -0.01 | 0.195 | 0.205 | 6.1 |
| iran-strike-feb28 | 2026-02-27 22:43:01 | Yes | 10,000 | 0.180 | 0.17 / 0.18 | 0.0 | 0.175 | 0.185 | 7.5 |
| iran-strike-feb28 | 2026-02-28 03:05:35 | Yes | 9,300 | 0.170 | 0.16 / 0.17 | 0.0 | 0.165 | 0.165 | 3.2 |
| iran-strike-feb28 | 2026-02-28 00:03:41 | Yes | 8,798 | 0.200 | 0.19 / 0.21 | -0.01 | 0.195 | 0.205 | 6.2 |
| iran-strike-feb28 | 2026-02-28 05:29:31 | Yes | 8,500 | 0.225 | 0.2 / 0.22 | 0.0046 | 0.195 | 0.205 | 0.8 |
| iran-strike-feb28 | 2026-02-27 20:46:07 | Yes | 7,500 | 0.180 | 0.17 / 0.18 | 0.0 | 0.165 | 0.175 | 9.5 |
| khamenei-out-mar31 | 2026-02-28 06:22:29 | No | 18,896 | 0.778 | 0.7 / 0.72 | 0.0581 | 0.755 | 0.685 | 5.6 |
| khamenei-out-mar31 | 2026-02-28 06:50:59 | Yes | 18,376 | 0.407 | 0.37 / 0.44 | -0.0325 | 0.375 | 0.405 | 5.2 |
| khamenei-out-mar31 | 2026-02-28 11:20:09 | Yes | 13,639 | 0.469 | 0.45 / 0.47 | -0.0009 | 0.455 | 0.495 | 0.7 |
| khamenei-out-mar31 | 2026-02-28 02:14:23 | No | 11,411 | 0.750 | 0.75 / 0.76 | -0.01 | 0.75 | 0.755 | 9.8 |
| khamenei-out-mar31 | 2026-02-28 10:39:09 | No | 10,626 | 0.570 | 0.56 / 0.58 | -0.0099 | 0.545 | 0.565 | 1.3 |
| khamenei-out-mar31 | 2026-02-28 11:25:23 | No | 10,554 | 0.535 | 0.5 / 0.51 | 0.025 | 0.545 | 0.505 | 0.6 |
| khamenei-out-mar31 | 2026-02-28 07:18:01 | Yes | 10,316 | 0.397 | 0.37 / 0.4 | -0.0026 | 0.375 | 0.375 | 4.7 |
| khamenei-out-mar31 | 2026-02-28 08:06:07 | Yes | 10,000 | 0.501 | 0.45 / 0.46 | 0.0415 | 0.45 | 0.455 | 3.9 |
| khamenei-out-mar31 | 2026-02-28 07:31:25 | No | 9,746 | 0.655 | 0.63 / 0.66 | -0.0047 | 0.615 | 0.625 | 4.5 |
| khamenei-out-mar31 | 2026-02-28 07:48:41 | Yes | 7,654 | 0.446 | 0.43 / 0.46 | -0.014 | 0.415 | 0.465 | 4.2 |

## Limits

- **Depth is one token's side.** Polymarket also fills against the opposite token, so a snapshot's asks understate what could fill. The theoretical cost in the output files often exceeds the price paid, for instance $15,000 on Iran Yes paid at 0.197 with only $364 in the snapshot's asks within 2 cents. It is an upper bound, not an estimate of slippage.
- **Rows are taker rows, seen by the second.** The order of a trade and of the book changes inside one second is not known, so a state one second before is used.
- **Reading.** These rows show a price paid close to the visible ask, with mids that mostly move little in 5 minutes. This is a description of a few entries chosen by size, and there is no comparison with other markets here. It says nothing about who knew what.
