from django.db import models
from apps.products.models import Product, ProductVariantCombination


class Cart(models.Model):
    guest_id = models.UUIDField(unique=True)
    rental_start = models.DateTimeField(blank=True, null=True)
    rental_end = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

    def __str__(self):
        return f"Cart {self.guest_id}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.DO_NOTHING, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    product_variant_combination = models.ForeignKey(
        ProductVariantCombination, 
        on_delete=models.DO_NOTHING, 
        blank=True, 
        null=True
    )
    quantity = models.IntegerField(default=1)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart_items'

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in {self.cart.guest_id}"
