# Controls on synthetic tables

Written by `code/ctl_10_synth.py`, 600 synthetic markets, threshold 0.05/6, through the verdict of the plan. 199 H2 draws here against 499 on real data. No real data.

| Scenario | Window | Seed | Bursts | Matched share | Difference | p H1 | Placebo p | H2 observed / median / p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| real null: groups planted, no information | 5 | 1 | 187 | 1.00 | 0.0339 | 0.1239 | 0.0958 | 187 / 10 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 5 | 2 | 160 | 1.00 | -0.0356 | 0.1538 | 0.4551 | 160 / 7 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 5 | 3 | 173 | 1.00 | -0.0214 | 0.4136 | 0.8782 | 173 / 10 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 30 | 1 | 187 | 1.00 | 0.0339 | 0.1239 | 0.8064 | 187 / 11 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 30 | 2 | 160 | 1.00 | -0.0356 | 0.1538 | 0.4351 | 160 / 8 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 30 | 3 | 173 | 1.00 | -0.0215 | 0.4136 | 0.8024 | 173 / 10 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 300 | 1 | 189 | 1.00 | 0.0333 | 0.1259 | 0.6267 | 189 / 16 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 300 | 2 | 164 | 1.00 | -0.0375 | 0.1139 | 0.4790 | 164 / 13 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 300 | 3 | 176 | 1.00 | -0.0173 | 0.5195 | 0.9661 | 176 / 15 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 3600 | 1 | 428 | 1.00 | 0.0263 | 0.1239 | 0.9501 | 428 / 310 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 3600 | 2 | 432 | 1.00 | -0.0324 | 0.0340 | 0.9980 | 432 / 312 / 0.005 | NOT_SUPPORTED |
| real null: groups planted, no information | 3600 | 3 | 472 | 1.00 | -0.0227 | 0.1059 | 0.7824 | 472 / 319 / 0.005 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 5 | 1 | 34 | 1.00 | -0.0595 | 0.2478 | 0.4152 | 34 / 39 / 0.805 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 5 | 2 | 33 | 1.00 | -0.0261 | 0.5614 | 0.9501 | 33 / 38 / 0.850 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 5 | 3 | 40 | 1.00 | -0.0104 | 0.7972 | 0.2196 | 40 / 39 / 0.490 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 30 | 1 | 443 | 1.00 | -0.0054 | 0.5235 | 0.3154 | 443 / 458 / 0.940 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 30 | 2 | 449 | 1.00 | -0.0057 | 0.4635 | 0.4950 | 449 / 457 / 0.890 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 30 | 3 | 461 | 1.00 | 0.0108 | 0.1518 | 0.4192 | 461 / 460 / 0.495 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 300 | 1 | 600 | 1.00 | -0.0073 | 0.9151 | 0.6267 | 600 / 600 / 1.000 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 300 | 2 | 600 | 1.00 | 0.0239 | 0.4136 | 0.8024 | 600 / 600 / 1.000 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 300 | 3 | 600 | 1.00 | 0.0176 | 0.6094 | 0.5030 | 600 / 600 / 1.000 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 3600 | 1 | 600 | 0.00 |  |  |  | 600 / 2036 / 1.000 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 3600 | 2 | 600 | 0.00 |  |  |  | 600 / 2036 / 1.000 | NOT_SUPPORTED |
| real null: independent wallets, dense enough for chance bursts | 3600 | 3 | 600 | 0.00 |  |  |  | 600 / 2036 / 1.000 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 5 | 1 | 0 |  |  |  |  | 0 / 2 / 1.000 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 5 | 2 | 3 | 1.00 | 0.1168 | 0.5305 | 0.3460 | 3 / 2 / 0.295 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 5 | 3 | 2 | 1.00 | -0.3820 | 0.0023 | 0.7643 | 2 / 2 / 0.655 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 30 | 1 | 49 | 1.00 | 0.1078 | 0.0559 | 0.6188 | 49 / 47 / 0.370 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 30 | 2 | 43 | 1.00 | 0.0852 | 0.1958 | 0.1517 | 43 / 44 / 0.630 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 30 | 3 | 50 | 1.00 | -0.0062 | 0.9530 | 0.5549 | 50 / 53 / 0.745 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 300 | 1 | 198 | 1.00 | 0.0590 | 0.0180 | 0.7625 | 198 / 202 / 0.855 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 300 | 2 | 194 | 1.00 | 0.0377 | 0.1538 | 0.8263 | 194 / 196 / 0.720 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 300 | 3 | 206 | 1.00 | 0.0651 | 0.0200 | 0.9102 | 206 / 212 / 0.980 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 3600 | 1 | 733 | 0.81 | 0.0284 | 0.0420 | 0.0120 | 733 / 1050 / 1.000 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 3600 | 2 | 735 | 0.81 | 0.0192 | 0.1858 | 0.4032 | 735 / 1048 / 1.000 | NOT_SUPPORTED |
| trap: crowded tokens win more, no alignment | 3600 | 3 | 745 | 0.79 | 0.0235 | 0.0779 | 0.1118 | 745 / 1098 / 1.000 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 5 | 1 | 18 | 1.00 | 0.1119 | 0.3117 | 0.3234 | 18 / 19 / 0.670 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 5 | 2 | 9 | 1.00 | 0.0898 | 0.5534 | 0.3792 | 9 / 18 / 0.995 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 5 | 3 | 18 | 1.00 | -0.1418 | 0.0919 | 0.0279 | 18 / 22 / 0.895 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 30 | 1 | 144 | 1.00 | 0.0227 | 0.2118 | 0.8064 | 144 / 142 / 0.325 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 30 | 2 | 134 | 1.00 | 0.0332 | 0.0659 | 0.1038 | 134 / 143 / 0.955 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 30 | 3 | 166 | 1.00 | 0.0120 | 0.3796 | 0.9820 | 166 / 160 / 0.140 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 300 | 1 | 191 | 1.00 | 0.1277 | 0.1259 | 0.8942 | 191 / 263 / 1.000 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 300 | 2 | 194 | 1.00 | 0.1670 | 0.0160 | 0.4232 | 194 / 259 / 1.000 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 300 | 3 | 203 | 1.00 | 0.1086 | 0.3916 | 0.4950 | 203 / 288 / 1.000 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 3600 | 1 | 352 | 0.76 | 0.1182 | 0.0020 | 0.8862 | 352 / 912 / 1.000 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 3600 | 2 | 364 | 0.77 | 0.1453 | 0.0020 | 0.3393 | 364 / 912 / 1.000 | NOT_SUPPORTED |
| trap: news day, entrants pile on, token wins, no alignment | 3600 | 3 | 375 | 0.71 | 0.1430 | 0.0020 | 0.2076 | 375 / 969 / 1.000 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 5 | 1 | 183 | 1.00 | -0.0474 | 0.0779 | 0.7944 | 183 / 13 / 0.005 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 5 | 2 | 187 | 1.00 | 0.0167 | 0.4935 | 0.5190 | 187 / 12 / 0.005 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 5 | 3 | 184 | 1.00 | -0.0515 | 0.0380 | 0.5469 | 184 / 13 / 0.005 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 30 | 1 | 212 | 1.00 | -0.0273 | 0.2498 | 0.4671 | 212 / 67 / 0.005 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 30 | 2 | 218 | 1.00 | 0.0100 | 0.6533 | 0.2595 | 218 / 65 / 0.005 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 30 | 3 | 210 | 1.00 | -0.0326 | 0.1399 | 0.2116 | 210 / 63 / 0.005 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 300 | 1 | 330 | 1.00 | 0.0029 | 0.8831 | 0.6946 | 330 / 230 / 0.005 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 300 | 2 | 323 | 1.00 | 0.0277 | 0.1079 | 0.6347 | 323 / 218 / 0.005 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 300 | 3 | 317 | 1.00 | -0.0075 | 0.7293 | 0.7904 | 317 / 210 / 0.005 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 3600 | 1 | 783 | 0.78 | 0.0300 | 0.0200 | 0.0439 | 783 / 1158 / 1.000 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 3600 | 2 | 774 | 0.80 | -0.0036 | 0.6973 | 0.6228 | 774 / 1129 / 1.000 | NOT_SUPPORTED |
| combined trap: crowded tokens win more, plus groups with no information | 3600 | 3 | 814 | 0.82 | -0.0163 | 0.2298 | 0.6307 | 814 / 1109 / 1.000 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 5 | 1 | 176 | 1.00 | 0.0427 | 0.1179 | 0.6587 | 176 / 27 / 0.005 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 5 | 2 | 178 | 1.00 | -0.0465 | 0.0639 | 0.9900 | 178 / 29 / 0.005 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 5 | 3 | 196 | 1.00 | -0.0555 | 0.0260 | 0.1876 | 196 / 29 / 0.005 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 30 | 1 | 306 | 1.00 | 0.0262 | 0.1499 | 0.2196 | 306 / 146 / 0.005 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 30 | 2 | 305 | 1.00 | -0.0059 | 0.7033 | 0.9461 | 305 / 153 / 0.005 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 30 | 3 | 322 | 1.00 | -0.0190 | 0.2657 | 0.8822 | 322 / 157 / 0.005 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 300 | 1 | 345 | 1.00 | 0.1850 | 0.0020 | 0.2475 | 345 / 263 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| combined trap: news day wins, plus groups with no information | 300 | 2 | 346 | 1.00 | -0.0454 | 0.5594 | 0.3114 | 346 / 272 / 0.005 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 300 | 3 | 369 | 1.00 | 0.0638 | 0.1778 | 0.4790 | 369 / 276 / 0.005 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 3600 | 1 | 526 | 0.78 | 0.1173 | 0.0020 | 0.4471 | 526 / 917 / 1.000 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 3600 | 2 | 540 | 0.77 | 0.0391 | 0.0619 | 0.9621 | 540 / 930 / 1.000 | NOT_SUPPORTED |
| combined trap: news day wins, plus groups with no information | 3600 | 3 | 536 | 0.74 | 0.0688 | 0.0040 | 0.4112 | 536 / 935 / 1.000 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 5 | 1 | 187 | 1.00 | 0.0638 | 0.0140 | 0.2555 | 187 / 10 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 5 | 2 | 160 | 1.00 | 0.0512 | 0.0779 | 0.6467 | 160 / 7 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 5 | 3 | 173 | 1.00 | 0.0354 | 0.1698 | 0.5190 | 173 / 10 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 30 | 1 | 187 | 1.00 | 0.0638 | 0.0140 | 0.6028 | 187 / 11 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 30 | 2 | 160 | 1.00 | 0.0512 | 0.0779 | 0.2515 | 160 / 8 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 30 | 3 | 173 | 1.00 | 0.0354 | 0.1698 | 0.7545 | 173 / 10 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 300 | 1 | 189 | 1.00 | 0.0629 | 0.0140 | 0.9621 | 189 / 16 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 300 | 2 | 164 | 1.00 | 0.0516 | 0.0839 | 0.5110 | 164 / 13 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 300 | 3 | 176 | 1.00 | 0.0385 | 0.1558 | 0.9102 | 176 / 15 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 3600 | 1 | 428 | 1.00 | 0.0341 | 0.0460 | 0.7745 | 428 / 310 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 3600 | 2 | 432 | 1.00 | -0.0096 | 0.5375 | 0.9940 | 432 / 312 / 0.005 | NOT_SUPPORTED |
| medium: planted groups at price plus 0.10 | 3600 | 3 | 472 | 1.00 | -0.0063 | 0.6993 | 0.7944 | 472 / 319 / 0.005 | NOT_SUPPORTED |
| strong: planted groups at price plus 0.25 | 5 | 1 | 187 | 1.00 | 0.1696 | 0.0020 | 0.3074 | 187 / 10 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| strong: planted groups at price plus 0.25 | 5 | 2 | 160 | 1.00 | 0.1560 | 0.0020 | 0.4431 | 160 / 7 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| strong: planted groups at price plus 0.25 | 5 | 3 | 173 | 1.00 | 0.1436 | 0.0020 | 0.4232 | 173 / 10 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| strong: planted groups at price plus 0.25 | 30 | 1 | 187 | 1.00 | 0.1696 | 0.0020 | 0.9980 | 187 / 11 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| strong: planted groups at price plus 0.25 | 30 | 2 | 160 | 1.00 | 0.1560 | 0.0020 | 0.7066 | 160 / 8 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| strong: planted groups at price plus 0.25 | 30 | 3 | 173 | 1.00 | 0.1436 | 0.0020 | 0.9341 | 173 / 10 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| strong: planted groups at price plus 0.25 | 300 | 1 | 189 | 1.00 | 0.1726 | 0.0020 | 0.9261 | 189 / 16 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| strong: planted groups at price plus 0.25 | 300 | 2 | 164 | 1.00 | 0.1532 | 0.0020 | 0.5110 | 164 / 13 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| strong: planted groups at price plus 0.25 | 300 | 3 | 176 | 1.00 | 0.1443 | 0.0020 | 0.6587 | 176 / 15 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| strong: planted groups at price plus 0.25 | 3600 | 1 | 428 | 1.00 | 0.0832 | 0.0020 | 0.5190 | 428 / 310 / 0.005 | PREDICTIVE_TIMING_PATTERN |
| strong: planted groups at price plus 0.25 | 3600 | 2 | 432 | 1.00 | 0.0220 | 0.1938 | 0.9301 | 432 / 312 / 0.005 | NOT_SUPPORTED |
| strong: planted groups at price plus 0.25 | 3600 | 3 | 472 | 1.00 | 0.0301 | 0.0599 | 0.1836 | 472 / 319 / 0.005 | NOT_SUPPORTED |

