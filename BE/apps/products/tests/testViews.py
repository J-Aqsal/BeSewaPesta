from rest_framework.test import APITestCase
from apps.products.models import Category, Product
from utils.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE, SUCCESS_CODE
from django.utils import timezone
from datetime import timedelta

class ProductAPIViewTest(APITestCase):
    def setUp(self):
        self.startDate = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT10:00:00Z')
        self.endDate = (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT10:00:00Z')
        
        self.category = Category.objects.create(name='Tenda')
        self.product = Product.objects.create(
            name='Tenda Dome',
            price=50000,
            price_unit='hari',
            total_stock=10,
            category=self.category
        )

    def testGetCatalogSuccess(self):
        """
        Input: POST request ke `/api/products/` dengan `startDate` dan `endDate`.
        Skenario: Mengambil data seluruh katalog barang pada rentang tanggal sewa tertentu untuk melihat stok asli yang masih tersedia.
        Expected Output: Status 200 OK, `success` bernilai True, dan mengembalikan array berisi produk (Tenda Dome).
        """
        data = {
            "startDate": self.startDate,
            "endDate": self.endDate
        }
        
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        
        res_data = response.json()['data']
        self.assertGreaterEqual(len(res_data), 1)
        self.assertEqual(res_data[0]['name'], 'Tenda Dome')

    def testGetProductDetailSuccess(self):
        """
        Input: POST request ke `/api/products/detail/` membawa `idProduct`, `startDate`, dan `endDate`.
        Skenario: Mengambil detail lengkap suatu produk (termasuk galeri foto, spesifikasi, dan variannya).
        Expected Output: Status 200 OK, mengembalikan objek detail lengkap dari produk terkait.
        """
        data = {
            "idProduct": self.product.id,
            "startDate": self.startDate,
            "endDate": self.endDate
        }
        
        response = self.client.post('/api/products/detail/', data, format='json')
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['productName'], 'Tenda Dome')

    def testGetProductDetailMissingId(self):
        """
        Input: POST request ke `/api/products/detail/` HANYA membawa tanggal sewa tanpa menyertakan `idProduct`.
        Skenario: Payload JSON dari client / frontend cacat.
        Expected Output: Status 400 Bad Request, dengan pesan peringatan "idProduct required".
        """
        data = {
            "startDate": self.startDate,
            "endDate": self.endDate
        }
        
        response = self.client.post('/api/products/detail/', data, format='json')
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['message'], "idProduct required")

    def testGetProductDetailNotFound(self):
        """
        Input: POST request berisi `idProduct` bodong yang tidak ada di DB (misal 999).
        Skenario: User memasukkan URL produk yang salah atau produk telah dihapus oleh admin.
        Expected Output: Status 404 Not Found, memastikan sistem stabil dan memberikan info produk tidak ditemukan.
        """
        data = {
            "idProduct": 999,
            "startDate": self.startDate,
            "endDate": self.endDate
        }
        
        response = self.client.post('/api/products/detail/', data, format='json')
        self.assertEqual(response.status_code, NOT_FOUND_CODE)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['message'], "Product not found")
