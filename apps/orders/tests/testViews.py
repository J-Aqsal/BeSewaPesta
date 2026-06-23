from rest_framework.test import APITestCase
from apps.products.models import Category, Product
from apps.carts.models import Cart, CartItem
from apps.orders.models import Order, OrderStatus, OrderItem
from utils.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE, SUCCESS_CODE
from django.utils import timezone
from datetime import timedelta
import uuid

class OrderAPIViewTest(APITestCase):
    def setUp(self):
        self.guestId = str(uuid.uuid4())
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
        
        self.pendingStatus = OrderStatus.objects.create(id=1, code='PENDING', name='Pending Payment')

    def _setup_cart(self):
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
        return cart

    def testPostCheckoutSuccess(self):
        """
        Input: POST request ke endpoint checkout berisi guestId dan data pengiriman (nama, hp, alamat, kota).
        Skenario: User memiliki cart dan melakukan checkout untuk menyelesaikan pesanan.
        Expected Output: Status 200 OK, `success` bernilai True, order dibuat, dan mengembalikan `paymentDeadline` tepat 24 jam dari sekarang.
        """
        self._setup_cart()
        data = {
            "guestId": self.guestId,
            "recipientName": "Budi",
            "phoneNumber": "08123456789",
            "shippingAddress": "Jl. Kemerdekaan",
            "city": "jakarta"
        }
        
        response = self.client.post('/api/orders/', data, format='json')
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        self.assertIn("paymentDeadline", response.json()['data'])

    def testPostCheckoutMissingFields(self):
        """
        Input: POST request ke endpoint checkout tanpa field yang diwajibkan (misal: city hilang).
        Skenario: Payload frontend tidak komplit.
        Expected Output: Status 400 Bad Request, dengan pesan error validasi.
        """
        self._setup_cart()
        data = {
            "guestId": self.guestId,
            "recipientName": "Budi",
            "phoneNumber": "08123"
        }
        
        response = self.client.post('/api/orders/', data, format='json')
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)
        self.assertFalse(response.json()['success'])
        self.assertEqual(response.json()['message'], "Missing required checkout information")

    def testGetCheckoutData(self):
        """
        Input: GET request ke `/api/orders/checkout/` membawa guestId.
        Skenario: Endpoint khusus untuk mengambil data deadline pembayaran setelah checkout berhasil.
        Expected Output: Status 200 OK, mengembalikan `totalRentalAmount`, `shippingCost`, dan kalkulasi `paymentDeadline` yang benar (24h).
        """
        order = Order.objects.create(
            guest_id=self.guestId,
            total_price=300000,
            shipping_cost=100000,
            status=self.pendingStatus,
            rental_start=self.startDate,
            rental_end=self.endDate,
            created_at=timezone.now(),
            recipient_name='Budi',
            phone_number='08123456789',
            shipping_address='Jl. Kemerdekaan',
            city='jakarta'
        )
        # Create OrderItem to prevent 404 in checkoutDataService (because it might do inner join)
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=300000
        )
        
        response = self.client.get(f"/api/orders/checkout-data/?guestId={self.guestId}")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        
        data = response.json()['data']
        self.assertIn("paymentDeadline", data)
        self.assertEqual(data['shippingCost'], 100000)

    def testGetShippingCost(self):
        """
        Input: GET request ke `/api/orders/shipping/` dengan guestId dan nama kota.
        Skenario: Cek ongkos kirim berdasarkan keranjang belanja (cart) yang dimiliki.
        Expected Output: Mengembalikan nilai `shippingCost` yang sesuai dari perhitungan di service.
        """
        self._setup_cart()
        response = self.client.get(f"/api/orders/shipping/?guestId={self.guestId}&city=jakarta")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertIn('shippingCost', response.json()['data'])
