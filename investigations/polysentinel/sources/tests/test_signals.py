"""Synthetic fixtures only: these tests do not validate insider detection."""
import copy
import unittest

from polysentinel.signals import evaluate, group_fills, bookkeeping, describe_scenarios

NOW = 1_800_000_000
A, B, C = ['0x' + c * 40 for c in 'abc']
CONFIG = {'large_nominal': 1000, 'minimum_baseline': 3, 'candidate_score': 2}


def trade(i='1', wallet=A, at=NOW-20, event='e', market='m', token='t',
          side='BUY', size=4000, price=.5, **kw):
    return dict(id=i, wallet=wallet, event_id=event, market_id=market,
                token_id=token, outcome='Named outcome', side=side, size=size,
                price=price, nominal=size*price, timestamp=at, observed_at=at+1,
                transaction_hash='0x'+str(i).zfill(64), fee=0,
                fee_unit='pUSD', **kw)


def metadata(public_at=None):
    event = dict(id='e', title='Synthetic award', active=True, closed=False,
                 observed_at=NOW-10000, tags=['awards'])
    if public_at is not None:
        event.update(public_at=public_at, public_observed_at=NOW-10)
    market = dict(id='m', event_id='e', active=True, closed=False,
                  observed_at=NOW-10000, liquidity=10000, tokens=[
                      {'token_id': 't', 'outcome': 'Named outcome'},
                      {'token_id': 'u', 'outcome': 'Other outcome'}])
    return [market], [event]


