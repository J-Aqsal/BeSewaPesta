from rest_framework.test import APITestCase
from apps.products.models import Category, Product
from apps.carts.models import Cart, CartItem
from apps.orders.models import Order, OrderStatus
from utils.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE, SUCCESS_CODE
from django.utils import timezone
import uuid

class CartAPIViewTest(APITestCase):
    def setUp(self):
        self.url = '/api/carts/'
        self.guestId = str(uuid.uuid4())
        self.startDate = '2026-10-10T10:00:00Z'
        self.endDate = '2026-10-15T10:00:00Z'

        # Buat data asli di database test_sewaPesta
        self.category = Category.objects.create(name='Tenda')
        self.product = Product.objects.create(
            name='Tenda Dome',
            price=50000,
            price_unit='hari',
            total_stock=10,
            category=self.category
        )
        self.productId = self.product.id
        self.pendingStatus = OrderStatus.objects.create(id=1, name='Pending Payment')

    def testGetCartSuccess(self):
        """
        Input: GET request dengan query parameter `guestId`.
        Skenario: Cart dan item sudah ada di database untuk guestId tersebut.
        Expected Output: Status 200 OK, `success` bernilai True, mengembalikan detail cart dan daftar items.
        """
        cart = Cart.objects.create(
            guest_id=self.guestId,
            rental_start=self.startDate,
            rental_end=self.endDate
        )
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )

        response = self.client.get(f"{self.url}?guestId={self.guestId}")

        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['cartId'], cart.id)
        self.assertEqual(len(response.json()['data']['items']), 1)
        self.assertEqual(response.json()['data']['items'][0]['quantity'], 2)
        self.assertEqual(response.json()['data']['items'][0]['productName'], 'Tenda Dome')

    def testGetCartMissingGuestId(self):
        """
        Input: GET request tanpa query parameter `guestId`.
        Skenario: User mencoba mengambil cart tanpa memberikan ID.
        Expected Output: Status 400 Bad Request, `success` bernilai False, dengan pesan error spesifik.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['message'], "guestId is required")

    def testGetCartPendingOrder(self):
        """
        Input: GET request dengan query parameter `guestId`.
        Skenario: User memiliki order (pesanan) yang statusnya masih 'Pending Payment'.
        Expected Output: Status 400 Bad Request, mengembalikan pesan peringatan untuk menyelesaikan pembayaran terlebih dahulu.
        """
        Order.objects.create(
            guest_id=self.guestId,
            total_price=100000,
            status=self.pendingStatus,
            rental_start=self.startDate,
            rental_end=self.endDate,
            created_at=timezone.now()
        )
        
        response = self.client.get(f"{self.url}?guestId={self.guestId}")
        
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)
        self.assertEqual(response.json()['message'], "You have a pending order waiting for payment. Please complete it first.")

    def testGetCartNotFound(self):
        """
        Input: GET request dengan query parameter `guestId`.
        Skenario: Tidak ada cart sama sekali untuk guestId tersebut di database.
        Expected Output: Status 404 Not Found.
        """
        response = self.client.get(f"{self.url}?guestId={self.guestId}")
        self.assertEqual(response.status_code, NOT_FOUND_CODE)

    def testPostAddItemSuccess(self):
        """
        Input: POST request berisi `guestId`, `idProduct`, `startDate`, `endDate`, dan `quantity`.
        Skenario: User menambahkan produk baru ke dalam cart dengan stok dan field yang valid.
        Expected Output: Status 200 OK, `success` bernilai True, data disimpan ke database dan mengembalikan `cartId`.
        """
        data = {
            "guestId": self.guestId,
            "idProduct": self.productId,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "quantity": 2
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        
        cart = Cart.objects.get(guest_id=self.guestId)
        self.assertEqual(response.json()['data']['cartId'], cart.id)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 2)

    def testPostAddItemMissingFields(self):
        """
        Input: POST request hanya dengan `guestId` (field wajib lainnya hilang).
        Skenario: User mengirim payload JSON yang tidak lengkap.
        Expected Output: Status 400 Bad Request, `success` bernilai False, muncul error validasi field.
        """
        data = {
            "guestId": self.guestId,
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)
        self.assertEqual(response.json()['message'], "guestId, idProduct, startDate, and endDate are required")
        self.assertFalse(Cart.objects.filter(guest_id=self.guestId).exists())

    def testPatchUpdateQuantitySuccess(self):
        """
        Input: PATCH request berisi `guestId`, `idCartItem`, dan `quantity` baru.
        Skenario: User memperbarui jumlah (quantity) barang yang sudah ada di cart.
        Expected Output: Status 200 OK, `success` bernilai True, dan quantity di database berubah.
        """
        cart = Cart.objects.create(
            guest_id=self.guestId,
            rental_start=self.startDate,
            rental_end=self.endDate
        )
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        data = {
            "guestId": self.guestId,
            "idCartItem": item.id,
            "quantity": 3
        }
        
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

    def testDeleteRemoveItemSuccess(self):
        """
        Input: DELETE request berisi `guestId` dan `idCartItem`.
        Skenario: User menghapus salah satu barang dari cart.
        Expected Output: Status 200 OK, `success` bernilai True, dan CartItem benar-benar terhapus dari database.
        """
        cart = Cart.objects.create(
            guest_id=self.guestId,
            rental_start=self.startDate,
            rental_end=self.endDate
        )
        item = CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        data = {
            "guestId": self.guestId,
            "idCartItem": item.id
        }
        
        response = self.client.delete(self.url, data, format='json')
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())
