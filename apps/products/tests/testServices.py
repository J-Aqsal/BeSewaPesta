from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.products.models import (
    Category, Product, ProductGallery, ProductSpecification, 
    VariantType, VariantOption, ProductVariantCombination, ProductVariantCombinationOption
)
from apps.products.services import getProductCatalogData, getProductDetailData

class ProductServicesTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Tenda')
        
        # Product without variant
        self.product1 = Product.objects.create(
            name='Tenda Dome',
            price=50000,
            price_unit='hari',
            total_stock=10,
            category=self.category,
            description='Tenda kuat dan tahan lama'
        )
        
        ProductSpecification.objects.create(product=self.product1, specification='Kapasitas: 4 Orang')
        ProductGallery.objects.create(product=self.product1, image_url='http://img.url/tenda.jpg', display_order=1)

        # Product with variants
        self.product2 = Product.objects.create(
            name='Kursi Lipat',
            price=10000, # Base price
            price_unit='hari',
            total_stock=0, # Computed from variants
            category=self.category
        )
        
        self.vType = VariantType.objects.create(product=self.product2, name='Warna')
        self.vOpt1 = VariantOption.objects.create(variant_type=self.vType, value='Merah')
        self.vOpt2 = VariantOption.objects.create(variant_type=self.vType, value='Biru')
        
        # Combination 1 (Merah, price 15000)
        self.comb1 = ProductVariantCombination.objects.create(product=self.product2, price=15000, stock=5)
        ProductVariantCombinationOption.objects.create(product_variant_combination=self.comb1, variant_option=self.vOpt1)
        
        # Combination 2 (Biru, price 20000)
        self.comb2 = ProductVariantCombination.objects.create(product=self.product2, price=20000, stock=2)
        ProductVariantCombinationOption.objects.create(product_variant_combination=self.comb2, variant_option=self.vOpt2)

        self.startDate = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT10:00:00Z')
        self.endDate = (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT10:00:00Z')

    def testGetProductCatalogData(self):
        """
        Input: Parameter rentang tanggal (startDate, endDate).
        Skenario: Meminta daftar semua produk (catalog) beserta status ketersediaan dan rentang harga dari variannya.
        Expected Output: Mengembalikan list berisi produk. Produk dengan varian (Kursi Lipat) akan memiliki minPrice dan maxPrice yang sesuai dengan varian termurah dan termahal.
        """
        catalog = getProductCatalogData(self.startDate, self.endDate)
        self.assertEqual(len(catalog), 2)
        
        # Find product 2 in catalog
        p2_data = next((p for p in catalog if p['id'] == self.product2.id), None)
        self.assertIsNotNone(p2_data)
        self.assertEqual(p2_data['minPrice'], 15000) # Base 10000 is ignored if combinations exist
        self.assertEqual(p2_data['maxPrice'], 20000)
        self.assertEqual(p2_data['stock'], 7) # 5 + 2
        self.assertTrue(p2_data['isAvailable'])
        
        # Find product 1 in catalog
        p1_data = next((p for p in catalog if p['id'] == self.product1.id), None)
        self.assertEqual(p1_data['minPrice'], 50000)
        self.assertEqual(p1_data['maxPrice'], 50000)
        self.assertEqual(p1_data['stock'], 10)

    def testGetProductDetailData(self):
        """
        Input: Parameter idProduct beserta rentang tanggal sewa.
        Skenario: Mengambil data mendalam suatu produk (Kursi Lipat) termasuk deskripsi, foto, spesifikasi, dan jenis variannya.
        Expected Output: Mengembalikan data detail lengkap beserta daftar variantCombinations (merah dan biru) dengan stok real-time.
        """
        detail = getProductDetailData(self.product2.id, self.startDate, self.endDate)
        
        self.assertIsNotNone(detail)
        self.assertEqual(detail['productName'], 'Kursi Lipat')
        self.assertEqual(detail['priceRange']['min'], 15000)
        self.assertEqual(detail['priceRange']['max'], 20000)
        self.assertEqual(detail['availableStock'], 7)
        
        # Cek Variant Types
        self.assertEqual(len(detail['variantTypes']), 1)
        self.assertEqual(detail['variantTypes'][0]['variantName'], 'Warna')
        
        # Cek Variant Combinations
        self.assertEqual(len(detail['variantCombinations']), 2)

    def testGetProductDetailDataNotFound(self):
        """
        Input: idProduct yang tidak ada di database (misal: 999).
        Skenario: User mengakses halaman detail barang yang sudah dihapus.
        Expected Output: Mengembalikan nilai None agar API bisa membalas dengan status 404 Not Found.
        """
        detail = getProductDetailData(999, self.startDate, self.endDate)
        self.assertIsNone(detail)
