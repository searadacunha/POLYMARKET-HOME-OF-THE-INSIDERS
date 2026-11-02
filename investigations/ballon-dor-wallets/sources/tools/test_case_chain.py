"""The withdrawal rule on the shape of a real receipt: burn, unwrap, then the wallet's own transfer. The zero address must never be the destination."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import case_chain as C
W, Z, R = '0x' + 'a' * 40, '0x' + '0' * 40, '0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f'
moves = [dict(log_index=1, token=C.PUSD, source=W, target=C.PUSD, raw=100), dict(log_index=2, token=C.USDCE, source='0xc417', target=W, raw=100), dict(log_index=3, token=C.PUSD, source=C.PUSD, target=Z, raw=100), dict(log_index=4, token=C.USDCE, source=W, target=R, raw=100)]
C.receipt_transfers = lambda tx, chain=137: (dict(logs=[]), moves)
C.relay_record = lambda tx: None
case = C.Case('t')
hop = C.trace_exit(case, W, dict(tx='0x1', at=1, usd=.0001))
assert hop['first_destination'] == R, hop
assert not any(r['target'] == Z for r in case.relations), case.relations
assert case.relations[0]['category'] == 'SERVICE_INTERACTION'
# A swap inside the deposit transaction: Relay names no separate payout hash, and that must not raise.
C.relay_record = lambda tx: dict(id='i', status='success', user=W, recipient='0xr', in_txs=[(137, tx)], out_txs=[(137, None)], in_symbol='USDC.e', in_address=None, in_amount='1', in_raw='1', in_chain=137, out_symbol='POL', out_amount='9', out_chain=137)
C.net.rpc = lambda method, params, chain=137, pause=.15: hex(10**18) if method == 'eth_getBalance' else None
case = C.Case('t')
hop = C.trace_exit(case, W, dict(tx='0x2', at=1, usd=.0001))
assert hop['same_transaction_swap'] and hop['recipient'] == '0xr' and hop['recipient_native_balance_now'] == 1
assert case.relations[0]['category'] == 'SERVICE_INTERACTION' and case.relations[0]['tx'] == '0x2'
print('ok')
