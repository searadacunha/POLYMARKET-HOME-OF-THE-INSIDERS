import json, base64, hashlib
from pathlib import Path
from github_inventory import get, ROOT
SELECTION={
'darrnhard/polymarket-smart-money':['docs/02_analysis.md','docs/EXECUTIVE_SUMMARY.md'],
'sturzael/polymarket-edge-research':['experiments/e23_stratification/SYNTHESIS.md'],
'vsbtc/polymarket-insider-detection':['src/score.py','src/detect_jumps.py','src/validate.py'],
'junegun/polymarket-strategy-lab':['backend/volume_spike_backtest.py','backend/vol_calibration_backtest.py','research/FINDINGS.md'],
'outcometick/polymarket-backtest':['outcometick/backtest/_sandbox/otengine.py','outcometick/backtest/generic.py','docs/verification.md'],
'SII-WANGZJ/Polymarket_data':['polymarket/processors/decoder.py','polymarket/processors/trades.py','data/README.md'],
'G0BLINDEV/polymarket-backtester-realistic':['_backtest_engine.py'],
'Fierdimo/polymarket-analysis':['simulation/cost_model.py','scripts/test_trade_signal.py'],
'tlafargue/polymarket-research':['reproduce/verify_stats.py','reproduce/wallet_skill.py','data/wallet_skill_splithalf.parquet','data/calibration_trades_1hour_10b.parquet','data/calibration_trades_6hours_10b.parquet','data/calibration_trades_24hours_10b.parquet','LICENSE-CODE','LICENSE-DOCS']}
if __name__=='__main__':
    rows=[]
    for repo,paths in SELECTION.items():
        folder=ROOT/'data/github'/repo.replace('/','__'); tree=json.loads((folder/'tree.json').read_text())['tree']
        for path in paths:
            x=next(x for x in tree if x['path']==path)
            assert x['size']<500000
            b=base64.b64decode(json.loads(get('repos/'+repo+'/git/blobs/'+x['sha']))['content'])
            dest=folder/'files'/path; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(b)
            rows.append({'repo':repo,'path':path,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
    (ROOT/'data/github/followup.json').write_text(json.dumps(rows,indent=2)); print(len(rows),'files')
