from django.db import models
from apps.products.models import Product, ProductVariantCombination


class OrderStatus(models.Model):
    code = models.CharField(unique=True, max_length=50)
    name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'order_statuses'

    def __str__(self):
        return self.name


class Order(models.Model):
    guest_id = models.UUIDField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.ForeignKey(OrderStatus, on_delete=models.DO_NOTHING, related_name='orders')
    rental_start = models.DateTimeField()
    rental_end = models.DateTimeField()
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    shipping_cost = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'orders'

    def __str__(self):
        return f"Order {self.id} - {self.recipient_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.DO_NOTHING, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    product_variant_combination = models.ForeignKey(
        ProductVariantCombination, 
        on_delete=models.DO_NOTHING, 
        blank=True, 
        null=True
    )
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'order_items'

    def __str__(self):
        return f"Item {self.product.name} in Order {self.order.id}"
