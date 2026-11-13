# Follow-up of 12-13 November 2026: the Nobel 2025 distributor (C7) and the Ballon d'Or accounts on Base, Arbitrum and Optimism

Data read on 12 November 2026 from public, keyless sources (Blockscout API v2, public JSON-RPC nodes, Relay requests API v2,
Polymarket gamma public profiles and data-api v2, Polymarket CLOB price history, Across deposit status). An address is not a
person. These accounts are subjects of investigation, not demonstrated insiders. Raw responses are not published; their URLs,
SHA-256 and fetch times are listed in `data/raw_response_index.csv`. Collectors: `tools/`.

## 1. Nobel Peace Prize 2025 (case C7): one key funds eight accounts and receives all their withdrawals

### Summary

- The Gnosis Safe of the account **6741** has a single owner, `0xe206961002feebd9edb152eed9b630a351874043` (the funder below; threshold 1), already at the block of
  the first transfer, before the announcement.
- Between 2025-10-09 22:40:19 and 2025-10-10 03:30:43 UTC that key sends **372,521.54 USDC** (native Polygon USDC) in
  14 transfers to **eight** Polymarket accounts: the six handles of the public C7 roster (6741, fmaduro, trumpdeservesit,
  aenews0, madurowilllose, dirtycup) and two accounts not on it (striketheboats, pinkuniforms).
- The public profile named **aenews0** is the proxy `0x4bac00c61a02275d681f3857cdc5ae315f1f7075` (the C7 notes on `main` list
  aenews0 without a proxy).
- Each profile was created 45 seconds to 6 minutes before its first funding (6741: 74 minutes).
- All 16 Relay withdrawal requests of the eight accounts went to the funder (15,
  523,060.18 USDC) or to the 6741 proxy (1). On Polygon the funder's USDC inflows equal its outflows to the cent; its
  remaining balance (0.00001 USDC) is exactly the difference.
- **Not demonstrated:** that one person controls the eight accounts (seven Safes have distinct owner keys that never transacted
  on-chain), and inside information (seven accounts first bought after the public repricing, see section 1.5).

### 1.1 The eight accounts

| Handle | Polymarket proxy | Safe owner | Profile created (UTC) | First funding (UTC) | Funded USDC | First Machado buy (UTC) | Nobel buys before 09:00 UTC | Redeemed |
|---|---|---|---|---|---|---|---|---|
| 6741 (C7 roster) | `0xa430506774f9efaf39903ee7e0db1351f66891ca` | **the funder** | 2025-10-09T21:26:43 | 2025-10-09T22:40:19 | 90,000.00 | 2025-10-09T22:42:57 at 0.048 | 38,787.06 | 80,439.75 |
| fmaduro (C7 roster) | `0x1973177faa69b94b4afab818e612a7c05b3c01a9` | `0xb08e902e7b7cc28b6b0bb54fbae9b9db49b56c3a` | 2025-10-10T00:42:47 | 2025-10-10T00:43:33 | 44,000.00 | 2025-10-10T00:44:43 at 0.340 | 2,410.37 | 27,021.49 |
| trumpdeservesit (C7 roster) | `0x03f8aae7ae1687ef7e2d55e4429e72e9a95d8541` | `0x9693dc7dc0f11a98774f5e8478eacecadad66a80` | 2025-10-10T01:02:58 | 2025-10-10T01:04:15 | 30,000.00 | 2025-10-10T01:07:25 at 0.495 | 10,286.32 | 21,189.74 |
| striketheboats | `0xa9c57a20cb8433a269976bb35eb872bd11380bd9` | `0x4a574d7287421221168bdf21847170b52b73e9d2` | 2025-10-10T01:09:45 | 2025-10-10T01:10:37 | 25,000.00 | 2025-10-10T01:12:41 at 0.566 | 17,046.95 | 29,483.45 |
| aenews0 (C7 roster) | `0x4bac00c61a02275d681f3857cdc5ae315f1f7075` | `0x1c19c01f86bc8a3c9661c4ad14a236f24d93717a` | 2025-10-10T01:30:21 | 2025-10-10T01:32:27 | 30,000.00 | 2025-10-10T01:33:49 at 0.652 | 8,618.80 | 19,921.38 |
| madurowilllose (C7 roster) | `0x8507124d416dd181ea552e01a0dfed19ab0b1086` | `0x6b0c628bbb36467517932a54036e657024dd7557` | 2025-10-10T01:45:08 | 2025-10-10T01:46:17 | 60,000.00 | 2025-10-10T01:54:09 at 0.650 | 30,449.19 | 72,040.10 |
| pinkuniforms | `0x2612496ab8f1d774f116f28b50769971936c92de` | `0xd1faa93b03b17734249782ddfba8338bc7d1bc34` | 2025-10-10T03:06:07 | 2025-10-10T03:11:55 | 25,000.00 | 2025-10-10T03:23:29 at 0.655 | 19,216.72 | 31,122.77 |
| dirtycup (C7 roster) | `0x234cc49e43dff8b3207bbd3a8a2579f339cb9867` | `0xe388642738e84f52f28b12a65b905b3d214c2848` | 2025-10-10T03:25:58 | 2025-10-10T03:26:43 | 68,521.54 | 2025-10-10T03:29:19 at 0.677 | 25,496.43 | 99,007.52 |

