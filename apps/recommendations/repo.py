from apps.products.models import Product, ProductUpsellRelation, ProductGallery
from django.db.models import F, OuterRef, Subquery


def getProductUpsellRelations(productId):
    first_gallery = ProductGallery.objects.filter(
        product_id=OuterRef('target_product_id')
    ).order_by('display_order', 'id')

    relations = ProductUpsellRelation.objects.filter(
        source_product_id=productId
    ).select_related('target_product').annotate(
        target_id=F('target_product_id'),
        product_name=F('target_product__name'),
        product_photo=Subquery(first_gallery.values('image_url')[:1]),
        product_price=F('target_product__price'),
        price_unit=F('target_product__price_unit'),
        total_stock=F('target_product__total_stock')
    ).values(
        'id', 'target_id', 'product_name', 'product_photo',
        'product_price', 'price_unit', 'total_stock'
    )

    results = []
    for r in relations:
        results.append({
            "id": r['id'],
            "target_product_id": r['target_id'],
            "product_name": r['product_name'],
            "product_photo": r['product_photo'],
            "product_price": r['product_price'],
            "price_unit": r['price_unit'],
            "total_stock": r['total_stock']
        })

    return results
