import json
import os
from django.core.management.base import BaseCommand
from apps.products.models import Product, ExpTagGroup, ExpTag, ExpProductTag

class Command(BaseCommand):
    help = 'Seeding Experimental Tags and Weights from JSON files'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting seeding process for experimental tags...')

        metaTagsPath = 'meta_tags_grouped.json'
        weightsPath = 'product_tags_weights.json'

        if not os.path.exists(metaTagsPath):
            self.stderr.write(f'File {metaTagsPath} not found!')
            return
            
        if not os.path.exists(weightsPath):
            self.stderr.write(f'File {weightsPath} not found!')
            return

        # 1. Clean existing experimental data
        self.stdout.write('Cleaning existing experimental tag data...')
        ExpProductTag.objects.all().delete()
        ExpTag.objects.all().delete()
        ExpTagGroup.objects.all().delete()

        # 2. Seed Groups and Tags
        self.stdout.write('Seeding Tag Groups and Tags...')
        with open(metaTagsPath, 'r', encoding='utf-8') as f:
            groupedData = json.load(f)

        tagNameToId = {}
        for groupItem in groupedData:
            groupName = groupItem.get('groupName') or groupItem.get('group_name')
            group = ExpTagGroup.objects.create(name=groupName)
            for tagItem in groupItem.get('tags', []):
                tag = ExpTag.objects.create(
                    group=group,
                    name=tagItem['name'],
                    label=tagItem['label']
                )
                tagNameToId[tag.name] = tag

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {ExpTagGroup.objects.count()} groups and {ExpTag.objects.count()} tags.'))

        # 3. Seed Product Tags with Weights
        self.stdout.write('Seeding Product Tags with TF-IDF Weights...')
        with open(weightsPath, 'r', encoding='utf-8') as f:
            weightsData = json.load(f)

        missingProducts = []
        productTagsCreated = 0

        for item in weightsData:
            productName = item.get('name')
            if not productName:
                continue

            try:
                # Retrieve the product from DB
                product = Product.objects.get(name=productName)
            except Product.DoesNotExist:
                missingProducts.append(productName)
                continue

            for tagData in item.get('tags', []):
                tagName = tagData['name']
                weight = float(tagData['weight'])
                
                expTag = tagNameToId.get(tagName)
                if expTag:
                    ExpProductTag.objects.create(
                        product=product,
                        tag=expTag,
                        weight=weight
                    )
                    productTagsCreated += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {productTagsCreated} Product-Tag relationships with weights.'))
        
        if missingProducts:
            self.stdout.write(self.style.WARNING(f'Warning: {len(missingProducts)} products in JSON were not found in database: {", ".join(missingProducts)}'))
            
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