Owner keys of the seven other Safes: no transaction on Polygon or Ethereum (`data/owner_keys_activity.csv`).

### 1.2 The 14 funding transfers (Polygon, USDC `0x3c499c542cef5e3811e1192ce70d8cc03d5c3359`)

| UTC | To | USDC | Transaction |
|---|---|---|---|
| 2025-10-09T22:40:19 | 6741 | 40,000.00 | `0xe4dd2102d6dd649611557415aa28457e792c5abaac963e5a6fbb7a3b6f3e2516` |
| 2025-10-09T23:21:39 | 6741 | 30,000.00 | `0x6463dc7bd0b380ee6974582c5565b7e7e6a21d7d96443353dd08bdc3cbafcc71` |
| 2025-10-10T00:29:43 | 6741 | 20,000.00 | `0x120f592d2472e7151abb8090b274fbaae832bc3074b12ec6eb8d581a7de52637` |
| 2025-10-10T00:43:33 | fmaduro | 30,000.00 | `0xfd981aca74f1b9ae6e9cdb9a726c82d7d3d3a65876ca34b8ae4290562209b838` |
| 2025-10-10T01:02:07 | fmaduro | 10,000.00 | `0x1d72dd86fdbe2ea18151c75bb6639110d5febd8d638f2fb5a0143c380d8eb267` |
| 2025-10-10T01:02:17 | fmaduro | 4,000.00 | `0x09938359fc5ec14c01f07cd6dba4fad76dbdb45a2bb46c516d87f6b1283ff483` |
| 2025-10-10T01:04:15 | trumpdeservesit | 30,000.00 | `0x8ccc80d84f4cb1002fd9af6a96da6403fbc718602ee8703e78ddd379068efe36` |
| 2025-10-10T01:10:37 | striketheboats | 25,000.00 | `0xc463fe747ae655f8af92bedfcc1d00c3beb2e44ec68c0b14dbe4af4a9171c962` |
| 2025-10-10T01:32:27 | aenews0 | 30,000.00 | `0xf3366b67b279de1cfea9927defe085b6a8a2706e164361a2c2af529163b12251` |
| 2025-10-10T01:46:17 | madurowilllose | 30,000.00 | `0x36a7fc28b0ade3f6a56b48e716ddaf6a574ff671836919e1df6452875760b1d6` |
| 2025-10-10T01:59:35 | madurowilllose | 30,000.00 | `0x0c26ce2d91e2fb79833b9af97020ed15322c35e21e35d2f45de23971eccf1077` |
| 2025-10-10T03:11:55 | pinkuniforms | 25,000.00 | `0x78b680338af0a0a3a1f30ee7df88bf863dd4f1fa49505a4a83dbf95d021baff1` |
| 2025-10-10T03:26:43 | dirtycup | 20,000.00 | `0x1b6836d22eb515b8eba1f8a5cb9c7c0909ded9519d4b47f63a63d1a6dce12d9e` |
| 2025-10-10T03:30:43 | dirtycup | 48,521.54 | `0x837bb79029d2749c2d3085da352c668ab6fca5f9a454a0d6a6dd0e5ad8c6d9fb` |

### 1.3 The 16 withdrawals (Relay requests, all successful)

