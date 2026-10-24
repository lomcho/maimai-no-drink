import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).parents[1] / 'skills/maimai-no-drink/scripts'))
from price_guard import verify_price

class PriceTests(unittest.TestCase):
    def test_real_observed_units(self):
        r=verify_price(dict(success=True, code=200, data=dict(productPrice=4150, deliveryPrice=600, packingPrice=190, price=4940)))
        self.assertEqual(r['payable_fen'],4940)
    def test_unknown_fee_missing_fee_failed_price(self):
        for d in [dict(productPrice=4150, deliveryPrice=600, price=4940),dict(productPrice=4150, deliveryPrice=600, packingPrice=190, price=5040),dict(productPrice=41.5, deliveryPrice=6, packingPrice=1.9, price=49.4)]:
            with self.subTest(data=d),self.assertRaises(ValueError):verify_price(dict(success=True,code=200,data=d))
        with self.assertRaises(ValueError):verify_price(dict(success=False,code=400,data={}))
