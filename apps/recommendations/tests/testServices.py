from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import uuid
from apps.products.models import (
    Category, Product, ProductUpsellRelation, VariantType, VariantOption,
    ProductVariantCombination, ProductVariantCombinationOption, Tag, ProductTag
)
from apps.carts.models import Cart, CartItem
from apps.recommendations.services import getUpsellingRecommendations, getCrossSellRecommendations

class RecommendationServicesTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Peralatan Pesta')
        self.category2 = Category.objects.create(name='Furniture')
        
        # Products
        self.productBase = Product.objects.create(name='Tenda Reguler', price=100000, price_unit='hari', total_stock=5, category=self.category)
        self.productUpsell = Product.objects.create(name='Tenda VIP', price=200000, price_unit='hari', total_stock=3, category=self.category)
        self.productCrossSell = Product.objects.create(name='Kursi Lipat', price=10000, price_unit='hari', total_stock=20, category=self.category2)
        
        # Product with Variant (for algorithmic upsell)
        self.productWithVariant = Product.objects.create(name='Meja IBM', price=200000, price_unit='pcs', total_stock=0, category=self.category)
        
        self.vType = VariantType.objects.create(product=self.productWithVariant, name='Tipe', is_upsell_dimension=True)
        self.vOpt1 = VariantOption.objects.create(variant_type=self.vType, value='Tanpa Cover')
        self.vOpt2 = VariantOption.objects.create(variant_type=self.vType, value='Dengan Cover')
        
        # Combination 1 (Current)
        self.combBase = ProductVariantCombination.objects.create(product=self.productWithVariant, price=200000, stock=50)
        ProductVariantCombinationOption.objects.create(product_variant_combination=self.combBase, variant_option=self.vOpt1)
        
        # Combination 2 (Upsell Target)
        self.combUpsell = ProductVariantCombination.objects.create(product=self.productWithVariant, price=250000, stock=100)
        ProductVariantCombinationOption.objects.create(product_variant_combination=self.combUpsell, variant_option=self.vOpt2)
        
        # Tags for Cross Sell calculation
        self.tagEvent = Tag.objects.create(name='Acara Outdoor', label='Acara Outdoor', group_name='Event')
        ProductTag.objects.create(product=self.productBase, tag=self.tagEvent, weight=0.8)
        ProductTag.objects.create(product=self.productCrossSell, tag=self.tagEvent, weight=0.8)

        # Upsell manual relations
        ProductUpsellRelation.objects.create(
            source_product=self.productBase,
            target_product=self.productUpsell
        )

        # Dates
        self.startDate = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT10:00:00Z')
        self.endDate = (timezone.now() + timedelta(days=2)).strftime('%Y-%m-%dT10:00:00Z')

        # Cart for Cross Sell
        self.guestId = str(uuid.uuid4())
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

        # Base product 2 (untuk test akumulasi stok)
        self.productBase2 = Product.objects.create(name='Kursi Biasa', price=10000, price_unit='pcs', total_stock=1000, category=self.category2)
        
        # Target Upsell product with variants
        self.productUpsellVariantTarget = Product.objects.create(name='Kursi VIP', price=20000, price_unit='pcs', total_stock=0, category=self.category2)
        
        self.vTypeVIP = VariantType.objects.create(product=self.productUpsellVariantTarget, name='Warna')
        self.vOptVIP1 = VariantOption.objects.create(variant_type=self.vTypeVIP, value='Merah')
        self.vOptVIP2 = VariantOption.objects.create(variant_type=self.vTypeVIP, value='Putih')
        
        self.combVIP1 = ProductVariantCombination.objects.create(product=self.productUpsellVariantTarget, price=20000, stock=50)
        ProductVariantCombinationOption.objects.create(product_variant_combination=self.combVIP1, variant_option=self.vOptVIP1)
        
        self.combVIP2 = ProductVariantCombination.objects.create(product=self.productUpsellVariantTarget, price=20000, stock=70)
        ProductVariantCombinationOption.objects.create(product_variant_combination=self.combVIP2, variant_option=self.vOptVIP2)

        # Target Upsell product 2 with variants (Fallback)
        self.productUpsellVariantFallback = Product.objects.create(name='Kursi VVIP', price=30000, price_unit='pcs', total_stock=0, category=self.category2)
        
        self.vTypeVVIP = VariantType.objects.create(product=self.productUpsellVariantFallback, name='Warna')
        self.vOptVVIP1 = VariantOption.objects.create(variant_type=self.vTypeVVIP, value='Merah')
        self.vOptVVIP2 = VariantOption.objects.create(variant_type=self.vTypeVVIP, value='Putih')
        
        self.combVVIP1 = ProductVariantCombination.objects.create(product=self.productUpsellVariantFallback, price=30000, stock=100)
        ProductVariantCombinationOption.objects.create(product_variant_combination=self.combVVIP1, variant_option=self.vOptVVIP1)
        
        self.combVVIP2 = ProductVariantCombination.objects.create(product=self.productUpsellVariantFallback, price=30000, stock=100)
        ProductVariantCombinationOption.objects.create(product_variant_combination=self.combVVIP2, variant_option=self.vOptVVIP2)

        ProductUpsellRelation.objects.create(
            source_product=self.productBase2,
            target_product=self.productUpsellVariantTarget
        )
        
        ProductUpsellRelation.objects.create(
            source_product=self.productUpsellVariantTarget,
            target_product=self.productUpsellVariantFallback
        )

    def testGetUpsellingRecommendationsManual(self):
        """
        Input: productId dari produk utama (Tenda Reguler).
        Skenario: Sistem mencari produk upsell yang sudah didefinisikan secara manual di tabel ProductUpsellRelation.
        Expected Output: Mengembalikan 'Tenda VIP' karena direlasikan langsung.
        """
        recs = getUpsellingRecommendations(
            productId=self.productBase.id,
            startDate=self.startDate,
            endDate=self.endDate,
            quantity=1
        )
        self.assertGreaterEqual(len(recs), 1)
        self.assertEqual(recs[0]['productName'], 'Tenda VIP')

    def testGetUpsellingRecommendationsVariant(self):
        """
        Input: productId (Meja IBM) dan variantId (Tanpa Cover).
        Skenario: Sistem mengecek apakah tipe varian ini punya 'is_upsell_dimension'=True, dan mencari kombinasi lain yang harganya lebih mahal (Dengan Cover).
        Expected Output: Mengembalikan 'Meja IBM + Cover' atau varian dengan harga 250000.
        """
        recs = getUpsellingRecommendations(
            productId=self.productWithVariant.id,
            variantId=self.combBase.id,
            startDate=self.startDate,
            endDate=self.endDate,
            quantity=1
        )
        
        self.assertGreaterEqual(len(recs), 1)
        self.assertEqual(recs[0]['price'], 250000)
        self.assertEqual(recs[0]['idUpsell'], self.combUpsell.id)
        self.assertEqual(recs[0]['availableStock'], 100)

    def testGetCrossSellRecommendations(self):
        """
        Input: guestId yang keranjangnya berisi 'Tenda Reguler'.
        Skenario: Sistem menghitung Weighted Jaccard Similarity antara produk di keranjang dan produk lain yang satu kategori/tag.
        Expected Output: Mengembalikan 'Kursi Lipat' sebagai rekomendasi lintas-jual karena memiliki tag 'Acara Outdoor' yang sama dengan Tenda Reguler.
        """
        recs = getCrossSellRecommendations(self.guestId)
        
        # Pastikan tidak kosong dan 'Kursi Lipat' ada di hasil
        self.assertTrue(len(recs) > 0)
        found = any(r['name'] == 'Kursi Lipat' for r in recs)
        self.assertTrue(found)

    def testGetUpsellManualMaxVariantStock(self):
        """
        Input: productId (Kursi Biasa), quantity = 100.
        Skenario: Kursi VIP punya 2 varian, masing-masing stok 50 dan 70 (total 120). 
        Karena tidak ada yang satuan >= 100, produk ini dilewati. 
        Lalu sistem fallback mengecek target berikutnya, yaitu Kursi VVIP (varian punya stok 100).
        Expected Output: Rekomendasi yang muncul adalah Kursi VVIP, bukan Kursi VIP.
        """
        recs = getUpsellingRecommendations(
            productId=self.productBase2.id,
            startDate=self.startDate,
            endDate=self.endDate,
            quantity=100
        )
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]['productName'], 'Kursi VVIP')
        self.assertEqual(recs[0]['availableStock'], 100)

        # Tapi kalau quantity = 50, harusnya direkomendasikan Kursi VIP karena max stoknya 70 (>= 50)
        recs2 = getUpsellingRecommendations(
            productId=self.productBase2.id,
            startDate=self.startDate,
            endDate=self.endDate,
            quantity=50
        )
        self.assertEqual(len(recs2), 1)
        self.assertEqual(recs2[0]['productName'], 'Kursi VIP')
        self.assertEqual(recs2[0]['availableStock'], 70)
