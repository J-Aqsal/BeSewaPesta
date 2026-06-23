from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from io import StringIO
import uuid
from apps.orders.models import Order, OrderStatus

class CancelExpiredOrdersCommandTest(TestCase):
    def setUp(self):
        self.statusPending = OrderStatus.objects.create(id=1, code="PENDING", name="Pending Payment")
        self.statusCancelled = OrderStatus.objects.create(id=5, code="CANCELLED", name="Cancelled")
        
        # Buat order dummy (belum 24 jam)
        self.orderBaru = Order.objects.create(
            guest_id=uuid.uuid4(),
            total_price=100000,
            status=self.statusPending,
            rental_start=timezone.now() + timedelta(days=5),
            rental_end=timezone.now() + timedelta(days=6)
        )
        
        # Buat order dummy (sudah lebih dari 24 jam)
        self.orderLama = Order.objects.create(
            guest_id=uuid.uuid4(),
            total_price=200000,
            status=self.statusPending,
            rental_start=timezone.now() + timedelta(days=5),
            rental_end=timezone.now() + timedelta(days=6)
        )
        Order.objects.filter(id=self.orderLama.id).update(created_at=timezone.now() - timedelta(hours=25))

    def testCancelExpiredOrdersCommand(self):
        """
        Skenario: Menjalankan command cancelExpiredOrders dengan order yang kedaluwarsa.
        Expected Output: Order yang lebih dari 24 jam statusnya berubah jadi CANCELED, order baru tetap PENDING.
        """
        out = StringIO()
        call_command('cancelExpiredOrders', stdout=out)
        
        self.orderBaru.refresh_from_db()
        self.orderLama.refresh_from_db()
        
        # Verifikasi hasilnya
        self.assertEqual(self.orderBaru.status.id, 1) # Tetap pending
        self.assertEqual(self.orderLama.status.id, 5) # Berubah jadi cancelled
        self.assertIn('Successfully cancelled 1 expired pending orders.', out.getvalue())
