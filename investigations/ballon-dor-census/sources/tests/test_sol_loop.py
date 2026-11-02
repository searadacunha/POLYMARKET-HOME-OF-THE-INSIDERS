"""The token account of a transaction read last must still be read, even when the last signature is failed or already seen."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))
import hist, net
A = 'OWNER'
def fake_sig(address, max_pages=20):
    return ([dict(signature='s2')], True) if address == 'TA' else ([], True)
net.sol = lambda method, params, cache=True: [dict(signature='s1'), dict(signature='bad', err='x')]
hist.sol_signatures = fake_sig
hist.sol_tx = lambda s: dict(slot=1, blockTime=2, meta=dict(preTokenBalances=[], postTokenBalances=[dict(accountIndex=1, owner=A, mint='EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', uiTokenAmount=dict(amount='5', decimals=6))], preBalances=[0, 0], postBalances=[0, 0]), transaction=dict(message=dict(accountKeys=['X', 'TA'], instructions=[])))
rows, info = hist.sol_rows(A)
assert info['n_signatures'] == 2, info
assert info['token_accounts'] == ['TA'], info
print('sol loop ok', info['n_signatures'])
