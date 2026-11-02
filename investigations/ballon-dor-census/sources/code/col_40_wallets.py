"""On-chain record of each Polymarket wallet: owner() read, CREATE2 check, ERC-20 / ERC-1155 / native history on Polygon,
and the receipt of each deposit and withdrawal named by the API. Output: derived/chain/<wallet>.json. Independent of the Data API for the cash totals."""
import json
import glob
import addr
import net

CHAIN = net.ROOT / 'derived/chain'
OWNER = '0x8da5cb5b'


def owner_of(wallet):
    code = net.rpc('eth_getCode', [wallet, 'latest'])
    if code in ('0x', None):
        return dict(wallet=wallet, deployed=False)
    out = net.rpc('eth_call', [dict(to=wallet, data=OWNER), 'latest'])
    own = '0x' + out[-40:] if out and len(out) >= 42 else None
    return dict(wallet=wallet, deployed=True, code_bytes=len(code) // 2 - 1, owner=own,
                create2_beacon=addr.deposit_wallet(own) == wallet if own else None, create2_old=addr.deposit_wallet(own, addr.TEMPLATE_OLD) == wallet if own else None)


def main():
    CHAIN.mkdir(exist_ok=True)
    for f in sorted(glob.glob(str(net.ROOT / 'derived/accounts/*.json'))):
        a = json.load(open(f))
        w = a['address']
        out = owner_of(w)
        out['erc20'] = net.es_all(137, 'tokentx', w)
        out['erc1155'] = net.es_all(137, 'token1155tx', w)
        out['native'] = net.es_all(137, 'txlist', w)
        out['internal'] = net.es_all(137, 'txlistinternal', w)
        txs = {}
        for r in a['activity']:
            if r['type'] in ('DEPOSIT', 'WITHDRAWAL'):
                tx = r['transaction_hash']
                txs[tx] = dict(type=r['type'], usdc=r['usdc_size'], ts=r['timestamp'], receipt=net.rpc('eth_getTransactionReceipt', [tx]), tx=net.rpc('eth_getTransactionByHash', [tx]))
        out['flows'] = txs
        (CHAIN / f'{w}.json').write_text(json.dumps(out))
        print(w, a['labels'][:2], 'owner', out.get('owner'), 'beacon', out.get('create2_beacon'), 'old', out.get('create2_old'), 'erc20', len(out['erc20']), 'erc1155', len(out['erc1155']), 'native', len(out['native']), 'internal', len(out['internal']), 'flows', len(txs), flush=True)


if __name__ == '__main__':
    main()