| Created (UTC) | Account | Recipient | USDC | Relay request | Input transaction |
|---|---|---|---|---|---|
| 2025-10-10T00:28:03 | 6741 | funder | 29,624.18 | `0x633419596e18a7e409eb469dda9e747a84f2bb08a719bff073467ca052d43eaf` | `0x9bed484b7108cd6a1453d8d776e8ad1f29f2b40565da8074fc77c527dffc6375` |
| 2025-10-10T01:30:11 | striketheboats | funder | 7,109.46 | `0xda9589a4aab720c32f8534366dd9bb75aa8f9ee160647d0f8feeb8549bbf1840` | `0xbad886caa770283f91417ecc12ab6f9fcdcdcadd51edc04d5d51eff75a0143b2` |
| 2025-10-10T01:44:53 | fmaduro | funder | 32,587.42 | `0x7cfd4729ebf7be8c9c0f7ddfe0d50ba0011b400a46fa84cc6720f3591ffc2fb9` | `0x443c2cceecef85d725bb31ea095e6ff886a6f28f6fda90ce1c317dbf2dfa3713` |
| 2025-10-10T02:37:49 | madurowilllose | funder | 5,540.69 | `0x4f8ad0013a65c108dba4e32a0980b28ced69daacb5380f7f82076b4c0e6591af` | `0x488dd842c8149531d999cb4fb13f990a1d54f08e82c8e8518f939ebfc1c762c4` |
| 2025-10-10T03:09:07 | aenews0 | funder | 16,614.74 | `0xd8af33de172dc28b9bc9a30827fe0e7053b27d199f6785433bf1b55ba6ae6b18` | `0xb5243bb26936a24ab10c1cabb799fc487aaa4fd98bec9b216c095ad2fefe5c77` |
| 2025-10-10T03:13:33 | 6741 | funder | 26,720.11 | `0x68d1d300cf77715ace9aec1c5fa813227280a80fdd7b83703099628569b1477b` | `0xe5265b4b8ca2d88ab091d88c6ee368f9467fe92416396f6441bd51fc166ca6d8` |
| 2025-10-10T03:25:48 | pinkuniforms | funder | 4,672.53 | `0xa127f3f1f53006d7fda149c361450817abaa79d6a39693a82df49a9dcae12c7d` | `0xcf47bbbf5c29c0523d2d9fb329e33c9c9b4dd3460244d064c5554bbe8cef9edf` |
| 2025-10-10T12:47:58 | fmaduro | funder | 27,010.64 | `0xf2f479f0a3d2d3e3066c9fd079c00ae7df1172c3f5239df9283a0d567c5b7e10` | `0x170cc94b75eb514a3986a99585fd6157d001a4b19c4b2c7e0afd1085de6acbb1` |
| 2025-10-10T12:48:48 | 6741 | funder | 80,731.95 | `0xcfd9c615915f06384919edf8dee00a2d4d170c5cf4c05a609f97db78892fb9fc` | `0x8f27e12c19ed6ec444821ed6020a8bea327ea9236bc3fd99440c2f0bc65b873e` |
| 2025-10-10T12:49:52 | dirtycup | funder | 99,094.15 | `0xb6061f82cf53a93a53582415222141b0762c3f3ff585ce4d85cafe55fc244215` | `0xdee0408acc49b3523803b16dc7316424670e2f124991d59f08bc3229323d450c` |
| 2025-10-10T12:51:36 | pinkuniforms | group account `0xa430506774f9efaf39903ee7e0db1351f66891ca` | 31,109.32 | `0xad7a7a7ba65b543eb31c08b0fc6a100e9f75f0d5865bcb79d5438e749269c0e7` | `0x1c2241855946d0656f8198dd6f4fe03e8473a465815e3b6c7e82bc555fbd25fa` |
| 2025-10-10T12:53:04 | madurowilllose | funder | 72,006.99 | `0x96a45e2fbd98f3fbfea8f0e71e909970b171a006d49b9015395906bf22c35a9e` | `0xf034d1b693306431ddef8fac2c1fc37d64600c2cd534edb7d7af88988099360d` |
| 2025-10-10T12:54:31 | aenews0 | funder | 19,909.96 | `0xea82606691106964d89cc26b171ee4afb9161018352a0d869f420359dc473bee` | `0xa18a1f7d3f928cbdfc163c93a2709f31ba1048c7b533296d0933f612f37d578c` |
| 2025-10-10T12:54:36 | 6741 | funder | 31,091.78 | `0x7adabf0d056ed43a741dbbc8763f686888142778eb9b924fd561e0897ca51880` | `0xba530e97889b3ca1865b4f1bca4b9d7716da6b2c29fef95647da859f7fa46ab3` |
| 2025-10-10T12:57:28 | striketheboats | funder | 29,468.39 | `0xe670504133682a3842f39ce6811b1f370f29088049df371f6d10d1a706a1f167` | `0x139be5a86718361f77da486ce4b1445ee09b619c0d7fe5832e5bc011044c865c` |
| 2025-10-10T13:00:22 | trumpdeservesit | funder | 40,877.20 | `0xbf82e8c1b83963e609b25e0e6c24402590ae3169209a3ec43a47ee24af1f3a41` | `0xe20167604e04a36d0376d37cd949f3038c3bf4f2ffbdd5ee04bbeecf747b45d4` |

