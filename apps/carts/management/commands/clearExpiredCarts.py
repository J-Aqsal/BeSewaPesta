from django.core.management.base import BaseCommand
from apps.carts.services import expireInactiveCartsService

class Command(BaseCommand):
    help = 'Clears inactive carts that have not been updated for more than 7 days (168 hours)'

    def handle(self, *args, **kwargs):
        # 7 days = 168 hours
        result = expireInactiveCartsService(hoursThreshold=168)
        self.stdout.write(self.style.SUCCESS(result['message']))
