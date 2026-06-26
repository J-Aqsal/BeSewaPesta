from django.db import models


class Category(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    photo = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.IntegerField()
    price_unit = models.CharField(max_length=20, blank=True, null=True)
    total_stock = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.name


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name='galleries')
    image_url = models.TextField()
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    product_variant_combination = models.ForeignKey('ProductVariantCombination', on_delete=models.DO_NOTHING, blank=True, null=True)

    class Meta:
        db_table = 'product_galleries'


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name='specifications')
    specification = models.TextField()

    class Meta:
        db_table = 'product_specifications'


class VariantType(models.Model):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name='variant_types')
    name = models.CharField(max_length=100)
    is_required = models.BooleanField(default=True)
    is_upsell_dimension = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'variant_types'
        unique_together = (('product', 'name'),)

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class VariantOption(models.Model):
    variant_type = models.ForeignKey(VariantType, on_delete=models.DO_NOTHING, related_name='options')
    value = models.CharField(max_length=100)
    price_modifier = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'variant_options'
        unique_together = (('variant_type', 'value'),)

    def __str__(self):
        return f"{self.variant_type.name}: {self.value}"


class ProductVariantCombination(models.Model):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name='variant_combinations')
    stock = models.IntegerField(default=0)
    price = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_variant_combinations'


class ProductVariantCombinationOption(models.Model):
    product_variant_combination = models.ForeignKey(ProductVariantCombination, on_delete=models.DO_NOTHING, related_name='combination_options')
    variant_option = models.ForeignKey(VariantOption, on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'product_variant_combination_options'


class TagGroup(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tag_groups'

    def __str__(self):
        return self.name


class Tag(models.Model):
    group = models.ForeignKey(TagGroup, on_delete=models.CASCADE, related_name='tags', null=True, blank=True)
    name = models.CharField(unique=True, max_length=100)
    label = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tags'

    def __str__(self):
        return self.name


class ProductTag(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    weight = models.FloatField(default=0.0)

    class Meta:
        db_table = 'product_tags'
        unique_together = (('product', 'tag'),)


class UpsellRelation(models.Model):
    source_product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name='upsell_sources', blank=True, null=True)
    source_variant = models.ForeignKey(VariantOption, on_delete=models.DO_NOTHING, related_name='upsell_variant_sources', blank=True, null=True)
    target_product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name='upsell_targets', blank=True, null=True)
    target_variant = models.ForeignKey(VariantOption, on_delete=models.DO_NOTHING, related_name='upsell_variant_targets', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'upsell_relations'


class ProductUpsellRelation(models.Model):
    source_product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name='product_upsell_sources')
    target_product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, related_name='product_upsell_targets')

    class Meta:
        db_table = 'product_upsell_relations'


class ExpTagGroup(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exp_tag_groups'

    def __str__(self):
        return self.name


class ExpTag(models.Model):
    group = models.ForeignKey(ExpTagGroup, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(unique=True, max_length=100)
    label = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exp_tags'

    def __str__(self):
        return self.name


class ExpProductTag(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='exp_product_tags')
    tag = models.ForeignKey(ExpTag, on_delete=models.CASCADE)
    weight = models.FloatField(default=0.0)

    class Meta:
        db_table = 'exp_product_tags'
        unique_together = (('product', 'tag'),)