The recipient of a withdrawal is part of the Safe `execTransaction` signed by the account owner; the relayer only submits it
(checked on one request; the Relay API allows about one call per minute).

### 1.4 Capital origin and exits

- 2025-10-09 22:11-22:12 UTC, Ethereum: `0x3e2c6d068fc6958684e836998285e3a836dbd96f` (active since 2021-02-05, first ETH from a
  Binance hot wallet on 2021-02-10) sells 6.2178 stETH and hands 1.8368 WBTC to a UniswapX solver; its ETH balance rises from
  6.32 to 57.33 ETH. At 22:13:47 and 22:18:23 it sends 0.022929 and 57.333146 ETH to the funder.
- 22:20:59: the funder swaps 57.3 ETH for 249,677.38 USDC; 22:23:35: Across deposit 3253263 to Polygon, filled by
  `0x609bb6181c0f916bd27e934b24c72bedddbc3e1c5f7c3013028b827a4b139ba7` (249,652.41 USDC paid by an Across relayer).
- 22:26:39, Polygon: the funder's first 183.95 POL, from `0x71d4249079684479f2651745fa2fcd79c9b45f53` (Blockscout tag
  "FixedFloat 3", single source).
- After the announcement the funder sends 330,191.06 USDC (Polygon), then 39,983.21 USDC and 6.950374 ETH (Ethereum) to
  `0xb282b48ae713fa2201282e298f3393130c4f851d`; 70,000 USDC go through Across to the funder's own address on Ethereum. On 2026-04-15 that treasury sends
  165,093.03 and 164,927.94 USDC to the Relay depository.

Ethereum legs of the funder and of its source (`data/funder_and_source_ethereum_flows.csv`, official tokens and ETH only):

