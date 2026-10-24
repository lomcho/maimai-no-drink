import importlib.util
from pathlib import Path
from datetime import datetime, timezone
import unittest

spec = importlib.util.spec_from_file_location('compare', Path(__file__).parents[1] / 'skills/maimai-no-drink/scripts/compare.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class QuoteTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)
        self.request = dict(context='store-delivery-batch-1', required={'burger': 1, 'wing_piece': 2}, drink_mode='indifferent')
    def quote(self, **changes):
        q = dict(id='combo', context=self.request['context'], foods={'burger': 1, 'wing_piece': 2}, drinks=1, resources=[], confirmed=True, fees_complete=True, payable_fen=2200, quoted_at=self.now.isoformat(), source='simulation')
        q.update(changes)
        return q
    def run_quotes(self, quotes):
        return module.rank(self.request, quotes, self.now)
    def test_combo_cheaper_despite_unwanted_drink(self):
        r = self.run_quotes([self.quote(), self.quote(id='single', drinks=0, payable_fen=2500)])
        self.assertEqual(r['best']['id'], 'combo')
        self.assertEqual(r['no_drink_extra_fen'], 300)
    def test_strict_exclusion(self):
        self.request['drink_mode'] = 'exclude'
        self.assertEqual(self.run_quotes([self.quote(), self.quote(id='single', drinks=0, payable_fen=2500)])['best']['id'], 'single')
    def test_invalid_candidates_cannot_win(self):
        for change in [dict(fees_complete=False), dict(confirmed=False), dict(context='other-store'), dict(payable_fen=None), dict(payable_fen=True), dict(foods={'burger':1, 'wing_piece':1}), dict(resources=['new_membership']), dict(resources=['points']), dict(quoted_at='2026-10-24T11:00:00+00:00')]:
            with self.subTest(change=change):
                self.assertIsNone(self.run_quotes([self.quote(**change)])['best'])
    def test_no_drink_wins_tie(self):
        self.assertEqual(self.run_quotes([self.quote(), self.quote(id='single', drinks=0)])['best']['id'], 'single')
    def test_mixed_evidence_rejected(self):
        with self.assertRaises(ValueError):
            self.run_quotes([self.quote(), self.quote(id='live', source='live')])
    def test_explicit_resource_opt_in(self):
        self.request['allow_resources'] = ['points']
        self.assertIsNotNone(self.run_quotes([self.quote(resources=['points'])])['best'])
    def test_empty_quotes(self):
        self.assertIsNone(self.run_quotes([])['best'])
    def test_duplicate_ids_fail_closed(self):
        with self.assertRaises(ValueError):self.run_quotes([self.quote(),self.quote(payable_fen=1)])
    def test_extra_food_disclosed_in_result(self):
        self.request['allow_extra_food'] = True
        r=self.run_quotes([self.quote(foods={'burger':1,'wing_piece':2,'nugget':5})])
        self.assertEqual(r['best']['foods']['nugget'],5)
    def test_default_excludes_drinks(self):
        self.request.pop('drink_mode')
        self.assertIsNone(self.run_quotes([self.quote()])['best'])
    def test_default_excludes_extra_food(self):
        self.assertIsNone(self.run_quotes([self.quote(foods={'burger':1,'wing_piece':2,'nugget':5})])['best'])
    def test_authorized_extra_quantity(self):
        self.request['allow_extra_food'] = True
        self.assertIsNotNone(self.run_quotes([self.quote(foods={'burger':1,'wing_piece':4})])['best'])
    def test_extra_required_food_not_same_portion(self):
        self.assertIsNone(self.run_quotes([self.quote(foods={'burger':2,'wing_piece':2})])['best'])
    def test_stale_or_future_quotes_rejected(self):
        for t in ['2026-10-24T12:01:00+00:00','2026-10-24T11:49:00+00:00','2026-10-24T12:00:00']:
            with self.subTest(time=t):self.assertIsNone(self.run_quotes([self.quote(quoted_at=t)])['best'])

class ValueOptionsTests(QuoteTests):
    def recommend(self, quotes):
        return module.recommend(self.request, quotes, self.now)
    def test_separate_exact_and_extra(self):
        self.request['drink_mode']='exclude'
        base=self.quote(id='base',drinks=0,payable_fen=2600)
        extra=self.quote(id='extra',drinks=0,payable_fen=2900,foods={'burger':1,'wing_piece':2,'fries':1})
        r=self.recommend([extra,base])
        self.assertEqual(r['best']['id'],'base')
        self.assertEqual(r['value_options'][0]['delta_fen'],300)
        self.assertEqual(r['value_options'][0]['extra_foods'],{'fries':1})
    def test_cheaper_extra_is_not_discarded(self):
        r=self.recommend([self.quote(id='base',drinks=0,payable_fen=3000),self.quote(id='extra',drinks=0,foods={'burger':1,'wing_piece':4})])
        self.assertEqual(r['value_options'][0]['delta_fen'],-800)
    def test_value_rejects_invalid_missing_drink_and_large_delta(self):
        base=self.quote(id='base',drinks=0)
        for changes in [dict(drinks=1),dict(fees_complete=False),dict(foods={'burger':1,'fries':1}),dict(payable_fen=2800),dict(context='other'),dict(resources=['points']),dict(quoted_at='2026-10-24T11:00:00+00:00')]:
            with self.subTest(changes=changes):
                q=self.quote(id='extra',drinks=0,foods={'burger':1,'wing_piece':2,'fries':1})
                q.update(changes)
                self.assertEqual(self.recommend([base,q])['value_options'],[])
    def test_exact_only(self):
        self.request['exact_only']=True
        self.assertEqual(self.recommend([self.quote(drinks=0,foods={'burger':1,'wing_piece':4})])['value_options'],[])
    def test_no_baseline_no_fake_difference(self):
        r=self.recommend([self.quote(drinks=0,foods={'burger':1,'wing_piece':4})])
        self.assertIsNone(r['best'])
        self.assertIsNone(r['value_options'][0]['delta_fen'])
    def test_budget_and_custom_increment(self):
        self.request.update(extra_budget_fen=1000,budget_fen=2800)
        q=self.quote(id='extra',drinks=0,payable_fen=2900,foods={'burger':1,'wing_piece':4})
        self.assertEqual(self.recommend([self.quote(drinks=0),q])['value_options'],[])
        self.request['budget_fen']=3000
        self.assertEqual(len(self.recommend([self.quote(drinks=0),q])['value_options']),1)
    def test_duplicate_baskets_and_max_two(self):
        quotes=[self.quote(id='base',drinks=0)]
        for i in range(1,5):
            quotes.append(self.quote(id=str(i),drinks=0,payable_fen=2200+i,foods={'burger':1,'wing_piece':2,'fries':i}))
        quotes.append(dict(quotes[1],id='duplicate',payable_fen=2202))
        self.assertEqual([q['quote']['id'] for q in self.recommend(quotes)['value_options']],['1','2'])
    def test_empty_and_invalid_budget(self):
        self.assertEqual(self.recommend([])['value_options'],[])
        self.request['extra_budget_fen']=-1
        with self.assertRaises(ValueError):self.recommend([])

if __name__ == '__main__':
    unittest.main()
