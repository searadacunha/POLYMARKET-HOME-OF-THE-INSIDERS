"""Which of the four Polymarket wallet types an address is, read from bytecode and official contracts.

Submitting a transaction says nothing about who owns the wallet: it may be a relayer, a bundler or the
owner. A legacy proxy stores no user, so its signer is known only if a candidate address derives to it,
and otherwise stays SIGNER_UNKNOWN. A proven signer is a key, not a person.
"""
from .keccak import create2, keccak256, selector, word

EOA, SAFE, PROXY, DEPOSIT, OTHER = 'EOA', 'GNOSIS_SAFE', 'POLYMARKET_PROXY', 'DEPOSIT_WALLET', 'OTHER_CONTRACT'
SIGNER_UNKNOWN, SIGNER_DERIVED, OWNERS_ONCHAIN, KEY_HOLDER = 'SIGNER_UNKNOWN', 'SIGNER_DERIVED_FROM_CANDIDATE', 'OWNERS_READ_ONCHAIN', 'ADDRESS_IS_ITS_OWN_KEY'
SAFE_FACTORY = '0xaacfeea03eb1561c4e67d661e40682bd20e3541b'
PROXY_FACTORY = '0xab45c5a4b0c941a2f231c04c3f49182e1a254052'
DEPOSIT_FACTORY = '0x00000000000fb5c9adea0298d729a0cb3823cc07'
DEPOSIT_BEACON = '0x7a18edfe055488a3128f01f563e5b479d92ffc3a'
LEGACY_EXCHANGE = '0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e'
CLONE_PREFIX = '363d3d373d3d3d363d73'
ERC1967_PREFIX = '363d3d373d3d363d7f360894a1'
BEACON_PREFIX = '363d3d373d3d363d602036600436635c60da1b'
SAFE_PROXY_PREFIX = '608060405260008054' 
EIP7702_PREFIX = 'ef0100'
# Layout of the official factory's clone, from its published library; the bytes are checked on-chain by derivation.
_PROXY_HEAD = bytes.fromhex('3d3d606380380380913d393d73')
_PROXY_MIDDLE = bytes.fromhex('5af4602a57600080fd5b602d8060366000396000f3363d3d373d3d3d363d73')
_PROXY_TAIL = bytes.fromhex('5af43d82803e903d91602b57fd5bf3')
_PROXY_ARGS = bytes.fromhex('52e831dd') + (32).to_bytes(32, 'big') + bytes(32)
_DEPOSIT_HEAD = bytes.fromhex('61007d3d8160233d3973')
_DEPOSIT_MIDDLE = bytes.fromhex('60095155f3363d3d373d3d363d7f360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc545af43d6000803e6038573d6000fd5b3d6000f3')


def proxy_address(owner, implementation, factory=PROXY_FACTORY):
    init = _PROXY_HEAD + bytes.fromhex(factory[2:]) + _PROXY_MIDDLE + bytes.fromhex(implementation[2:]) + _PROXY_TAIL + _PROXY_ARGS
    return create2(factory, keccak256(bytes.fromhex(owner[2:])), keccak256(init))


def deposit_wallet_address(owner, implementation, factory=DEPOSIT_FACTORY):
    init = _DEPOSIT_HEAD + bytes.fromhex(implementation[2:]) + _DEPOSIT_MIDDLE + word(factory) + word(owner)
    return create2(factory, keccak256(word(factory) + word(owner)), keccak256(init))


def _address_of(result):
    return '0x' + result[-40:].lower() if result and result != '0x' and len(result) >= 42 else None


def _read(client, to, signature, argument=None):
    data = selector(signature) + (word(argument).hex() if argument else '')
    try:
        return client.call(to, data)
    except Exception:
        return None


def _addresses(result):
    if not result or len(result) < 2 + 64 * 2:
        return []
    raw = result[2:]
    count = int(raw[64:128], 16)
    if count > 64 or len(raw) < 128 + 64 * count:
        return []
    return ['0x' + raw[128 + i * 64 + 24:128 + (i + 1) * 64].lower() for i in range(count)]