| UTC | From | To | Amount | Transaction |
|---|---|---|---|---|
| 2025-10-09T22:11:11 | `0x3e2c6d068fc6958684e836998285e3a836dbd96f` | `0x4028daac072e492d34a3afdbef0ba7e35d8b55c4` | 6.217774 stETH | `0x8f897edee6c23a5f3395120916a9160e4a3003b004575891e182842224353f21` |
| 2025-10-09T22:11:11 | `0x66a9893cc07d91d95644aedd05d03f95e1dba8af` | `0x3e2c6d068fc6958684e836998285e3a836dbd96f` | 6.112318 ETH | `0x8f897edee6c23a5f3395120916a9160e4a3003b004575891e182842224353f21` |
| 2025-10-09T22:12:23 | `0x3e2c6d068fc6958684e836998285e3a836dbd96f` | `0x225a38bc71102999dd13478bfabd7c4d53f2dc17` | 1.836769 WBTC | `0xe40b4578fcb782a0ef7f1058f8d2d5c6770476d11461949ba39f36b754b076be` |
| 2025-10-09T22:12:23 | `0x00000011f84b9aa48e5f8aa8b9897600006289be` | `0x3e2c6d068fc6958684e836998285e3a836dbd96f` | 51.037255 ETH | `0xe40b4578fcb782a0ef7f1058f8d2d5c6770476d11461949ba39f36b754b076be` |
| 2025-10-09T22:13:47 | `0x3e2c6d068fc6958684e836998285e3a836dbd96f` | `0xe206961002feebd9edb152eed9b630a351874043` | 0.022929 ETH | `0x521010dcebdbb95468792aea68337c599cc5685aa974c1b12454509d6ce4e7b8` |
| 2025-10-09T22:18:23 | `0x3e2c6d068fc6958684e836998285e3a836dbd96f` | `0xe206961002feebd9edb152eed9b630a351874043` | 57.333146 ETH | `0x2b2dc98b5322e96a486a325c7c14c2623287709f2b711008b146ca9a67d8c27a` |
| 2025-10-09T22:20:59 | `0xe206961002feebd9edb152eed9b630a351874043` | `0x0000000000001ff3684f28c67538d4d072c22734` | 57.300000 ETH | `0xc49cede96c20fb850e967fa46a5c8b55fea552d135a820ffaeea48faa17d695b` |
| 2025-10-09T22:20:59 | `0x207e1074858a7e78f17002075739ed2745dbaece` | `0xe206961002feebd9edb152eed9b630a351874043` | 249,677.378613 USDC | `0xc49cede96c20fb850e967fa46a5c8b55fea552d135a820ffaeea48faa17d695b` |
| 2025-10-09T22:23:35 | `0xe206961002feebd9edb152eed9b630a351874043` | `0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5` | 249,677.378613 USDC | `0xde3c36d433640f1b2e693f7e4619ded6abbaa3f7ac228321b621f7b0b523d53b` |
| 2025-10-09T22:25:35 | `0xe206961002feebd9edb152eed9b630a351874043` | `0xe113795ee908223da45c800ec0ac4d8bfb416f8f` | 0.010000 ETH | `0x1163ac2dbf42d5a6413efd547d59dc09c1c195e177dc46440433e2bbf1ad373e` |
| 2025-10-09T23:55:47 | `0xe206961002feebd9edb152eed9b630a351874043` | `0x43436b273ba557295ad6df3c1fb1fd91194a2e6b` | 0.001030 ETH | `0x95ed54f937b1460b2825c0085e163b69f410f231d00f20bc0f7caa6d4f961c53` |
| 2025-10-10T02:16:11 | `0xe206961002feebd9edb152eed9b630a351874043` | `0xaa97ae57dd5b49f321a2c5d06500f9ffa4d55c8c` | 0.001031 ETH | `0x1e7c7a972f3d512fe3ef072a22231af1148cbcdac39b54414cdb031aab19966f` |
| 2025-10-10T14:43:11 | `0xeff7337b37c8d217d01cb8223fe497abd75190d5` | `0xe206961002feebd9edb152eed9b630a351874043` | 69,983.213228 USDC | `0x778dce975a92059454edf1e9f84fb319e18ead22a0f5c6b823d3b3fe074721c0` |
| 2025-10-10T14:50:59 | `0x00000011f84b9aa48e5f8aa8b9897600006289be` | `0xe206961002feebd9edb152eed9b630a351874043` | 6.908976 ETH | `0x43cb1aea9db5480993fc80d0206a9513b6dcc574b757468984e8cd28c28b0abb` |
| 2025-10-10T14:50:59 | `0xe206961002feebd9edb152eed9b630a351874043` | `0x225a38bc71102999dd13478bfabd7c4d53f2dc17` | 30,000.000000 USDC | `0x43cb1aea9db5480993fc80d0206a9513b6dcc574b757468984e8cd28c28b0abb` |
| 2025-10-10T15:26:59 | `0xe206961002feebd9edb152eed9b630a351874043` | `0xb282b48ae713fa2201282e298f3393130c4f851d` | 39,983.213228 USDC | `0x93083ee195dc1c042549bb9b5c760d6c7afc2b05cfb11e7e4125d1151a592416` |
| 2025-10-10T15:29:11 | `0xe206961002feebd9edb152eed9b630a351874043` | `0xb282b48ae713fa2201282e298f3393130c4f851d` | 6.950374 ETH | `0x42246567a38304af29f0f4a0d5322487bacbd0247ac8db065534935d18ffdb9b` |

### 1.5 Timing against the price

Machado "Yes" (`data/machado_yes_price_history.json`, 5-minute points): 0.035-0.037 until 22:30 UTC on 2025-10-09, 0.075 at
22:45, 0.390 at 23:00, 0.652 at 23:30, 0.728 at 00:00, between 0.36 and 0.73 during the night. 6741 first buys at 22:42:57 at
0.048, two minutes after its funding: its purchases are part of the move. The seven other accounts first buy between 00:44:43
and 03:29:19 UTC at 0.34 to 0.68, after the public repricing, next to large buyers unrelated to the funder.

### 1.6 Verification

Three independent reviews: (1) chain replay through public JSON-RPC, not Blockscout: all 14 transfers, the Safe owner at
the current block and at block 77,472,527, all 16 Relay deliveries, the Across deposit and fill, and the exits;
(2) an attempt to refute the interpretation, which led to the wording above (ownership is shown for 6741 only; a group with a
common treasurer is not excluded; no inside information shown for seven accounts); (3) a novelty check against this repository.

### 1.7 Relation to the repository

