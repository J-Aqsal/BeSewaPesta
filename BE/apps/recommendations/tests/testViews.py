from rest_framework.test import APITestCase
from apps.products.models import (
    Category, Product, ProductUpsellRelation, VariantType, VariantOption,
    ProductVariantCombination, ProductVariantCombinationOption
)
from apps.carts.models import Cart, CartItem
from utils.constants import BAD_REQUEST_CODE, SUCCESS_CODE
from django.utils import timezone
from datetime import timedelta
import uuid

class RecommendationAPIViewTest(APITestCase):
    def setUp(self):
        self.guestId = str(uuid.uuid4())
        self.startDate = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT10:00:00Z')
        self.endDate = (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT10:00:00Z')

        self.category = Category.objects.create(name='Peralatan Pesta')
        
        self.productBase = Product.objects.create(name='Tenda Reguler', price=100000, price_unit='hari', total_stock=5, category=self.category)
        self.productUpsell = Product.objects.create(name='Tenda VIP', price=200000, price_unit='hari', total_stock=3, category=self.category)
        
        ProductUpsellRelation.objects.create(
            source_product=self.productBase,
            target_product=self.productUpsell
        )

        self.productWithVariant = Product.objects.create(name='Meja IBM', price=200000, price_unit='pcs', total_stock=0, category=self.category)
        self.vType = VariantType.objects.create(product=self.productWithVariant, name='Tipe', is_upsell_dimension=True)
        self.vOpt1 = VariantOption.objects.create(variant_type=self.vType, value='Tanpa Cover')
        self.vOpt2 = VariantOption.objects.create(variant_type=self.vType, value='Dengan Cover')
        
        self.combBase = ProductVariantCombination.objects.create(product=self.productWithVariant, price=200000, stock=50)
        ProductVariantCombinationOption.objects.create(product_variant_combination=self.combBase, variant_option=self.vOpt1)
        
        self.combUpsell = ProductVariantCombination.objects.create(product=self.productWithVariant, price=250000, stock=100)
        ProductVariantCombinationOption.objects.create(product_variant_combination=self.combUpsell, variant_option=self.vOpt2)

        self.cart = Cart.objects.create(
            guest_id=self.guestId,
            rental_start=self.startDate,
            rental_end=self.endDate
        )
        CartItem.objects.create(
            cart=self.cart,
            product=self.productBase,
            quantity=1
        )

    def testUpSellAPIViewSuccess(self):
        """
        Input: GET request ke `/api/recommendations/up-sell/` membawa `idProduct`, `startDate`, `endDate`, `quantity`.
        Skenario: Meminta rekomendasi produk upsell untuk 'Tenda Reguler' dari halaman produk atau keranjang.
        Expected Output: Status 200 OK, mengembalikan array berisi 'Tenda VIP'.
        """
        response = self.client.get(f"/api/recommendations/up-sell/?idProduct={self.productBase.id}&startDate={self.startDate}&endDate={self.endDate}&quantity=1")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        
        data = response.json()['data']
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]['productName'], 'Tenda VIP')

    def testUpSellAPIViewVariant(self):
        """
        Input: GET request ke `/api/recommendations/up-sell/` membawa `idProduct`, `idVariantCombination`, `startDate`, `endDate`.
        Skenario: Meminta rekomendasi produk upsell algoritmik dari varian produk (Meja IBM Tanpa Cover -> Dengan Cover).
        Expected Output: Status 200 OK, mengembalikan array varian upsell dengan idVariantCombination.
        """
        response = self.client.get(f"/api/recommendations/up-sell/?idProduct={self.productWithVariant.id}&idVariantCombination={self.combBase.id}&startDate={self.startDate}&endDate={self.endDate}&quantity=1")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        
        data = response.json()['data']
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]['price'], 250000)
        self.assertEqual(data[0]['idUpsell'], self.combUpsell.id)

    def testUpSellAPIViewMissingId(self):
        """
        Input: GET request ke `/api/recommendations/up-sell/` TANPA membawa `idProduct`.
        Skenario: Payload/Query params cacat.
        Expected Output: Status 400 Bad Request, dengan pesan peringatan.
        """
        response = self.client.get("/api/recommendations/up-sell/")
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)
        self.assertFalse(response.json()['success'])

    def testCrossSellAPIViewSuccess(self):
        """
        Input: GET request ke `/api/recommendations/cross-sell/` membawa `guestId`.
        Skenario: User membuka keranjang belanja. Sistem menarik data produk lain yang relevan dengan isi keranjang tersebut.
        Expected Output: Status 200 OK. Karena datanya kecil, setidaknya array dikembalikan tanpa error.
        """
        response = self.client.get(f"/api/recommendations/cross-sell/?guestId={self.guestId}")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])

    def testCrossSellAPIViewMissingGuestId(self):
        """
        Input: GET request ke `/api/recommendations/cross-sell/` TANPA membawa `guestId`.
        Skenario: Payload/Query params cacat.
        Expected Output: Status 400 Bad Request.
        """
        response = self.client.get("/api/recommendations/cross-sell/")
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)
        self.assertFalse(response.json()['success'])
