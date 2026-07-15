import json
import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Convert master_scenario.csv to master_scenario.json'

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        input_file = os.path.join(base_dir, 'master_scenario.csv')
        output_file = os.path.join(base_dir, 'master_scenario.json')

        if not os.path.exists(input_file):
            self.stdout.write(self.style.ERROR(f"Error: {input_file} not found."))
            return

        scenarios_dict = {}

        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                s_id = int(row['scenarioId']) if row['scenarioId'].isdigit() else row['scenarioId']
                s_name = row['scenarioName']
                item_type = row['type']
                item_name = row['itemName']
                item_category = row['itemCategory']
                tags_str = row['tags']
                reason = row['reason']

                tags = [tag.strip() for tag in tags_str.split(',')] if tags_str.strip() else []

                if s_id not in scenarios_dict:
                    scenarios_dict[s_id] = {
                        "scenarioId": s_id,
                        "scenarioName": s_name,
                        "cart": [],
                        "recommendations": []
                    }
                
                item_data = {
                    "name": item_name,
                    "category": item_category,
                    "tags": tags
                }
                
                if item_type == 'cart':
                    scenarios_dict[s_id]["cart"].append(item_data)
                elif item_type == 'recommendation':
                    if reason:
                        item_data["reason"] = reason
                    scenarios_dict[s_id]["recommendations"].append(item_data)

        data = list(scenarios_dict.values())

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"Berhasil mengkonversi master_scenario.csv ke master_scenario.json"))