The notes `research_notes/c5-c7-recovery-overlaps-2026-11-07/REPORT.md` and `research_notes/c1-c7-primary-anchors-2026-11-07/REPORT.md`
say that the alleged distributor of about $250k has no address and that aenews0 has no proxy. The public branch
`research/global-insider-forensics-20261102` (commit `34ff284`, 2026-11-03) already holds, in machine-generated tables, the
funder as the owner key of 6741, its upstream and its exits (`results/FUNDERS_AND_EXITS.md`, `results/graphs/nodes.json`,
`results/discovery/queue.json`). This follow-up connects those data to case C7, verifies them and adds the handle mappings,
the creation sequence, the withdrawal loop and the timing.

### 1.8 Alternative explanations

- The funder is a service (OTC desk, market maker, escrow): unlikely. Fresh wallet, first movement on 2025-10-09, counterparties
  limited to the Relay router, the Across bridge, the eight accounts and the treasury, no tag.
- A group of people with a common treasurer: plausible, not refuted.
- The relayer chose the recipients: refuted on the request read (recipient inside the owner-signed data).
- Inside information: not shown; only 6741 bought before the public move, and its own purchases may have started it.

## 2. Ballon d'Or 2026: Base, Arbitrum and Optimism

### 2.1 No direct transfer and no shared counterparty

`investigations/ballon-dor-flow-trace/STATUS.md` records Base and BSC as unread (anti-bot on `base.blockscout.com`). On
12 November 2026 the Base API answered. For the 40 EVM addresses of the 11 case files
(`investigations/ballon-dor-flow-trace/sources/state/pairs.json`), transactions, token transfers and internal transactions were
read on Base, Arbitrum and Optimism, with complete pagination: 24 edges kept (native ETH and official USDC, USDbC,
USDC.e, USDT, WETH, DAI, wstETH), **0 direct transfers** between case files, **0 shared
counterparties**. Spam NFTs, airdrop tokens and look-alike USDC tokens were excluded. BSC is still unread (no free history).

