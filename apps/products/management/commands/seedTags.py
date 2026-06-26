import json
import os
from django.core.management.base import BaseCommand
from apps.products.models import Product, TagGroup, Tag, ProductTag

class Command(BaseCommand):
    help = 'Seeding Tags and Weights from JSON files into the main tables'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting seeding process for main tags...')

        metaTagsPath = 'meta_tags_grouped.json'
        weightsPath = 'product_tags_weights.json'

        if not os.path.exists(metaTagsPath):
            self.stderr.write(f'File {metaTagsPath} not found!')
            return
            
        if not os.path.exists(weightsPath):
            self.stderr.write(f'File {weightsPath} not found!')
            return

        # 1. Clean existing data
        self.stdout.write('Cleaning existing main tag data...')
        ProductTag.objects.all().delete()
        Tag.objects.all().delete()
        TagGroup.objects.all().delete()

        # 2. Seed Groups and Tags
        self.stdout.write('Seeding Tag Groups and Tags...')
        with open(metaTagsPath, 'r', encoding='utf-8') as f:
            groupedData = json.load(f)

        tagNameToId = {}
        for groupItem in groupedData:
            groupName = groupItem.get('groupName') or groupItem.get('group_name')
            group = TagGroup.objects.create(name=groupName)
            for tagItem in groupItem.get('tags', []):
                tag = Tag.objects.create(
                    group=group,
                    name=tagItem['name'],
                    label=tagItem['label']
                )
                tagNameToId[tag.name] = tag

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {TagGroup.objects.count()} groups and {Tag.objects.count()} tags.'))

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
                
                mainTag = tagNameToId.get(tagName)
                if mainTag:
                    ProductTag.objects.create(
                        product=product,
                        tag=mainTag,
                        weight=weight
                    )
                    productTagsCreated += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {productTagsCreated} Product-Tag relationships with weights.'))
        
        if missingProducts:
            self.stdout.write(self.style.WARNING(f'Warning: {len(missingProducts)} products in JSON were not found in database: {", ".join(missingProducts)}'))
            
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))
