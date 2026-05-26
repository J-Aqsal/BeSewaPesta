from django.test import TestCase
from .services import calculateShippingCostService

class ShippingCostTests(TestCase):
    def test_jakarta_normalization(self):
        # Subtotal < 500,000, Jakarta base cost is 500,000
        cost_pusat = calculateShippingCostService(100000, "Jakarta Pusat")
        cost_selatan = calculateShippingCostService(100000, "jakarta selatan")
        cost_plain = calculateShippingCostService(100000, "Jakarta")
        
        self.assertEqual(cost_pusat, 500000)
        self.assertEqual(cost_selatan, 500000)
        self.assertEqual(cost_plain, 500000)

    def test_tangerang_normalization(self):
        # Subtotal < 500,000, Tangerang base cost is 1,000,000
        cost_selatan = calculateShippingCostService(100000, "Tangerang Selatan")
        cost_kota = calculateShippingCostService(100000, "tangerang kota")
        
        self.assertEqual(cost_selatan, 1000000)
        self.assertEqual(cost_kota, 1000000)

    def test_unknown_city(self):
        cost = calculateShippingCostService(100000, "Surabaya")
        self.assertEqual(cost, 0)
