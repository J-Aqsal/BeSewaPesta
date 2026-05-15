# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Products(models.Model):
    name = models.CharField(max_length=200)
    photo = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    price_unit = models.CharField(max_length=20, blank=True, null=True)
    total_stock = models.IntegerField()
    category = models.ForeignKey('Categories', models.DO_NOTHING)
    description_embedding = models.TextField(blank=True, null=True)
    embedding_updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products'


class ProductGalleries(models.Model):
    product = models.ForeignKey(Products, models.DO_NOTHING)
    variant_option = models.ForeignKey('VariantOptions', models.DO_NOTHING, blank=True, null=True)
    image_url = models.TextField()
    display_order = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_galleries'


class VariantTypes(models.Model):
    product = models.ForeignKey(Products, models.DO_NOTHING)
    name = models.CharField(max_length=100)
    is_required = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'variant_types'
        unique_together = (('product', 'name'),)


class VariantOptions(models.Model):
    variant_type = models.ForeignKey(VariantTypes, models.DO_NOTHING)
    value = models.CharField(max_length=100)
    price_modifier = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'variant_options'
        unique_together = (('variant_type', 'value'),)


class Categories(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'categories'


class ProductVariantCombinationOptions(models.Model):
    product_variant_combination = models.ForeignKey('ProductVariantCombinations', models.DO_NOTHING)
    variant_option = models.ForeignKey(VariantOptions, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_variant_combination_options'


class ProductVariantCombinations(models.Model):
    product = models.ForeignKey(Products, models.DO_NOTHING)
    stock = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_variant_combinations'
