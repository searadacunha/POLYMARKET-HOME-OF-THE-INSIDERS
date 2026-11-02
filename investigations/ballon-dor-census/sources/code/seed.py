"""Addresses as published, each with its source. Nothing here is a finding: these are leads to test."""

# Full text of the note tweet (raw/x_post/irboz_fxtwitter.json) and first image (raw/x_post/irboz_img1_*.jpg).
IRBOZ = {
    1: dict(profile='0xdd97e6ad12ca4dd18a88804fb5ed7ed429849464', created='20/10', pnl=19000, deposited=44000, withdrawn=63000,
            evm=['0x22ceC127f5E203578d2b8b7E6EddF182a2342E76', '0xca8B1f1a56A0Fe8947D325BAAFA286F5bD4D6165'], sol=['4MMHYz6K6zrXpSGsSDAsx235ZQ3kbnM4hzKK2FeWzgE1']),
    2: dict(profile='0x84212ee459d1edaf35983bbec342b0806282d8ec', created='1/10', pnl=10000, deposited=5500, withdrawn=15100, evm=['0x101B5f4Dc0886c32E2b75972101AeAF9F338fb65']),
    3: dict(profile='0x3ed2c452f141c291adecb97ddfc72b1650acff3d', created='09/10', pnl=29353, deposited=42400, withdrawn=74200, evm=['0x69837228fa0bcBaC53713D981161C929523c0DED']),
    4: dict(profile='0x71ae923f12eb947c58365287691cf5a10bc3e5bf', created='22/10', pnl=21663, deposited=39383, withdrawn=73200, evm=['0xB3aFcdc711378d17CA1a1000770af5A0b78BB0BA', '0x1B500B6c40a2Ff0930e540e8F53C559a32E75f2c']),
    5: dict(profile='0xe966177219a0655b7aec3140a52b5e883007fa3e', created='25/10', pnl=35000, deposited=73668, withdrawn=109150, evm=['0xc15cbd1e89d4252581a0a31ff88f64a29addf1cb'], name='Denver28',
            btc=['bc1qqd68vnxek6vfnq3ztlsj3x80vvd9z56g334zvm', 'bc1q8gr53e7laqedpll6dh8kgsc2n7sezxznk0ry3v', 'bc1qqlh9r40agtf3a04nrc28xahngt5wfnyq7wue8d',
                 'bc1q5fqc7fx2gu82fr3y3ucfv9wlca3qfv05zxee0r', 'bc1qphd7y77f6egqqqhy4lh7ff3nezjatrdlh74j02', 'bc1q5w4kq7pj5adl53fweqakt6n5a2syaha4xdgjhs',
                 'bc1qdh7ffa0k3xa29akdl45ld2h0u990lng3ykqnkn', 'bc1q98jgll5y4l87u2yw82l6ns73ku7yanyn2lq4jt']),
    6: dict(profile='0xb01f9ad38962efb6c795ac36bc759b2a28a955e3', created='20/10', pnl=5500, deposited=9780, withdrawn=15106,
            evm=['0xe5bac95f7b398c499d9290e30d2c87006db9adf0', '0x20a18b70eab5b096fb06920693444a04ea3b5ade', '0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50']),
}

# Upside prints names and share counts, not addresses. Wallets below come from an earlier local inventory, so they are
# hypotheses until ana_10_upside_match.py reproduces the printed share counts from this module's own tape.
UPSIDE_PRINTED = {  # first image of the 23/10 post, https://x.com/UpsideMediaoff/status/2113651111051596165
    'Thin-Disclaimer-Life': '0x8d3319c51520518ad01f6744486ceea29f376f5b', 'VidenteRibeira': '0x5f8b30fde56bd2d2f3853769602330aeb9f1866a',
    'cookedrice': '0x4060509c8c70cece529be4a089d6d66ad865b4d0', 'WenZhuanBuPei': '0x8832319d9c25df311e37511f0aa5b214abc16500',
    '0x86544e4dfde': '0x3ed2c452f141c291adecb97ddfc72b1650acff3d', 'brace227': '0x873848cd27784900e193611845fc3fd2c4716d03',
    'walletwallet8424': '0x1a1ef4c65583d5c71011d7fe51e9f544e2b1cc40', 'Zoomman17': '0x92a8eec13a691af81a1a196b7594c1eccfa0eebc',
    'kraben006': '0x84212ee459d1edaf35983bbec342b0806282d8ec',
}
UPSIDE_LATER = {  # follow-up of 27/10, names only
    'OuldLm3alem': '0x71ae923f12eb947c58365287691cf5a10bc3e5bf', '0xdd97e6': '0xdd97e6ad12ca4dd18a88804fb5ed7ed429849464',
}

BALLON_EVENTS = {  # public-search of 02/11, re-listed by col_10_markets.py
    48361: 'winner', 811116: 'top5', 811117: 'top3', 1105364: 'mbappe_v_yamal', 1218178: '2nd', 1218179: '3rd', 1225367: '4th', 1225368: '5th', 1105369: 'rodri_v_messi',
    1105379: 'kane_v_yamal', 1226675: 'mbappe_v_messi', 1226676: 'yamal_v_messi', 1105380: 'dembele_v_kvara', 1105381: 'haaland_v_bellingham', 1200407: 'attendance',
}
CEREMONY_UTC = '2026-10-26T20:00:00Z'  # UEFA page dated 19/10, to re-read in col_10
VOTE_CLOSED_UTC = '2026-09-28'  # press, France Football deadline, not verified on a primary source yet
