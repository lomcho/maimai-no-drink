import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('menu_index',Path(__file__).parents[1]/'skills/maimai-no-drink/scripts/menu_index.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MenuIndexTests(unittest.TestCase):
    def fixture(self):
        menu={'meals':{'A':{'name':'神秘餐'},'B':{'name':'鸡排堡'},'C':{'name':'玉米杯(小)'}}}
        details={'A':{'name':'神秘餐','rounds':[{'choices':[{'code':'P','name':'土豆泥'}]}]},'B':{'name':'鸡排堡'},'C':{'name':'玉米杯（小）'}}
        return menu,details
    def test_discovers_food_hidden_in_bundle(self):
        a,b=self.fixture();i=m.build_index(a,b);hit=m.lookup(i,'土豆泥')
        self.assertEqual(hit['status'],'exact');self.assertEqual(hit['matches'][0]['parents'],['A'])
    def test_does_not_replace_patty_with_burger(self):
        a,b=self.fixture();self.assertEqual(m.lookup(m.build_index(a,b),'大鸡排')['status'],'not_found_in_returned_menu')
    def test_failed_details_prevent_absence_claim(self):
        a,b=self.fixture();b.pop('A');i=m.build_index(a,b,{'A':'HTTPError'})
        self.assertFalse(i['discovery_complete']);self.assertEqual(m.lookup(i,'土豆泥')['status'],'discovery_incomplete')
    def test_partial_and_ambiguous_are_not_confirmed(self):
        a,b=self.fixture();i=m.build_index(a,b);self.assertEqual(m.lookup(i,'鸡排')['status'],'needs_confirmation')
    def test_normalizes_punctuation_and_keeps_scope(self):
        a,b=self.fixture();i=m.build_index(a,b);self.assertEqual(m.lookup(i,'玉米杯（小）')['status'],'exact');self.assertFalse(i['price_search_complete'])
    def test_new_menu_food_needs_no_allowlist(self):
        a,b=self.fixture();a['meals']['NEW']={'name':'全新食物'};b['NEW']={'name':'全新食物'}
        self.assertEqual(m.lookup(m.build_index(a,b),'全新食物')['status'],'exact')
