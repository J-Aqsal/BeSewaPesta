from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, timezone as dt_timezone
import uuid

from apps.products.models import Category, Product
from apps.carts.models import Cart, CartItem
from apps.orders.models import Order, OrderStatus
from apps.orders.services import (
    calculateShippingCostService,
    getRentalSummaryService,
    processCheckout,
    checkoutDataService,
    updateOrderStatusService,
    getOrderDetail
)

class OrderServicesTest(TestCase):
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
        self.paidStatus = OrderStatus.objects.create(id=2, code='PAID', name='Payment Verified')

    def _setup_cart(self):
        cart = Cart.objects.create(
            guest_id=self.guestId,
            rental_start=self.startDate,
            rental_end=self.endDate
        )
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2,
            notes='Tolong packing rapi'
        )
        return cart

    def testCalculateShippingCost(self):
        """
        Input: Subtotal harga sewa dan nama kota.
        Skenario: Mengetes ongkir berdasarkan kombinasi harga dan kota sesuai aturan di service.
        Expected Output: Ongkir yang dikalkulasi bernilai benar (contoh: subtotal < 500k di depok = 500.000).
        """
        self.assertEqual(calculateShippingCostService(400000, 'depok'), 500000)
        self.assertEqual(calculateShippingCostService(600000, 'jakarta'), 300000)
        self.assertEqual(calculateShippingCostService(1200000, 'bogor'), 500000)

    def testGetRentalSummary(self):
        """
        Input: guestId yang memiliki keranjang belanja.
        Skenario: Menghitung total durasi sewa, total quantity, total biaya harian, total biaya keseluruhan, dan minimal DP.
        Expected Output: Summary berisi kalkulasi yang akurat (contoh DP = 50% dari total).
        """
        self._setup_cart()
        summary = getRentalSummaryService(self.guestId)
        self.assertIsNotNone(summary)
        self.assertEqual(summary['totalQuantity'], 2)
        self.assertEqual(summary['totalPricePerDay'], 100000) # 2 * 50k
        self.assertEqual(summary['totalDays'], 2)
        self.assertEqual(summary['totalRentalAmount'], 200000)
        self.assertEqual(summary['downPayment'], 100000)

    def testProcessCheckoutSuccess(self):
        """
        Input: guestId, informasi alamat pengiriman, kontak.
        Skenario: Proses mengubah keranjang (cart) menjadi pesanan (order) yang fix.
        Expected Output: Order terbuat di DB, status "success" True, dan nilai `paymentDeadline` yang dihitung tepat 24 jam ke depan.
        """
        self._setup_cart()
        result = processCheckout(
            guestId=self.guestId,
            recipientName='Budi',
            phoneNumber='08123456789',
            shippingAddress='Jalan A',
            city='jakarta'
        )
        
        self.assertTrue(result['success'])
        orderId = result['data']['orderId']
        
        # Keranjang belanja seharusnya dihapus otomatis setelah checkout sukses
        self.assertFalse(Cart.objects.filter(guest_id=self.guestId).exists())
        
        order = Order.objects.get(id=orderId)
        self.assertEqual(order.recipient_name, 'Budi')
        self.assertEqual(order.city, 'jakarta')
        order_items = order.order_items.all()
        self.assertEqual(order_items.first().notes, 'Tolong packing rapi')

    def testCheckoutDataServiceDeadline(self):
        """
        Input: guestId dari user yang baru saja berhasil melakukan checkout.
        Skenario: Memvalidasi fungsi checkoutDataService yang digunakan FE untuk halaman instruksi pembayaran.
        Expected Output: Mengembalikan rincian pembayaran termasuk `paymentDeadline` yang dikalkulasi akurat = created_at + 24 jam.
        """
        self._setup_cart()
        # Lakukan checkout untuk membuat order
        processCheckout(
            guestId=self.guestId,
            recipientName='Budi',
            phoneNumber='08123456789',
            shippingAddress='Jalan A',
            city='jakarta'
        )
        
        # Ambil datanya
        data = checkoutDataService(self.guestId)
        self.assertIsNotNone(data)
        
        order = Order.objects.get(guest_id=self.guestId)
        expectedDeadline = timezone.localtime(
            order.created_at.replace(tzinfo=dt_timezone.utc) + timedelta(hours=24)
        ).strftime('%Y-%m-%dT%H:%M:%S')
        
        self.assertEqual(data['paymentDeadline'], expectedDeadline)

    def testUpdateOrderStatus(self):
        """
        Input: orderId dan ID status pesanan yang baru (misal status 2 = Payment Verified).
        Skenario: Admin mengubah status pesanan.
        Expected Output: "success" True dan status di DB berubah menjadi status yang baru.
        """
        self._setup_cart()
        processCheckout(
            guestId=self.guestId,
            recipientName='Budi',
            phoneNumber='08123456789',
            shippingAddress='Jalan A',
            city='jakarta'
        )
        order = Order.objects.get(guest_id=self.guestId)
        
        result = updateOrderStatusService(order.id, self.paidStatus.id)
        self.assertTrue(result['success'])
        
        order.refresh_from_db()
        self.assertEqual(order.status.id, self.paidStatus.id)

    def testProcessCheckoutInvalidPhoneNumberShort(self):
        """
        Input: No HP kurang dari 9 digit.
        Skenario: Pengguna mencoba checkout dengan no HP terlalu pendek.
        Expected Output: success False, pesan error panjang no HP.
        """
        self._setup_cart()
        result = processCheckout(
            guestId=self.guestId,
            recipientName='Budi',
            phoneNumber='123',
            shippingAddress='Jalan A',
            city='jakarta'
        )
        self.assertFalse(result['success'])
        self.assertIn('between 9 and 13', result['message'])

    def testProcessCheckoutInvalidPhoneNumberLong(self):
        """
        Input: No HP lebih dari 13 digit.
        Skenario: Pengguna mencoba checkout dengan no HP terlalu panjang.
        Expected Output: success False, pesan error panjang no HP.
        """
        self._setup_cart()
        result = processCheckout(
            guestId=self.guestId,
            recipientName='Budi',
            phoneNumber='081234567890123',
            shippingAddress='Jalan A',
            city='jakarta'
        )
        self.assertFalse(result['success'])
        self.assertIn('between 9 and 13', result['message'])

    def testProcessCheckoutInvalidPhoneNumberLetters(self):
        """
        Input: No HP mengandung huruf.
        Skenario: Pengguna mencoba checkout dengan no HP berhuruf.
        Expected Output: success False, pesan error khusus angka.
        """
        self._setup_cart()
        result = processCheckout(
            guestId=self.guestId,
            recipientName='Budi',
            phoneNumber='081234abc',
            shippingAddress='Jalan A',
            city='jakarta'
        )
        self.assertFalse(result['success'])
        self.assertIn('only digits', result['message'])
