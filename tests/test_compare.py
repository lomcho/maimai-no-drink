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

if __name__ == '__main__':
    unittest.main()