def classify_wallet(client, address):
    address = address.lower()
    code = client.rpc('eth_getCode', [address, 'latest'])[2:].lower()
    out = dict(address=address, chain_id=137, type=OTHER, signer_status=SIGNER_UNKNOWN, owners=[], threshold=None, evidence=[])
    if not code or code.startswith(EIP7702_PREFIX):
        out.update(type=EOA, signer_status=KEY_HOLDER, owners=[address], evidence=['No contract code at this address.' if not code else 'EIP-7702 delegation to 0x' + code[6:46] + '.'],
                   limit='An EOA may also be a smart wallet not deployed yet. The key holder is not known.')
        return out
    if code.startswith(CLONE_PREFIX):
        implementation = '0x' + code[len(CLONE_PREFIX):len(CLONE_PREFIX) + 40]
        official = _address_of(_read(client, PROXY_FACTORY, 'getImplementation()'))
        out['evidence'].append(f'Clone of {implementation}; official proxy factory implementation {official}.')
        if implementation == official:
            out.update(type=PROXY, implementation=implementation)
        return out
    if code.startswith(ERC1967_PREFIX) or code.startswith(BEACON_PREFIX):
        owner = _address_of(_read(client, address, 'owner()'))
        official = DEPOSIT_FACTORY[2:] in code or DEPOSIT_BEACON[2:] in code
        out['evidence'].append(f"ERC-1967 {'beacon ' if code.startswith(BEACON_PREFIX) else ''}proxy; official factory or beacon in its code: {official}; owner() = {owner}.")
        if owner and official:
            out.update(type=DEPOSIT, owners=[owner], signer_status=OWNERS_ONCHAIN, limit='Owner read on-chain. Session signers authorized by that owner are not listed here.')
        return out
    owners = _addresses(_read(client, address, 'getOwners()'))
    if owners:
        threshold = _read(client, address, 'getThreshold()')
        predicted = {o: _address_of(_read(client, SAFE_FACTORY, 'computeProxyAddress(address)', o)) for o in owners}
        out.update(type=SAFE, owners=owners, threshold=int(threshold, 16) if threshold else None, signer_status=OWNERS_ONCHAIN, polymarket_factory=address in predicted.values())
        out['evidence'].append(f"getOwners() read on-chain; official Safe factory predicts this address from an owner: {address in predicted.values()}.")
    return out


def relayed_signer_candidates(transaction):
    """Every address-shaped word in calldata, plus the sender. Candidates only: derivation decides, never position."""
    raw = (transaction.get('input') or '0x')[2:]
    found = {transaction.get('from', '').lower()}
    for start in range(8, len(raw), 64):
        chunk = raw[start:start + 64]
        if len(chunk) == 64 and chunk.startswith('0' * 24) and not chunk.startswith('0' * 34):
            found.add('0x' + chunk[24:])
    found.discard('')
    return sorted(found)


def resolve_proxy_signer(client, wallet, transactions):
    """Tests each candidate with the factory's formula, then with an official contract's own view."""
    wallet = wallet['address'] if isinstance(wallet, dict) else wallet
    implementation = _address_of(_read(client, PROXY_FACTORY, 'getImplementation()'))
    submitters, tested = set(), set()
    for transaction in transactions:
        submitters.add(transaction.get('from', '').lower())
        for candidate in relayed_signer_candidates(transaction):
            if candidate in tested:
                continue
            tested.add(candidate)
            if proxy_address(candidate, implementation) == wallet:
                view = _address_of(_read(client, LEGACY_EXCHANGE, 'getPolyProxyWalletAddress(address)', candidate))
                return dict(signer=candidate, signer_status=SIGNER_DERIVED, local_derivation=True, official_view_agrees=view == wallet, signer_also_submitted=candidate in submitters, candidates_tested=len(tested))
    return dict(signer=None, signer_status=SIGNER_UNKNOWN, candidates_tested=len(tested), submitters=sorted(submitters), note='No candidate derives to this wallet. Submitting its transactions does not make an address its owner.')
