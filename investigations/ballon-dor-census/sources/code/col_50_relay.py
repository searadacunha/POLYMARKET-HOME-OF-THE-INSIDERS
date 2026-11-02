"""Relay's own record of each deposit and withdrawal of the 13 wallets. Route requests/v2 is to be retired on 24/11/2026: raw answers are archived.
A record says what Relay says: origin and destination chain, user, recipient. It is checked afterwards against the chain, in ana_30_flows.py."""
import glob
import json
import net

OUT = net.ROOT / 'derived/relay.json'


def main():
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for f in sorted(glob.glob(str(net.ROOT / 'derived/chain/*.json'))):
        c = json.load(open(f))
        for tx, fl in c['flows'].items():
            if tx in out:
                continue
            d = net.get('https://api.relay.link/requests/v2', dict(hash=tx))
            out[tx] = dict(wallet=c['wallet'], type=fl['type'], usdc=fl['usdc'], ts=fl['ts'], requests=d.get('requests') or [])
            OUT.write_text(json.dumps(out))
            print(c['wallet'][:10], fl['type'], fl['usdc'], tx[:12], 'relay_requests', len(out[tx]['requests']), flush=True)


if __name__ == '__main__':
    main()
