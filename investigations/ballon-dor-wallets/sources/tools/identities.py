"""Public labels and how each was tied to an address. An alias shown today says nothing about who holds the wallet, and no civil identity is recorded."""
S_A = 'S_A sealed comparison, studies/pipeline_replay_20261101/derived/interim_R3_S_A_20261101.json.gz, mapping exact_current_profile_alias'
SHOT = 'Row of the Upside screenshot reproduced from the public tape: 15 rows of 15 in the same order, gap under 0.5 share, evidence/screenshot_reconstruction.json'
IDS = {
    'thin': dict(label='Thin-Disclaimer-Life', address='0x8d3319c51520518ad01f6744486ceea29f376f5b', basis=[S_A, SHOT], group='highlighted', level='ALIAS_EXACT_AND_SHARES'),
    'vidente': dict(label='VidenteRibeira', address='0x5f8b30fde56bd2d2f3853769602330aeb9f1866a', basis=[S_A, SHOT], group='highlighted', level='ALIAS_EXACT_AND_SHARES'),
    'cookedrice': dict(label='cookedrice', address='0x4060509c8c70cece529be4a089d6d66ad865b4d0', basis=['Name on the public tape of market 1105364', SHOT], group='highlighted', level='ALIAS_EXACT_AND_SHARES'),
    'wen': dict(label='WenZhuanBuPei', address='0x8832319d9c25df311e37511f0aa5b214abc16500', basis=[S_A, SHOT], group='highlighted', level='ALIAS_EXACT_AND_SHARES'),
    '0x86544e4dfde': dict(label='0x86544e4dfde', address='0x3ed2c452f141c291adecb97ddfc72b1650acff3d', basis=[SHOT, 'Name shown today differs: 0z8hlf..mmhofrzs. The label is not the address prefix, nor the owner prefix.'], group='highlighted', level='SHARES_ONLY'),
    'brace227': dict(label='brace227', address='0x873848cd27784900e193611845fc3fd2c4716d03', basis=[S_A, SHOT], group='highlighted', level='ALIAS_EXACT_AND_SHARES'),
    'walletwallet8424': dict(label='walletwallet8424', address='0x1a1ef4c65583d5c71011d7fe51e9f544e2b1cc40', basis=[S_A, SHOT], group='highlighted', level='ALIAS_EXACT_AND_SHARES'),
    'zoomman17': dict(label='Zoomman17', address='0x92a8eec13a691af81a1a196b7594c1eccfa0eebc', basis=[SHOT, 'Name shown today differs: Atlfalcons7.'], group='highlighted', level='SHARES_ONLY'),
    'kraben006': dict(label='kraben006', address='0x84212ee459d1edaf35983bbec342b0806282d8ec', basis=[SHOT, 'Name shown today differs: Edgarblade.'], group='highlighted', level='SHARES_ONLY'),
    'ouldlm3alem': dict(label='OuldLm3alem', address='0x71ae923f12eb947c58365287691cf5a10bc3e5bf', basis=[S_A, 'Also on the same tape under this name.'], group='later_named', level='ALIAS_EXACT'),
    '0xdd97e6': dict(label='0xdd97e6', address='0xdd97e6ad12ca4dd18a88804fb5ed7ed429849464', basis=['Press gives the prefix only. Official profile search returns this one address, whose default name starts with the prefix and dates the profile to 20 Oct 2026 08:57:48 UTC. It is also the only corpus wallet with that prefix.'], group='later_named', level='PREFIX_UNIQUE'),
}
NOT_HIGHLIGHTED = {'cypyo': '0xa9f4dc80fd27e2977ef1fcaea41d263ecd7a4dfb', 'briardxo': '0x226aca3e129cf187431ce84a7ba83b0575ee22fd', 'cypya': '0x970998da056e60c707d9b1fc55cfdf3d68c252ab', 'pup1': '0x54b56146656e7eef9da02b3a030c18e06e924b31', 'mr.ozi': '0x614dc8d3542c12103d2c6a3553fd761e391d1546', 'enginesinmyfactory': '0xb4847ababacf932bfee54fca9f455d80f9153bc3'}
