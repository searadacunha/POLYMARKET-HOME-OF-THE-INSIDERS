"""Which Polymarket wallet a key could own, in all four known forms. A derived address only counts if the wallet also has activity.

Two deposit-wallet shapes (legacy, and the beacon form since the upgrade of 2026-06-29), the Magic/email proxy clone, and the Safe,
whose address is asked from the official factory. Earlier searches tested deposit wallets only. Constants are copied by script from
tools/proxy_check.py and fund_flow/wallets.py, and self_check() recomputes known wallets before anything is believed.
"""
from .keccak import create2, keccak256, selector, word
from .net import Refused

DEPOSIT_FACTORY = '0x00000000000fb5c9adea0298d729a0cb3823cc07'
PROXY_FACTORY = '0xab45c5a4b0c941a2f231c04c3f49182e1a254052'
SAFE_FACTORY = '0xaacfeea03eb1561c4e67d661e40682bd20e3541b'
_LEGACY = bytes.fromhex('61007d3d8160233d397358ca52ebe0dadfdf531cde7062e76746de4db1eb60095155f3363d3d373d3d363d7f360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc545af43d6000803e6038573d6000fd5b3d6000f300000000000000000000000000000000000fb5c9adea0298d729a0cb3823cc07')
_BEACON = bytes.fromhex('6100923d8160233d39737a18edfe055488a3128f01f563e5b479d92ffc3a60195155f3363d3d373d3d363d602036600436635c60da1b60e01b36527fa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50545afa5036515af43d6000803e604d573d6000fd5b3d6000f300000000000000000000000000000000000fb5c9adea0298d729a0cb3823cc07')
_PROXY_HEAD = bytes.fromhex('3d3d606380380380913d393d73')
_PROXY_MIDDLE = bytes.fromhex('5af4602a57600080fd5b602d8060366000396000f3363d3d373d3d3d363d73')
_PROXY_TAIL = bytes.fromhex('5af43d82803e903d91602b57fd5bf3')
_PROXY_ARGS = bytes.fromhex('52e831dd') + (32).to_bytes(32, 'big') + bytes(32)


def deposit_wallet(owner, shape='beacon'):
    pad = word(owner)
    template = _BEACON if shape == 'beacon' else _LEGACY
    return create2(DEPOSIT_FACTORY, keccak256(word(DEPOSIT_FACTORY) + pad), keccak256(template + pad))


def magic_proxy(net, owner):
    """The clone's implementation is read from the factory once, then the address is local."""
    value, _ = net.rpc('eth_call', [dict(to=PROXY_FACTORY, data=selector('getImplementation()')), 'latest'], 137)
    implementation = '0x' + value[-40:].lower()
    init = _PROXY_HEAD + bytes.fromhex(PROXY_FACTORY[2:]) + _PROXY_MIDDLE + bytes.fromhex(implementation[2:]) + _PROXY_TAIL + _PROXY_ARGS
    return create2(PROXY_FACTORY, keccak256(bytes.fromhex(owner[2:])), keccak256(init))


def safe_wallet(net, owner):
    value, _ = net.rpc('eth_call', [dict(to=SAFE_FACTORY, data=selector('computeProxyAddress(address)') + owner[2:].rjust(64, '0')), 'latest'], 137)
    return '0x' + value[-40:].lower() if value and len(value) >= 42 else None


def all_forms(net, owner):
    forms = dict(deposit_beacon=deposit_wallet(owner), deposit_legacy=deposit_wallet(owner, 'legacy'))
    try:
        forms['magic_proxy'] = magic_proxy(net, owner)
        forms['safe'] = safe_wallet(net, owner)
    except Refused as exc:
        forms['error'] = str(exc)[:120]
    return forms


def self_check():
    assert deposit_wallet('0x08d409aae84f9b7b6a798c97c457a0f41e856c7b', 'legacy') == '0x5008c44a36c52f03de75d7aa98c15c14397e2302'
    assert deposit_wallet('0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d') == '0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5'
    assert deposit_wallet('0xc852b0938f5ad79b640d105ed11c14499454af26') == '0x873848cd27784900e193611845fc3fd2c4716d03'