| Chain | UTC | From | To | Amount | Transaction |
|---|---|---|---|---|---|
| arbitrum | 2026-10-26T09:40:40 | `0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055` | `0xb3afcdc711378d17ca1a1000770af5a0b78bb0ba` | 15982.842 USDC | `0xc579ce36eea56ec37480b2d3c268f1a137af674c3cdc55c2d33f382a00840a32` |
| arbitrum | 2026-10-26T09:40:45 | `0xb3afcdc711378d17ca1a1000770af5a0b78bb0ba` | `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 15982.842 USDC | `0x02a46fe71e8f8edf64c1e22f8b0a1b1d5e94c36c2736a0c840c45fafcf1825eb` |
| arbitrum | 2026-10-27T22:58:05 | `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | `0xe820ecb3c6f48a420a5538046cab73d2f40987cd` | 27724.79 USDC | `0x521dbd22f8e00ba8ac55737e2a3479c76ea1162984b97815b4ea4c53a4f8595c` |
| arbitrum | 2026-10-27T22:58:08 | `0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50` | `0xe820ecb3c6f48a420a5538046cab73d2f40987cd` | 1e-05 ETH | `0x354c1a50144ff28a7183b938b097547607add9a873319f6839c34d1783ad3f7c` |
| arbitrum | 2026-10-27T22:58:10 | `0xe820ecb3c6f48a420a5538046cab73d2f40987cd` | `0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50` | 7.8166217e-06 ETH | `0xcada414b8291561d7e6bc3e099a7c94004e925f2a70cb44e8ebcb96c2af8ef8b` |
| arbitrum | 2026-10-27T22:58:10 | `0xe820ecb3c6f48a420a5538046cab73d2f40987cd` | `0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50` | 27724 USDC | `0xa06fecae758b361f2acf0c2198c5f399c89326806e0906d58561c6eb338640da` |
| arbitrum | 2026-10-27T23:05:06 | `0x3ab2f1e0bfc85d3f66bc52980b514b1f2c4a1d50` | `0xe820ecb3c6f48a420a5538046cab73d2f40987cd` | 2.7e-05 USDC | `0x44fd5ff729fec7609c0b838c249e7d2438b22caece4189e99cbfd45e6842da4b` |
| arbitrum | 2026-10-27T23:08:54 | `0x3ab2edbfcd61499cc24326115703acfde7c07d50` | `0xe820ecb3c6f48a420a5538046cab73d2f40987cd` | 2.7e-05 USDC | `0xdcbc8a9b7ccecc41470795d8443af4182d3ab8e2723c726a839ac551aecac4a6` |
| arbitrum | 2026-10-28T01:10:06 | `0x3ab2f1e0bfc85d3f66bc52980b514b1f2c4a1d50` | `0xe820ecb3c6f48a420a5538046cab73d2f40987cd` | 2.7e-05 USDC | `0xa0187e2a2d60ec215f41b3e6ce684762c7fe39bfaa49f662ceda9bb1624e447d` |
| arbitrum | 2026-10-28T01:13:47 | `0x3ab2edbfcd61499cc24326115703acfde7c07d50` | `0xe820ecb3c6f48a420a5538046cab73d2f40987cd` | 2.7e-05 USDC | `0xa7890ebfd0658ae451a418e0a7cc776a0d1ab9481f90d568c8d862e347c4345e` |
| arbitrum | 2026-10-29T20:54:55 | `0x555ce236c0220695b68341bc48c68d52210cc35b` | `0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c` | 75724.742 USDC | `0x88a0d82f0453c76294e665fc884069773b486f4c57b9ba88a6dde84f40f466b7` |
| arbitrum | 2026-10-29T20:54:56 | `0xe78af23df2f2168132b4628aea681c0e6ebba7d7` | `0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c` | 2e-05 ETH | `0xb1a2f3a974352781b6da9dc896d9c9e897e410a33040c521c00a09e46d3c9c14` |
| arbitrum | 2026-10-29T20:55:52 | `0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c` | `0xa95d9c1f655341597c94393fddc30cf3c08e4fce` | 75724.74 USDC | `0x5c5e1650625c27fdc99cd69993a79132db223b899fef7b1b6b85911cf0fc223a` |
| arbitrum | 2026-10-29T22:11:18 | `0x0000000000000000000000000000000000000000` | `0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c` | 73001.185 USDC | `0x6edc469d422b1c11a78807dcf90a7d2253b32ca319d2319cfb8c8d3f718f55a5` |
| arbitrum | 2026-10-29T22:11:59 | `0xe7351fd770a37282b91d153ee690b63579d6dd7f` | `0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c` | 0.034299694 ETH | `0x1609361dc493ec13dc46cb99ab042e69b9a404c0d490e9b605fc66b498118739` |
| base | 2024-12-17T01:45:43 | `0x1b1d2149d656f8ca33fb633e6f642b5a2426b53d` | `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | 0.0027463 ETH | `0xc52d83c13c7c39cfbadb014f76d0d1b9fae3776b852438041b9ae99488e8650b` |
| base | 2024-12-17T01:54:17 | `0x1b1d2149d656f8ca33fb633e6f642b5a2426b53d` | `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | 0.00274595 ETH | `0xb4197dab4efc3472fcf4014518660b8d3a92500bbdfba95687f30cf604b1356c` |
| base | 2024-12-17T01:59:45 | `0x1b1d2149d656f8ca33fb633e6f642b5a2426b53d` | `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | 0.00274903 ETH | `0x0b3e4d32b4ff930cc949b30d9f39045d492bf52798081adc968f30bbc844cc46` |
| base | 2024-12-17T02:10:49 | `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | `0x4450ff76f8bea943aca0e61208be7328da6f1d8f` | 0.008 ETH | `0x92d8fce2c7835a2eb13f936419520874a1b2bfed6ddd93360ba9e7ca01bed9af` |
| base | 2025-02-07T02:54:35 | `0x4200000000000000000000000000000000000010` | `0x408ce42ac7538e5a6f53324585075470d1b3c5b3` | 0.4 ETH | `0x6fc91a651d78e40b2469c274ca22ddc4e6d29ba27e50d01361824c8283fb3e9a` |
| base | 2025-02-07T03:41:53 | `0x408ce42ac7538e5a6f53324585075470d1b3c5b3` | `0x6ff5693b99212da76ad316178a184ab56d299b43` | 0.1 ETH | `0xb115fcf7c182df805788111c3c5fffe9e5d39ed25af2422f378aeb74cbc879be` |
| base | 2025-02-07T03:42:53 | `0x408ce42ac7538e5a6f53324585075470d1b3c5b3` | `0x6ff5693b99212da76ad316178a184ab56d299b43` | 0.15 ETH | `0xe5cd4e9a62d166c77aefbf6cbbc9863b1ffbf4002718c369ffda53ac4327fa27` |
| base | 2025-12-03T23:40:13 | `0x647c084d9bb5109f96c1b926328caa1514d1c209` | `0x408ce42ac7538e5a6f53324585075470d1b3c5b3` | 1.7001e-09 wstETH | `0x7df7bec770a2e878a0c0bbc2133cd321a92619a833b3c478321555d648d66ffb` |
| base | 2026-02-27T21:53:57 | `0x408ce42ac7538e5a6f53324585075470d1b3c5b3` | `0xf567c7b384c77c9c4a77e8a0a5f52ae37e8b74df` | 0.14999257 ETH | `0xe9788b01e28f186f006f496101323e650d75c0a0a117d21a4b5d2e7dc59a1298` |

