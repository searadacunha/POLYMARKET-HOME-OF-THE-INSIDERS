import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))
import addr, seed

assert addr.keccak(b'').hex() == 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
assert addr.eip55_status('0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed') == 'valid'
assert addr.eip55_status('0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAeD') == 'invalid'
assert addr.eip55_status('0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed') == 'no_checksum'
assert addr.bech32_valid('bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4')
assert not addr.bech32_valid('bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5')
assert addr.base58_32('11111111111111111111111111111111')
assert addr.base58_32('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
assert not addr.base58_32('EPjFWdd5AufqSSqeM')
assert addr.deposit_wallet('0x08d409aae84f9b7b6a798c97c457a0f41e856c7b', addr.TEMPLATE_OLD) == '0x5008c44a36c52f03de75d7aa98c15c14397e2302'
print('addr ok')
for n, a in seed.IRBOZ.items():
    for x in a.get('evm', []):
        print(n, x, addr.eip55_status(x))
    for x in a.get('btc', []):
        print(n, x, 'bech32', addr.bech32_valid(x))
    for x in a.get('sol', []):
        print(n, x, 'base58_32', addr.base58_32(x))