## Reading

Passes of the verdict, out of 3 seeds: {
"real null: groups planted, no information, w=5": 0,
"real null: groups planted, no information, w=30": 0,
"real null: groups planted, no information, w=300": 0,
"real null: groups planted, no information, w=3600": 0,
"real null: independent wallets, dense enough for chance bursts, w=5": 0,
"real null: independent wallets, dense enough for chance bursts, w=30": 0,
"real null: independent wallets, dense enough for chance bursts, w=300": 0,
"real null: independent wallets, dense enough for chance bursts, w=3600": 0,
"trap: crowded tokens win more, no alignment, w=5": 0,
"trap: crowded tokens win more, no alignment, w=30": 0,
"trap: crowded tokens win more, no alignment, w=300": 0,
"trap: crowded tokens win more, no alignment, w=3600": 0,
"trap: news day, entrants pile on, token wins, no alignment, w=5": 0,
"trap: news day, entrants pile on, token wins, no alignment, w=30": 0,
"trap: news day, entrants pile on, token wins, no alignment, w=300": 0,
"trap: news day, entrants pile on, token wins, no alignment, w=3600": 0,
"combined trap: crowded tokens win more, plus groups with no information, w=5": 0,
"combined trap: crowded tokens win more, plus groups with no information, w=30": 0,
"combined trap: crowded tokens win more, plus groups with no information, w=300": 0,
"combined trap: crowded tokens win more, plus groups with no information, w=3600": 0,
"combined trap: news day wins, plus groups with no information, w=5": 0,
"combined trap: news day wins, plus groups with no information, w=30": 0,
"combined trap: news day wins, plus groups with no information, w=300": 1,
"combined trap: news day wins, plus groups with no information, w=3600": 0,
"medium: planted groups at price plus 0.10, w=5": 0,
"medium: planted groups at price plus 0.10, w=30": 0,
"medium: planted groups at price plus 0.10, w=300": 0,
"medium: planted groups at price plus 0.10, w=3600": 0,
"strong: planted groups at price plus 0.25, w=5": 3,
"strong: planted groups at price plus 0.25, w=30": 3,
"strong: planted groups at price plus 0.25, w=300": 3,
"strong: planted groups at price plus 0.25, w=3600": 1
}

The real nulls and both traps must stay at or near 0. Medium and strong show power on this synthetic size only. Real effective n is events, so real power is lower than a passing medium suggests. A real effect smaller than the medium scenario can be missed: not supported is not disproved.
