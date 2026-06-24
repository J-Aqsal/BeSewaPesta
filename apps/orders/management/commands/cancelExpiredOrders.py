from django.core.management.base import BaseCommand
from apps.orders.repo import cancelExpiredOrdersRepo

class Command(BaseCommand):
    help = 'Cancels pending orders that have not been paid for more than 24 hours'

    def handle(self, *args, **kwargs):
        count = cancelExpiredOrdersRepo(hoursThreshold=24)
        self.stdout.write(self.style.SUCCESS(f'Successfully cancelled {count} expired pending orders.'))
