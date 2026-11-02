"""join_date, markets traded and PnL rollup for each wallet of the population. Runs after the fact, but join_date never changes, so it is what a detector could read at the time."""
import json
import net


def main():
    pop = json.load(open(net.ROOT / 'derived/population.json'))['population']
    path = net.ROOT / 'derived/population_stats.json'
    out = json.loads(path.read_text()) if path.exists() else {}
    for i, w in enumerate(sorted(pop)):
        if w in out:
            continue
        d = net.get('https://data-api.polymarket.com/v2/user-stats', dict(user=w))
        s = d.get('data') or {}
        pnl = s.get('all_time_pnl') or {}
        out[w] = dict(join_date=s.get('join_date'), markets=s.get('trades'), economic_pnl=pnl.get('economic_pnl'), name_known=d.get('data') is not None)
        if i % 200 == 0:
            path.write_text(json.dumps(out))
            print(i, len(out), flush=True)
    path.write_text(json.dumps(out))
    print('done', len(out), 'no join_date', sum(1 for v in out.values() if not v['join_date']))


if __name__ == '__main__':
    main()
