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

def calculate_available_stock_for_combinations(product_id, combination_ids, start_date, end_date):
    combination_ids = list(combination_ids)
    if not combination_ids:
        return {}

    total_stock_rows = (
        ProductVariantCombinations.objects.filter(product_id=product_id, id__in=combination_ids)
        .values("id")
        .annotate(total_stock=Sum("stock"))
    )
    total_stock_map = {
        row["id"]: int(row["total_stock"] or 0)
        for row in total_stock_rows
    }

    used_stock_rows = (
        OrderItems.objects.filter(
            product_id=product_id,
            product_variant_combination_id__in=combination_ids,
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
        .values("product_variant_combination_id")
        .annotate(used_stock=Sum("quantity"))
    )
    used_stock_map = {
        row["product_variant_combination_id"]: int(row["used_stock"] or 0)
        for row in used_stock_rows
    }

    return {
        combination_id: int(total_stock_map.get(combination_id, 0) - used_stock_map.get(combination_id, 0))
        for combination_id in combination_ids
    }


def calculate_price_range(product, prices_list):
    if prices_list:
        price_min_val = min(prices_list)
        price_max_val = max(prices_list)
        # ubah ke int jika merupakan bilangan bulat
        price_min_val = int(price_min_val) if float(price_min_val).is_integer() else float(price_min_val)
        price_max_val = int(price_max_val) if float(price_max_val).is_integer() else float(price_max_val)
        return {"min": price_min_val, "max": price_max_val}
    else:
        # Fallback ke product price
        p = getattr(product, "price", None) or 0
        p_val = int(p) if float(p).is_integer() else float(p)
        return {"min": p_val, "max": p_val}
