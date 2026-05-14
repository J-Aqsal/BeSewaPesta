# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class CartItemVariants(models.Model):
    cart_item = models.ForeignKey('CartItems', models.DO_NOTHING, blank=True, null=True)
    variant_option = models.ForeignKey('VariantOptions', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cart_item_variants'


class CartItems(models.Model):
    cart = models.ForeignKey('Carts', models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('Products', models.DO_NOTHING, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    rental_start = models.DateTimeField(blank=True, null=True)
    rental_end = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cart_items'


class Carts(models.Model):
    guest_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'carts'


class Categories(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'categories'


class Contexts(models.Model):
    slug = models.CharField(unique=True, max_length=100)
    label = models.CharField(max_length=150)
    group_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contexts'


class OrderItemVariants(models.Model):
    order_item = models.ForeignKey('OrderItems', models.DO_NOTHING, blank=True, null=True)
    variant_option = models.ForeignKey('VariantOptions', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_item_variants'


class OrderItems(models.Model):
    order = models.ForeignKey('Orders', models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('Products', models.DO_NOTHING, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    rental_start = models.DateTimeField(blank=True, null=True)
    rental_end = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_items'


class OrderStatuses(models.Model):
    code = models.CharField(unique=True, max_length=50, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_statuses'


class Orders(models.Model):
    guest_id = models.CharField(max_length=255, blank=True, null=True)
    total_price = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    status = models.ForeignKey(OrderStatuses, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'


class ProductContexts(models.Model):
    pk = models.CompositePrimaryKey('product_id', 'context_id')
    product = models.ForeignKey('Products', models.DO_NOTHING)
    context = models.ForeignKey(Contexts, models.DO_NOTHING)
    weight = models.FloatField()

    class Meta:
        managed = False
        db_table = 'product_contexts'


class ProductSpecifications(models.Model):
    product = models.ForeignKey('Products', models.DO_NOTHING)
    specification = models.TextField()

    class Meta:
        managed = False
        db_table = 'product_specifications'


class Products(models.Model):
    name = models.CharField(max_length=200)
    photo = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    price_unit = models.CharField(max_length=20, blank=True, null=True)
    total_stock = models.IntegerField()
    category = models.ForeignKey(Categories, models.DO_NOTHING)
    description_embedding = models.TextField(blank=True, null=True)
    embedding_updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products'


class VariantOptions(models.Model):
    variant_type = models.ForeignKey('VariantTypes', models.DO_NOTHING)
    value = models.CharField(max_length=100)
    price_modifier = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'variant_options'
        unique_together = (('variant_type', 'value'),)


class VariantTypes(models.Model):
    product = models.ForeignKey(Products, models.DO_NOTHING)
    name = models.CharField(max_length=100)
    is_required = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'variant_types'
        unique_together = (('product', 'name'),)
