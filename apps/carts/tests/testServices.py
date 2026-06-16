from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import uuid

from apps.products.models import Category, Product, VariantType, VariantOption, ProductVariantCombination, ProductVariantCombinationOption
from apps.carts.models import Cart, CartItem
from apps.orders.models import Order, OrderStatus
from apps.carts.services import (
    getCartDetailByGuestId,
    addItemToCart,
    removeItemFromCart,
    updateItemQuantityService,
    getExistingCategoriesService
)

class CartServicesTest(TestCase):
    def setUp(self):
        self.guestId = str(uuid.uuid4())
        self.startDate = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%dT10:00:00Z')
        self.endDate = (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT10:00:00Z')
        
        self.category = Category.objects.create(name='Tenda')
        
        # Product without variant
        self.product1 = Product.objects.create(
            name='Tenda Dome',
            price=50000,
            price_unit='hari',
            total_stock=10,
            category=self.category
        )
        
        # Product with variant
        self.product2 = Product.objects.create(
            name='Kursi Lipat',
            price=10000,
            price_unit='hari',
            total_stock=0, # Stock is determined by variants
            category=self.category
        )
        self.vType = VariantType.objects.create(product=self.product2, name='Warna')
        self.vOpt = VariantOption.objects.create(variant_type=self.vType, value='Merah')
        self.combination = ProductVariantCombination.objects.create(
            product=self.product2,
            price=15000,
            stock=5
        )
        ProductVariantCombinationOption.objects.create(
            product_variant_combination=self.combination,
            variant_option=self.vOpt
        )

        # Status Order
        self.pendingStatus = OrderStatus.objects.create(id=1, name='Pending Payment')

    def testAddItemToCartSuccessNoVariant(self):
        """
        Input: Parameter guestId, productId (produk tanpa varian), quantity (2), dan tanggal sewa.
        Skenario: Menambahkan produk biasa ke dalam cart baru. Stok mencukupi.
        Expected Output: Berhasil (`success` bernilai True), mengembalikan `cartId`, dan item tersimpan di database dengan quantity 2.
        """
        result = addItemToCart(
            guestId=self.guestId,
            productId=self.product1.id,
            combinationId=None,
            quantity=2,
            startDate=self.startDate,
            endDate=self.endDate
        )
        self.assertTrue(result['success'])
        self.assertIn('cartId', result)
        
        cart = Cart.objects.get(guest_id=self.guestId)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 2)

    def testAddItemToCartExceedStock(self):
        """
        Input: Parameter penambahan produk dengan quantity (20) yang melebihi stok tersedia (10).
        Skenario: Memastikan service menolak penambahan barang apabila stok tidak cukup.
        Expected Output: Gagal (`success` bernilai False), mengembalikan pesan error "exceeds available stock".
        """
        result = addItemToCart(
            guestId=self.guestId,
            productId=self.product1.id,
            combinationId=None,
            quantity=20, # Exceeds stock of 10
            startDate=self.startDate,
            endDate=self.endDate
        )
        self.assertFalse(result['success'])
        self.assertIn('exceeds available stock', result['message'])

    def testAddItemToCartWithPendingOrder(self):
        """
        Input: Pemanggilan fungsi addItemToCart.
        Skenario: User memiliki order (pesanan) aktif dengan status 'Pending Payment'.
        Expected Output: Ditolak (`success` bernilai False), mengembalikan pesan error "pending order" karena tidak diizinkan membuat cart baru.
        """
        Order.objects.create(
            guest_id=self.guestId,
            total_price=100000,
            status=self.pendingStatus,
            rental_start=self.startDate,
            rental_end=self.endDate,
            created_at=timezone.now()
        )
        
        result = addItemToCart(
            guestId=self.guestId,
            productId=self.product1.id,
            combinationId=None,
            quantity=1,
            startDate=self.startDate,
            endDate=self.endDate
        )
        self.assertFalse(result['success'])
        self.assertIn('pending order', result['message'])

    def testGetCartDetail(self):
        """
        Input: Memanggil getCartDetailByGuestId(guestId).
        Skenario: Mengambil rekap detail cart yang berisi 1 jenis produk sejumlah 2 unit (harga 50.000/hari).
        Expected Output: Mengembalikan detail cart, list items, dan total harga yang dikalkulasi dengan benar (100.000).
        """
        # Insert item first
        addItemToCart(
            guestId=self.guestId,
            productId=self.product1.id,
            combinationId=None,
            quantity=2,
            startDate=self.startDate,
            endDate=self.endDate
        )
        
        detail = getCartDetailByGuestId(self.guestId)
        self.assertIsNotNone(detail)
        self.assertEqual(detail['totalPrice'], 100000) # 2 * 50000
        self.assertEqual(len(detail['items']), 1)
        self.assertEqual(detail['items'][0]['productName'], 'Tenda Dome')

    def testUpdateItemQuantity(self):
        """
        Input: Memanggil updateItemQuantityService dengan quantity baru (5), lalu dengan quantity (20).
        Skenario: Mengubah kuantitas item yang sudah ada di cart. Skenario 1 valid, Skenario 2 melebihi stok.
        Expected Output: Update ke 5 berhasil, nilai di database berubah. Update ke 20 ditolak (`success` False).
        """
        add_result = addItemToCart(
            guestId=self.guestId,
            productId=self.product1.id,
            combinationId=None,
            quantity=2,
            startDate=self.startDate,
            endDate=self.endDate
        )
        cart = Cart.objects.get(guest_id=self.guestId)
        cartItemId = cart.items.first().id
        
        # Update quantity to 5
        upd_result = updateItemQuantityService(self.guestId, cartItemId, 5)
        self.assertTrue(upd_result['success'])
        
        # Verify db
        item = CartItem.objects.get(id=cartItemId)
        self.assertEqual(item.quantity, 5)
        
        # Update beyond stock (should fail)
        upd_fail = updateItemQuantityService(self.guestId, cartItemId, 20)
        self.assertFalse(upd_fail['success'])

    def testRemoveItem(self):
        """
        Input: Memanggil removeItemFromCart dengan parameter `cartItemId` dan `guestId`.
        Skenario: User menghapus salah satu item secara eksplisit dari dalam cart miliknya.
        Expected Output: Berhasil (`success` bernilai True), item tersebut benar-benar hilang dari database.
        """
        addItemToCart(
            guestId=self.guestId,
            productId=self.product1.id,
            combinationId=None,
            quantity=2,
            startDate=self.startDate,
            endDate=self.endDate
        )
        cart = Cart.objects.get(guest_id=self.guestId)
        cartItemId = cart.items.first().id
        
        # Remove item
        rm_result = removeItemFromCart(cartItemId, self.guestId)
        self.assertTrue(rm_result['success'])
        
        # Verify db
        self.assertFalse(CartItem.objects.filter(id=cartItemId).exists())
