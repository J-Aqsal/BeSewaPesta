import json
import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Convert master_scenario.json to master_scenario.csv'

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        input_file = os.path.join(base_dir, 'master_scenario.json')
        output_file = os.path.join(base_dir, 'master_scenario.csv')

        if not os.path.exists(input_file):
            self.stdout.write(self.style.ERROR(f"Error: {input_file} not found."))
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['scenarioId', 'scenarioName', 'type', 'itemName', 'itemCategory', 'tags', 'reason'])
            
            for scenario in data:
                s_id = scenario.get('scenarioId', '')
                s_name = scenario.get('scenarioName', '')
                
                # Write Cart Items
                for item in scenario.get('cart', []):
                    tags_str = ', '.join(item.get('tags', []))
                    writer.writerow([s_id, s_name, 'cart', item.get('name', ''), item.get('category', ''), tags_str, ''])
                    
                # Write Recommendation Items
                for item in scenario.get('recommendations', []):
                    tags_str = ', '.join(item.get('tags', []))
                    reason = item.get('reason', '')
                    writer.writerow([s_id, s_name, 'recommendation', item.get('name', ''), item.get('category', ''), tags_str, reason])

        self.stdout.write(self.style.SUCCESS(f"Berhasil mengkonversi master_scenario.json ke master_scenario.csv"))
