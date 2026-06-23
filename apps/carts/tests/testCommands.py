from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from io import StringIO
import uuid
from apps.carts.models import Cart

class ClearExpiredCartsCommandTest(TestCase):
    def setUp(self):
        # Buat cart baru (kurang dari 7 hari)
        self.cartBaru = Cart.objects.create(guest_id=uuid.uuid4())
        
        # Buat cart lama (lebih dari 7 hari)
        self.cartLama = Cart.objects.create(guest_id=uuid.uuid4())
        Cart.objects.filter(id=self.cartLama.id).update(updated_at=timezone.now() - timedelta(days=8))

    def testClearExpiredCartsCommand(self):
        """
        Skenario: Menjalankan command clearExpiredCarts untuk menguji penghapusan cart kadaluarsa.
        Expected Output: Cart lama akan terhapus, cart baru tetap ada.
        """
        out = StringIO()
        call_command('clearExpiredCarts', stdout=out)
        
        # Verifikasi hasilnya
        self.assertTrue(Cart.objects.filter(id=self.cartBaru.id).exists())
        self.assertFalse(Cart.objects.filter(id=self.cartLama.id).exists())
