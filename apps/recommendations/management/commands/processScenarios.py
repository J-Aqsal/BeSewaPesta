import json
import os
from collections import defaultdict
import math
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Proses master_scenario.json untuk generate tags dan product weights'

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        scenario_file = os.path.join(base_dir, 'master_scenario.json')
        meta_tags_file = os.path.join(base_dir, 'meta_tags.json')
        product_weights_file = os.path.join(base_dir, 'product_tags_weights.json')
        
        if not os.path.exists(scenario_file):
            self.stdout.write(self.style.ERROR(f"Error: {scenario_file} not found."))
            return

        with open(scenario_file, 'r', encoding='utf-8') as f:
            scenarios = json.load(f)

        product_tags_map = defaultdict(set)
        all_tags_set = set()
        product_category_map = {}

        for scenario in scenarios:
            for item in scenario.get('cart', []):
                name = item.get('name')
                tags = item.get('tags', [])
                category = item.get('category')
                if name:
                    product_tags_map[name].update(tags)
                    all_tags_set.update(tags)
                    if category:
                        product_category_map[name] = category
            
            for item in scenario.get('recommendations', []):
                name = item.get('name')
                tags = item.get('tags', [])
                category = item.get('category')
                if name:
                    product_tags_map[name].update(tags)
                    all_tags_set.update(tags)
                    if category:
                        product_category_map[name] = category

        self.stdout.write(f"\nBerhasil memproses {len(product_tags_map)} produk unik dan {len(all_tags_set)} tag unik.")

        total_products = len(product_tags_map)
        document_frequency = defaultdict(int)
        for tags in product_tags_map.values():
            for tag in tags:
                document_frequency[tag] += 1

        meta_tags = []
        for tag in sorted(list(all_tags_set)):
            meta_tags.append({
                "name": tag,
                "count": document_frequency[tag]
            })
            
        meta_tags.sort(key=lambda x: (-x['count'], x['name']))

        with open(meta_tags_file, 'w', encoding='utf-8') as f:
            json.dump(meta_tags, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f"Generated {meta_tags_file}"))

        product_weights_list = []

        for name, tags_set in product_tags_map.items():
            tags = list(tags_set)
            tag_count = len(tags)
            
            if tag_count == 0:
                product_weights_list.append({
                    "name": name,
                    "tags": []
                })
                continue

            raw_weights = {}
            for tag in tags:
                TF = 1.0 / tag_count
                IDF = math.log(total_products / document_frequency[tag]) if document_frequency[tag] > 0 else 0
                
                TF_IDF = TF * IDF
                raw_weights[tag] = TF_IDF

            total_weight = sum(raw_weights.values())
            
            product_tags_with_weights = []
            if total_weight > 0:
                for tag, weight in raw_weights.items():
                    normalized_weight = round(weight / total_weight, 4)
                    product_tags_with_weights.append({
                        "name": tag,
                        "weight": normalized_weight
                    })
            else:
                
                for tag in tags:
                    product_tags_with_weights.append({
                        "name": tag,
                        "weight": round(1.0 / tag_count, 4)
                    })
            
            
            product_tags_with_weights.sort(key=lambda x: x['weight'], reverse=True)

            product_weights_list.append({
                "name": name,
                "tags": product_tags_with_weights
            })

        with open(product_weights_file, 'w', encoding='utf-8') as f:
            json.dump(product_weights_list, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f"Generated {product_weights_file}"))


        self.evaluate_scenarios(scenarios, product_weights_list, product_category_map)

    def evaluate_scenarios(self, scenarios, product_weights_list, product_category_map):
        self.stdout.write("\n--- Evaluasi Skenario (Weighted Jaccard) ---")
        
        pw_dict = {}
        all_tags = set()
        for p in product_weights_list:
            w_dict = {t['name']: t['weight'] for t in p['tags']}
            pw_dict[p['name']] = w_dict
            all_tags.update(w_dict.keys())
            
        total_scenarios = len(scenarios)
        perfect_matches = 0
        total_hits = 0
        total_ground_truth = 0
        
        failed_scenarios = []
        
        for i, scenario in enumerate(scenarios, 1):
            cart_items = [item['name'] for item in scenario.get('cart', []) if 'name' in item]
            ground_truth = [item['name'] for item in scenario.get('recommendations', []) if 'name' in item]
            cart_categories = {product_category_map.get(item, "") for item in cart_items}
            
            cart_profile = defaultdict(float)
            for item in cart_items:
                if item in pw_dict:
                    for tag, w in pw_dict[item].items():
                        cart_profile[tag] += w
                        
            scores = []
            for p_name, p_weights in pw_dict.items():
                if p_name in cart_items:
                    continue
                if product_category_map.get(p_name, "") in cart_categories:
                    continue
                    
                intersection = 0.0
                union = 0.0
                for tag in all_tags:
                    cw = cart_profile.get(tag, 0.0)
                    pw = p_weights.get(tag, 0.0)
                    intersection += min(cw, pw)
                    union += max(cw, pw)
                    
                score = intersection / union if union > 0 else 0
                scores.append((p_name, score))
                
            scores.sort(key=lambda x: x[1], reverse=True)
            top_5_predicted = [x[0] for x in scores[:5]]
            
            hits = set(top_5_predicted) & set(ground_truth)
            total_hits += len(hits)
            total_ground_truth += len(ground_truth)
            
            if len(hits) > 0:
                perfect_matches += 1
            else:
                failed_scenarios.append({
                    "scenario": scenario.get('scenarioName', f'Scenario {i}'),
                    "cart": cart_items,
                    "expected": ground_truth,
                    "predicted": top_5_predicted
                })
                
        self.stdout.write(f"Total Skenario: {total_scenarios}")
        self.stdout.write(f"Skenario dengan minimal 1 tebakan benar (dalam Top 5): {perfect_matches} dari {total_scenarios} ({(perfect_matches/total_scenarios*100) if total_scenarios > 0 else 0:.1f}%)")
        self.stdout.write(f"Total item rekomendasi yang berhasil tertebak: {total_hits} dari {total_ground_truth} ({(total_hits/total_ground_truth*100) if total_ground_truth > 0 else 0:.1f}%)")
        
        if failed_scenarios:
            self.stdout.write("\nDetail Skenario Gagal (0 tebakan benar):")
            for fail in failed_scenarios:
                self.stdout.write(f"- {fail['scenario']}")
                self.stdout.write(f"  Cart: {fail['cart']}")
                self.stdout.write(f"  Expected: {fail['expected']}")
                self.stdout.write(f"  Predicted Top 5: {fail['predicted']}")
        self.stdout.write("--------------------------------------------\n")
