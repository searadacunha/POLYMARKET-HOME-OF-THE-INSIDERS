"""The four funded bets named in the mission, and the contracts they touch. Facts below are inputs; every one is re-checked on chain."""

CTF = "0x4d97dcd97ec945f40cf65f87097ace5ea0476045"      # Gnosis Conditional Tokens on Polygon (emitter of the position transfers)
USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"     # native USDC, 6 decimals
USDC_E = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"   # bridged USDC.e, 6 decimals
PUSD = "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"     # Polymarket collateral since 2026, 6 decimals
F2020 = "0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423"    # the commingled route of PR 110

# The mission text gives wallet 4 as 0xadd9ab62b2c22151c661b99821cbbafb9cc9361: 39 hex digits, not an address. Its first 29
# characters match 0xadd9ab62...8df9 and its last 10 match 0xe129d1e0...cc9361. Funding amount, time, block and bet tx all
# belong to 0xadd9ab62...8df9 in PR 110's wallet_funding.csv and on chain, so that is the wallet studied.
FOCUS = [
    dict(id="W1", wallet="0x9fed84d86211d077277426db9831d74756531d1b", kind="btc5m", window_start=1792941000,
         cid="0x90c2141b69cd6f19ca7151323b870a2c8a67ac2f459bd9311d4fc8a4d8459526",
         funding_tx="0xf33adda7050db46a8db7cdb65e6ba5567a6db36d5723a1583fc418421875b884", funding_log=178, funding_ts=1792940826,
         bet_tx="0x3fa0acff0fc531091701c3fbea371c125b770e4c3a534dc9555f5addb4130aac"),
    dict(id="W2", wallet="0xd74d2d3a4016079ff49743f831d1a31b668cccf3", kind="btc5m", window_start=1790904300,
         cid="0x21c38ba0761e1510ce74a7ad26c873cd3c742dd8f3bb1f2eee398c0176f2cd16",
         funding_tx="0xeb056655d1c4248f685bdc61e063f27f9c7fa415fcb1cb01c92f76eb897bfe10", funding_log=122, funding_ts=1790903898,
         bet_tx="0x3699f4fc60ad6d5d7cc2903deba6ec448cf5684777df5dd1e56b0d1d50f8a94c"),
    dict(id="W3", wallet="0x569c5f3850c31bcb8590ef1926fb69e0f42f741d", kind="btc5m", window_start=1790243700,
         cid="0xaf10b9a2e7d992c1fd35cc11849c09d53ebaaaad092cdce899eb4a779e656449",
         funding_tx="0x5091f0f0243a6bb383c0d7e01a656fa1edfe63187d976f692dbfe028cb073f1f", funding_log=94, funding_ts=1790241972,
         bet_tx="0x56a320f48ad0ad9eafee8d76fe3b1087e7ce9501804e9a0c7110debce5163bad"),
    dict(id="W4", wallet="0xadd9ab62b2c22151c661b99821cbb7433df98df9", kind="weather", window_start=None,
         cid="0x5ef8a6de47a93de0e2c467e5f2cb426502d65afa8bde273b7eb4f2c7ea07b905",
         funding_tx="0x862e0947bd7c3e660fc76bd5705f0ffdc17c707a1a149f9705767732aaf8fb82", funding_log=162, funding_ts=1790398472,
         bet_tx="0x2c4ff87943aadc7b36c96be229a8ce0aaaf86bc7c461c7a7e6fbef4a80962639"),
]
WALLETS = [f["wallet"] for f in FOCUS]
MISSION_WALLET4 = "0xadd9ab62b2c22151c661b99821cbbafb9cc9361"
