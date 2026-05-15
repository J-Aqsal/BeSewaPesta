# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Orders(models.Model):
    guest_id = models.CharField(max_length=255, blank=True, null=True)
    total_price = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    status = models.ForeignKey('OrderStatuses', models.DO_NOTHING, blank=True, null=True)
    rental_start = models.DateTimeField(blank=True, null=True)
    rental_end = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'


class OrderItems(models.Model):
    order = models.ForeignKey(Orders, models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('products.Products', models.DO_NOTHING, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    product_variant_combination = models.ForeignKey('products.ProductVariantCombinations', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_items'


class OrderStatuses(models.Model):
    code = models.CharField(unique=True, max_length=50, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_statuses'
