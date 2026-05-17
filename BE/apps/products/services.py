from datetime import timedelta

from django.db.models import Q, Sum
from django.utils import timezone

from apps.orders.models import OrderItems
from .models import VariantTypes, ProductVariantCombinationOptions, ProductVariantCombinations

"""
service.py berisi fungsi-fungsi yang mengandung logika bisnis terkait produk, 
seperti perhitungan stok yang tersedia berdasarkan pesanan yang sudah ada. 
Fungsi calculate_available_stock menghitung stok yang tersedia untuk suatu produk dalam 
rentang tanggal tertentu dengan mempertimbangkan pesanan yang sedang aktif dan pesanan 
yang baru saja selesai.
"""

ACTIVE_STATUSES = [
    "PENDING",
    "DP",
    "PAID"
]


def calculate_available_stock(
    product,
    start_date,
    end_date
):

    has_variant = VariantTypes.objects.filter(
        product=product
    ).exists()

    if not has_variant:

        total_stock = product.total_stock

        used_stock = (
            OrderItems.objects.filter(
                product=product,

                order__rental_start__lt=end_date,
                order__rental_end__gt=start_date
            )
            .filter(
                Q(
                    order__status__code__in=ACTIVE_STATUSES
                )
                |
                Q(
                    order__status__code="COMPLETED",
                    order__rental_end__gte=(
                        timezone.now() - timedelta(hours=24)
                    )
                )
            )
            .aggregate(
                total=Sum("quantity")
            )["total"]
            or 0
        )
        
        return total_stock - used_stock

    total_stock = (
        product.productvariantcombinations_set.aggregate(
            total=Sum("stock")
        )["total"]
        or 0
    )

    used_stock = (
        OrderItems.objects.filter(
            product=product,

            order__rental_start__lt=end_date,
            order__rental_end__gt=start_date,

            product_variant_combination__isnull=False
        )
        .filter(
            Q(
                order__status__code__in=ACTIVE_STATUSES
            )
            |
            Q(
                order__status__code="COMPLETED",
                order__rental_end__gte=(
                    timezone.now() - timedelta(hours=24)
                )
            )
        )
        .aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )
    return total_stock - used_stock


def calculate_available_stock_for_variant_option(product_id, variant_option_id, start_date, end_date):
    combo_ids = ProductVariantCombinationOptions.objects.filter(
        variant_option_id=variant_option_id
    ).values_list("product_variant_combination_id", flat=True)

    if not combo_ids:
        return 0

    # Total stock
    total_stock = (
        ProductVariantCombinations.objects.filter(id__in=combo_ids).aggregate(
            total=Sum("stock")
        )["total"]
        or 0
    )

    # Used stock
    used_stock = (
        OrderItems.objects.filter(
            product_id=product_id,
            product_variant_combination_id__in=combo_ids,
            order__rental_start__lt=end_date,
            order__rental_end__gt=start_date,
        )
        .filter(
            Q(order__status__code__in=ACTIVE_STATUSES)
            | Q(
                order__status__code="COMPLETED",
                order__rental_end__gte=(timezone.now() - timedelta(hours=24)),
            )
        )
        .aggregate(total=Sum("quantity"))["total"]
        or 0
    )

    return int(total_stock - used_stock)