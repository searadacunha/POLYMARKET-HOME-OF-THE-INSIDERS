"""The addresses read, in two tiers kept apart everywhere. Reasons are in reports/COVERAGE_AND_FALSE_POSITIVES.md and PLAN.md."""
HOT3 = '0xdd3d72c53ff982ff59853da71158bf1538b3ceee'
HOT4 = '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1'
DEP = '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b'
CN13 = '0x3525d3a883f743ca146288c146de7ccd59d48bf5'
ARB = '0xd5b73fc035d4d679234323e0d891cab4a4f5a1ab'
HUB = '0x64cdaa89629fe003eaa31b480d8b63372d109a53'
GAS = '0x300773969b499b9768267e0c5a049f7751de79e7'
POLY = '0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423'
ETIQUETEE = {(1, HOT3), (1, HOT4), (1, DEP), (1, CN13), (42161, ARB)}
CANDIDAT = {(1, HUB), (1, GAS), (137, POLY)}
ROTATION = 1786365060  # 2026-08-10 12:31:00 UTC, minute of the first transaction of HUB and GAS, both from HOT4 (state/hubs_probe.py)
CHAIN = {1: 'ethereum', 137: 'polygon', 42161: 'arbitrum'}
NATIVE = {1: 'ETH', 137: 'POL', 42161: 'ETH'}


def tier(chain, addr):
    if (chain, addr) in ETIQUETEE:
        return 'ETIQUETEE'
    return 'CANDIDAT' if (chain, addr) in CANDIDAT else 'AUTRE'
