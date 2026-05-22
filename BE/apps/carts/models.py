# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Carts(models.Model):
    guest_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    rental_start = models.DateTimeField(blank=True, null=True)
    rental_end = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'carts'


class CartItems(models.Model):
    cart = models.ForeignKey(Carts, models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('products.Products', models.DO_NOTHING, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    product_variant_combination = models.ForeignKey('products.ProductVariantCombinations', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cart_items'