### 2.2 The 2024-12-17 ChangeNOW payout to `0x3eaef6d5` is its own ETH moved from Base

`investigations/ballon-dor-flow-trace/sources/data/walk_edges.csv` (row 49) records 0.0076965 ETH from the ChangeNOW wallet
`0xeba88149…` to `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` (a former funder of the brace227 key) on 2024-12-17 02:14:47 UTC
as funding. On Base, the same address received three payouts from the ChangeNOW hot wallet
`0x1b1d2149d656f8ca33fb633e6f642b5a2426b53d` (01:45:43, 01:54:17, 01:59:45), sent 0.008 ETH at 02:10:49 to the single-use
address `0x4450ff76f8bea943aca0e61208be7328da6f1d8f`, which forwarded 0.00798298 ETH to that ChangeNOW wallet at 02:14:11,
36 seconds before the Ethereum payout (`data/ballon_changenow_roundtrip.csv`):

| Chain | UTC | From | To | Amount | Transaction |
|---|---|---|---|---|---|
| base | 2024-12-17T01:45:43 | `0x1b1d2149d656f8ca33fb633e6f642b5a2426b53d` | `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | 0.0027463 ETH | `0xc52d83c13c7c39cfbadb014f76d0d1b9fae3776b852438041b9ae99488e8650b` |
| base | 2024-12-17T01:54:17 | `0x1b1d2149d656f8ca33fb633e6f642b5a2426b53d` | `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | 0.00274595 ETH | `0xb4197dab4efc3472fcf4014518660b8d3a92500bbdfba95687f30cf604b1356c` |
| base | 2024-12-17T01:59:45 | `0x1b1d2149d656f8ca33fb633e6f642b5a2426b53d` | `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | 0.00274903 ETH | `0x0b3e4d32b4ff930cc949b30d9f39045d492bf52798081adc968f30bbc844cc46` |
| base | 2024-12-17T02:10:49 | `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | `0x4450ff76f8bea943aca0e61208be7328da6f1d8f` | 0.008 ETH | `0x92d8fce2c7835a2eb13f936419520874a1b2bfed6ddd93360ba9e7ca01bed9af` |
| base | 2024-12-17T02:14:11 | `0x4450ff76f8bea943aca0e61208be7328da6f1d8f` | `0x1b1d2149d656f8ca33fb633e6f642b5a2426b53d` | 0.00798298 ETH | `0xee338bdbba66bad7c6e36b75a5841e1294b418396c400b11bb4395bfda95b28b` |
| ethereum | 2024-12-17T02:14:47 | `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | 0.0076965 ETH | `0x33b619fee777c198b71afda8822c149a3f0f5d5550be1466a2252119f690ca47` |

The Ethereum "funding" is the output of an order paid by `0x3eaef6d5` itself
(SUPPORTED: the ChangeNOW order is not public; the hot-wallet tag is single-source).

### 2.3 Unresolved observation: gas advance on the WenZhuanBuPei key (Arbitrum)

On 2026-10-27 `0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50` (the "1% service") sends 0.00001 ETH to
`0xe820ecb3c6f48a420a5538046cab73d2f40987cd` two seconds before that key transfers 27,724.00 USDC to it, and receives 0.000008 ETH
back in the same second. Two readings (service-managed deposit address, or user wallet driven by an app); the round amount
leaves 0.79 USDC behind. Not decided.

## 3. Limits

- Labels (FixedFloat, ChangeNOW hot wallet, Relay depository) come from Blockscout alone.
- Profile creation times come from Polymarket's public profile API, not from the on-chain Safe deployment.
- The sample of other Machado buyers is incomplete (data-api pagination); no calibrated base rate.
- BSC histories remain unread.
- Identity, a single operator and inside information are not established.

## 4. Reproduction

The collectors in `tools/` run from the original workspace (`scripts/` folder, Python 3.12 standard library plus the archive
helper `onchain.py`): `pm_nobel_c7.py`, `pm_nobel_financeur.py`, `pm_nobel_comptes.py` (Relay: about one call per minute),
`pm_nobel_amont_aval.py`, `pm_ballon_l2.py`. Every transaction listed above can be checked on a public explorer.
