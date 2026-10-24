import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('replay',Path(__file__).parents[1]/'scripts/replay.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ReplayTests(unittest.TestCase):
    def test_historical_snapshot(self):
        result=module.replay()
        self.assertEqual(result['mode'],'historical_replay')
        self.assertEqual([r['payable_fen'] for r in result['results']],[4940,5040])
        self.assertTrue(all(r['best']=='single' and r['combo_extra_fen']==440 for r in result['results']))