class SignalTests(unittest.TestCase):
    def test_diagnostics_reconcile_buy_candidates_without_changing_cases(self):
        markets,events=metadata();rows=[trade(),trade('2',wallet=B,size=1),trade('3',wallet=C,side='SELL')]
        diagnostics={}
        result=evaluate(rows,markets,events,now=NOW,config=CONFIG,diagnostics=diagnostics)
        self.assertEqual(result,evaluate(rows,markets,events,now=NOW,config=CONFIG))
        self.assertEqual(diagnostics['wallet_event_pairs'],3)
        self.assertEqual(diagnostics['examined_recent_buy_pairs'],2)
        self.assertEqual(diagnostics['emitted_cases']+diagnostics['without_signal'],2)
        self.assertEqual(diagnostics['without_signal'],1)

    def test_older_known_trade_outside_analysis_input_prevents_first_activity_signal(self):
        markets,events=metadata()
        context={A:{'first_timestamp':NOW-86400*10,'observations':200}}
        cases=evaluate([trade()],markets,events,now=NOW,config=CONFIG,wallet_history=context)
        self.assertNotIn('first_observed_large',{s['rule'] for c in cases for s in c['signals']})

    def evaluate(self, rows, **kw):
        markets, events = metadata()
        return evaluate(rows, kw.get('markets', markets), kw.get('events', events),
                        now=NOW, config=CONFIG)

    def test_synthetic_alert_reachable_and_censored(self):
        cases = self.evaluate([trade()])
        self.assertEqual(len(cases), 1)
        case = cases[0]
        self.assertEqual(case['status'], 'données insuffisantes')
        self.assertIn('première disponibilité publique inconnue', case['limitations'])
        self.assertTrue(case['quality']['history_left_censored'])
        self.assertFalse(case.get('calibrated', True))
        self.assertTrue(all('n' in s and 'reference' in s for s in case['signals']))

    def test_future_observation_and_later_trade_do_not_change_score(self):
        base = self.evaluate([trade()])
        future = trade('future', size=100000)
        future['observed_at'] = NOW+1
        later = trade('later', at=NOW+2, price=.99)
        self.assertEqual(base, self.evaluate([trade(), future, later]))

    def test_public_result_excludes_preliminary_case(self):
        markets, events = metadata(NOW-30)
        cases = self.evaluate([trade()], markets=markets, events=events)
        self.assertEqual(cases[0]['status'], 'information publique retrouvée')
        self.assertFalse(cases[0]['preliminary'])
        self.assertEqual(cases[0]['score'], 0)

    def test_public_result_observed_later_cannot_change_replay(self):
        markets, events = metadata(NOW-30)
        events[0]['public_observed_at'] = NOW+30
        cases = self.evaluate([trade()], markets=markets, events=events)
        self.assertNotEqual(cases[0]['status'], 'information publique retrouvée')

    def test_closed_event_is_retrospective(self):
        markets, events = metadata()
        events[0]['closed'] = True
        self.assertEqual(self.evaluate([trade()], events=events)[0]['status'], 'événement terminé')

    def test_future_liquidity_is_not_reference(self):
        markets, events = metadata()
        markets[0]['observed_at'] = NOW-1
        cases = self.evaluate([trade()], markets=markets, events=events)
        self.assertNotIn('liquidity_fraction', {s['rule'] for s in cases[0]['signals']})

    def test_split_order_grouping_and_dedup(self):
        rows = [trade(str(i), size=1000, order_hash='parent') for i in range(4)]
        groups = group_fills(rows + [copy.deepcopy(rows[0])], now=NOW)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['size'], 4000)
        self.assertEqual(len(groups[0]['trade_ids']), 4)
        self.assertEqual(groups[0]['nominal'], 2000)

    def test_fallback_group_does_not_merge_opposite_side_or_complement(self):
        rows = [trade('1'), trade('2', token='u', side='SELL')]
        rows[1]['transaction_hash'] = rows[0]['transaction_hash']
        groups = group_fills(rows, now=NOW)
        self.assertEqual(len(groups), 2)
        self.assertEqual({g['side'] for g in groups}, {'BUY', 'SELL'})
        self.assertEqual({g['token_id'] for g in groups}, {'t', 'u'})

    def test_same_transaction_is_not_synchronization_evidence(self):
        rows = [trade(str(i), wallet=w) for i,w in enumerate([A,B,C])]
        for r in rows:
            r['transaction_hash'] = 'shared'
        cases = self.evaluate(rows)
        self.assertFalse(any(s['rule']=='synchronized_entries' for c in cases for s in c['signals']))

    def test_synchronization_is_not_ownership_proof(self):
        rows = [trade(str(i), wallet=w) for i,w in enumerate([A,B,C])]
        cases = self.evaluate(rows)
        self.assertTrue(all(any(s['rule']=='synchronized_entries' for s in c['signals']) for c in cases))
        self.assertTrue(all(c['coordination']['ownership_established'] is False for c in cases))
        self.assertTrue(all(c['priority'] for c in cases))

    def test_wallet_size_baseline_excludes_current(self):
        rows = [trade(str(i), at=NOW-100-i, size=20) for i in range(3)] + [trade('large')]
        case = self.evaluate(rows)[0]
        signal = next(s for s in case['signals'] if s['rule']=='wallet_size_shift')
        self.assertEqual(signal['n'], 3)
        self.assertEqual(signal['reference']['median'], 10)

    def test_signal_families_are_not_double_counted(self):
        case = self.evaluate([trade()])[0]
        families = {s['family'] for s in case['signals'] if s.get('weight', 0)>0}
        self.assertEqual(case['score'], len(families))

    def test_loss_and_fees(self):
        rows = [trade('buy', size=100, price=.6, at=NOW-50),
                trade('sell', size=100, price=.4, side='SELL', at=NOW-10)]
        result = bookkeeping(rows, history_complete=True)
        self.assertAlmostEqual(result['realized_gross'], -20)
        self.assertAlmostEqual(result['realized_net'], -20)
        self.assertEqual(result['tokens']['t']['observed_inventory_delta'], 0)
        self.assertEqual(result['volume'], 100)

    def test_unknown_opening_or_transform_makes_pnl_not_calculable(self):
        rows = [trade('buy', size=100), trade('sell', size=100, side='SELL')]
        self.assertIsNone(bookkeeping(rows)['realized_net'])
        rows.append(dict(type='SPLIT', timestamp=NOW, observed_at=NOW))
        self.assertIsNone(bookkeeping(rows, history_complete=True)['realized_gross'])

    def test_unmatched_sale_never_invents_cost(self):
        result = bookkeeping([trade(side='SELL')], history_complete=True)
        self.assertIsNone(result['realized_gross'])
        self.assertEqual(result['status'], 'non calculable')

    def test_unknown_fee_retains_gross_only(self):
        rows = [trade('buy', size=100, price=.6, at=NOW-50),
                trade('sell', size=100, price=.4, side='SELL', at=NOW-10)]
        rows[1]['fee'] = None
        result = bookkeeping(rows, history_complete=True)
        self.assertAlmostEqual(result['realized_gross'], -20)
        self.assertIsNone(result['realized_net'])

    def test_invalid_numeric_data_is_explicit(self):
        row = trade()
        row['price'] = float('nan')
        with self.assertRaises(ValueError):
            self.evaluate([row])

    def test_unknown_catalog_status_is_not_preliminary(self):
        case = self.evaluate([trade()], markets=[], events=[])[0]
        self.assertFalse(case['preliminary'])
        self.assertFalse(case['priority'])

    def test_clock_alone_does_not_change_material_fingerprint(self):
        markets, events = metadata()
        before = evaluate([trade()], markets, events, now=NOW, config=CONFIG)[0]
        after = evaluate([trade()], markets, events, now=NOW+60, config=CONFIG)[0]
        self.assertEqual(before['material_fingerprint'], after['material_fingerprint'])

    def test_group_fee_sum_and_multiple_transaction_identity(self):
        rows = [trade(str(i), size=1000, order_hash='parent') for i in range(4)]
        for r in rows:
            r['fee'] = 1
        group = group_fills(rows, now=NOW)[0]
        self.assertEqual(group['fee'], 4)
        self.assertIsNone(group['transaction_hash'])
        self.assertEqual(len(group['transactions']), 4)

    def test_same_second_order_unknown_is_not_calculable(self):
        result = bookkeeping([trade('buy'), trade('sell', side='SELL')], history_complete=True)
        self.assertTrue(result['ordering_uncertain'])
        self.assertIsNone(result['realized_gross'])

    def test_distinct_tx_count_cannot_fake_distinct_wallet_transactions(self):
        rows = [trade(str(i), wallet=A) for i in range(3)]
        for i,wallet in enumerate((B,C)):
            row = trade('shared'+str(i), wallet=wallet)
            row['transaction_hash'] = 'shared'
            rows.append(row)
        cases = self.evaluate(rows)
        self.assertFalse(any(s['rule']=='synchronized_entries' for c in cases for s in c['signals']))

    def test_liquidity_uses_old_snapshot_and_not_post_trade_refresh(self):
        markets, events = metadata()
        markets[0]['observed_at'] = NOW-30
        later = copy.deepcopy(markets[0])
        later.update(observed_at=NOW-1, liquidity=1)
        before = self.evaluate([trade()], markets=markets, events=events)[0]
        after = self.evaluate([trade()], markets=markets+[later], events=events)[0]
        ref = next(s for s in after['signals'] if s['rule']=='liquidity_fraction')['reference']
        self.assertEqual(ref['liquidity'], 10000)
        self.assertEqual(before['score'], after['score'])

    def test_verified_log_order_allows_same_second_loss(self):
        rows = [trade('z-buy', size=100, price=.6, block_number=123, log_index=1),
                trade('a-sell', size=100, price=.4, side='SELL', block_number=123, log_index=2)]
        result = bookkeeping(rows, history_complete=True)
        self.assertFalse(result['ordering_uncertain'])
        self.assertAlmostEqual(result['realized_net'], -20)

    def test_event_ids_do_not_establish_independence(self):
        rows = [trade(str(i), event=e, at=NOW-10-i) for i,e in enumerate(('e','e2','e3'))]
        cases = self.evaluate(rows)
        repeated = [s for c in cases for s in c['signals'] if s['rule']=='repeated_large_entries']
        self.assertTrue(repeated)
        self.assertTrue(all(s['weight']==0 for s in repeated))

    def test_mixed_event_closed_buys_cannot_trigger_preliminary_alert(self):
        markets, events = metadata()
        closed = dict(markets[0], id='closed', closed=True)
        rows = []
        for i, wallet in enumerate((A, B, C)):
            rows.extend([trade(f'{i}-closed',wallet=wallet,market='closed',token='closed-token',size=10000,at=NOW-10+i),
                         trade(f'{i}-open',wallet=wallet,size=2,at=NOW-9+i)])
        cases = self.evaluate(rows, markets=markets+[closed], events=events)
        self.assertEqual(len(cases), 3)
        self.assertTrue(all(not c['priority'] and not c['preliminary'] and c['score']==0 for c in cases))
        self.assertTrue(all(c['retrospective_score']>=2 for c in cases))
        self.assertFalse(any(a['market_id']=='closed' for c in cases for a in c['alerts']))
        self.assertTrue(all(c['retrospective_trades'] for c in cases))

    def test_mixed_event_resolved_and_past_end_markets_are_excluded(self):
        for field in ({'resolved':True}, {'end_date':NOW-1},
                      {'public_at':NOW-30,'public_observed_at':NOW-25}):
            with self.subTest(field=field):
                markets, events = metadata()
                excluded = dict(markets[0], id='excluded', **field)
                rows = [trade('excluded',market='excluded',size=10000),trade('small',size=2,at=NOW-10)]
                cases = self.evaluate(rows, markets=markets+[excluded], events=events)
                self.assertFalse(any(c['priority'] or c['preliminary'] for c in cases))
                self.assertFalse(any(a['market_id']=='excluded' for c in cases for a in c['alerts']))

    def test_valid_open_signal_survives_with_closed_history_separate(self):
        markets, events = metadata()
        closed = dict(markets[0],id='closed',closed=True)
        rows = [trade('old',market='closed',size=10000,at=NOW-100)]
        rows += [trade(str(i),wallet=w,size=10000) for i,w in enumerate((A,B,C))]
        cases = self.evaluate(rows, markets=markets+[closed], events=events)
        self.assertTrue(all(c['priority'] for c in cases))
        self.assertTrue(all(a['market_id']=='m' for c in cases for a in c['alerts']))

    def test_later_closed_snapshot_does_not_change_earlier_replay(self):
        markets, events = metadata()
        later = dict(markets[0],closed=True,observed_at=NOW+1)
        before = self.evaluate([trade()],markets=markets,events=events)
        self.assertEqual(before,self.evaluate([trade()],markets=markets+[later],events=events))


class ScenarioTests(unittest.TestCase):
    @staticmethod
    def market(key, question, event='award', outcomes=('Yes', 'No')):
        return dict(id=key,event_id=event,question=question,
                    tokens=[dict(token_id=f'{key}-{i}',outcome=o) for i,o in enumerate(outcomes)])

    def test_winner_top_three_exact_second_are_conditional_rank_scenarios(self):
        rows = [self.market('winner', "Will Alice win the 2026 Ballon d'Or?"),
                self.market('top', "Will Alice finish in the top 3 of the 2026 Ballon d'Or?"),
                self.market('second', "Will Alice finish 2nd in the 2026 Ballon d'Or?")]
        result = describe_scenarios(rows)
        self.assertEqual(result['score_bonus'], 0)
        self.assertFalse(result['independence_assumed'])
        self.assertEqual(len(result['groups']), 1)
        group = result['groups'][0]
        self.assertFalse(group['resolution_equivalence_verified'])
        ranks = {tuple(s['rank_interval']):s['affirmative_outcomes'] for s in group['coherent_scenarios']}
        self.assertEqual(ranks[(1,1)], {'winner': True, 'top': True, 'second': False})
        self.assertEqual(ranks[(2,2)], {'winner': False, 'top': True, 'second': True})
        self.assertEqual(ranks[(4,None)], {'winner': False, 'top': False, 'second': False})

    def test_unrelated_title_or_competition_does_not_join(self):
        rows = [self.market('winner', 'Will Alice win the Championship?'),
                self.market('top', 'Will Alice finish in the top 3 of the Other Championship?'),
                self.market('unrelated', 'Will Alice attend the Championship?'),
                self.market('other-event', 'Will Alice finish 2nd in the Championship?', event='other')]
        result = describe_scenarios(rows)
        self.assertTrue(all(len(g['markets'])==1 for g in result['groups']))
        self.assertEqual(result['unclassified'][0]['market_id'], 'unrelated')

    def test_explicit_named_issue_can_match_binary_subject(self):
        rows = [self.market('winner', 'Who will win the Championship?', outcomes=('Alice','Bob','Other')),
                self.market('top', 'Will Alice finish in the top 3 of the Championship?')]
        result = describe_scenarios(rows)
        alice = next(g for g in result['groups'] if g['subject']=='Alice')
        self.assertEqual(len(alice['markets']), 2)
        self.assertTrue(all(m['positive_token_id'] for m in alice['markets']))

    def test_unlabeled_boolean_and_missing_event_remain_unclassified(self):
        rows = [self.market('a', 'Will Alice win the Championship?', outcomes=('0','1')),
                self.market('b', 'Will Alice win the Championship?', event='')]
        result = describe_scenarios(rows)
        self.assertEqual(result['groups'], [])
        self.assertEqual(len(result['unclassified']), 2)

    def test_winning_several_games_is_not_winner_rank(self):
        result = describe_scenarios([self.market('count', 'Will Alice win at least 3 games?')])
        self.assertEqual(result['groups'], [])
        self.assertEqual(result['unclassified'][0]['market_id'], 'count')


if __name__ == '__main__':
    unittest.main()
