from .models import (
    Product, 
    Category, 
    ProductGallery, 
    ProductSpecification, 
    VariantType, 
    VariantOption, 
    ProductVariantCombination,
    ProductVariantCombinationOption,
    ProductTag,
    Tag
)
from apps.orders.models import OrderItem, Order
from django.db.models import F, Sum, Q, Case, When, Value, IntegerField, Count
from django.db.models.functions import Coalesce, Cast
from datetime import timedelta


def getProducts():
    return list(Product.objects.all().annotate(category_name=F('category__name')).values('id', 'name', 'photo', 'price', 'price_unit', 'total_stock', 'category_name').order_by('id'))


def getProductById(productId):
    product = Product.objects.filter(id=productId).annotate(category_name=F('category__name')).values(
        'id', 'name', 'photo', 'description', 'price', 'price_unit', 'total_stock', 'category_name'
    ).first()
    return product

def calculatePriceRange(productPrice, pricesList):
    if pricesList:
        return {
            "min": min(pricesList),
            "max": max(pricesList),
        }
    return {"min": productPrice, "max": productPrice}


def calculateAvailableStock(productIds, startDate, endDate):
    isSingleProduct = not isinstance(productIds, (list, tuple, set))
    productIds = [productIds] if isSingleProduct else list(productIds)
    
    if not productIds:
        return 0 if isSingleProduct else {}

    # Convert to datetime if they are strings
    from datetime import datetime
    if isinstance(startDate, str):
        startDate = datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
    if isinstance(endDate, str):
        endDate = datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')

    # 1. Identify products with variants
    productsWithVariant = set(ProductVariantCombination.objects.filter(
        product_id__in=productIds
    ).values_list('product_id', flat=True).distinct())

    # 2. Get total stock for each product
    totalStocks = Product.objects.filter(id__in=productIds).annotate(
        product_total_stock=Coalesce('total_stock', 0),
        variant_total_stock=Coalesce(Sum('variant_combinations__stock'), 0)
    ).values('id', 'product_total_stock', 'variant_total_stock')

    totalStockMap = {
        row['id']: {
            "productTotalStock": row['product_total_stock'],
            "variantTotalStock": row['variant_total_stock']
        } for row in totalStocks
    }

    # 3. Calculate used stock from orders
    # Logic: rental_start < endDate AND ( (status in PENDING, DP, PAID AND rental_end > startDate) OR (status COMPLETED AND rental_end + 24h > startDate) )
    # Note: INTERVAL '24 HOURS' in ORM
    usedStockRows = OrderItem.objects.filter(
        product_id__in=productIds,
        order__rental_start__lt=endDate
    ).filter(
        Q(order__status__code__in=['PENDING', 'DP', 'PAID'], order__rental_end__gt=startDate) |
        Q(order__status__code='COMPLETED', order__rental_end__gt=startDate - timedelta(hours=24))
    ).values('product_id').annotate(
        used_stock_all=Sum('quantity'),
        used_stock_variant=Sum(
            Case(
                When(product_variant_combination_id__isnull=False, then='quantity'),
                default=Value(0),
                output_field=IntegerField()
            )
        )
    )

    usedStockMap = {
        row['product_id']: {
            "usedStockAll": row['used_stock_all'],
            "usedStockVariant": row['used_stock_variant']
        } for row in usedStockRows
    }

    result = {}
    for pid in productIds:
        stock = totalStockMap.get(pid, {"productTotalStock": 0, "variantTotalStock": 0})
        used = usedStockMap.get(pid, {"usedStockAll": 0, "usedStockVariant": 0})
        
        if pid in productsWithVariant:
            available = stock["variantTotalStock"] - used["usedStockVariant"]
        else:
            available = stock["productTotalStock"] - used["usedStockAll"]
        
        result[pid] = max(available, 0)

    return result.get(productIds[0], 0) if isSingleProduct else result


def calculateAvailableStockForCombinations(productId, combinationIds, startDate, endDate):
    combinationIds = list(combinationIds)
    if not combinationIds:
        return {}

    # Convert to datetime if they are strings
    from datetime import datetime
    if isinstance(startDate, str):
        startDate = datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
    if isinstance(endDate, str):
        endDate = datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')

    # Total Stock
    totalStocks = ProductVariantCombination.objects.filter(
        product_id=productId, id__in=combinationIds
    ).values('id', 'stock')
    
    totalStockMap = {row['id']: row['stock'] for row in totalStocks}

    # Used Stock
    usedStockRows = OrderItem.objects.filter(
        product_id=productId,
        product_variant_combination_id__in=combinationIds,
        order__rental_start__lt=endDate
    ).filter(
        Q(order__status__code__in=['PENDING', 'DP', 'PAID'], order__rental_end__gt=startDate) |
        Q(order__status__code='COMPLETED', order__rental_end__gt=startDate - timedelta(hours=24))
    ).values('product_variant_combination_id').annotate(
        used_stock=Sum('quantity')
    )

    usedStockMap = {row['product_variant_combination_id']: row['used_stock'] for row in usedStockRows}

    result = {}
    for cid in combinationIds:
        total = totalStockMap.get(cid, 0)
        used = usedStockMap.get(cid, 0)
        result[cid] = max(total - used, 0)

    return result


def getProductGalleries(productId):
    return list(ProductGallery.objects.filter(
        product_id=productId, product_variant_combination_id__isnull=True
    ).order_by('display_order', 'id').values_list('image_url', flat=True))


def getVariantTypes(productId):
    types = VariantType.objects.filter(product_id=productId).order_by('id')
    if not types.exists():
        return []

    type_ids = list(types.values_list('id', flat=True))
    options = VariantOption.objects.filter(variant_type_id__in=type_ids).order_by('id')
    
    optionsMap = {}
    for opt in options:
        optionsMap.setdefault(opt.variant_type_id, []).append({
            "idOption": opt.id,
            "valueOption": opt.value
        })

    return [{
        "idVariant": t.id,
        "variantName": t.name,
        "isRequired": t.is_required,
        "options": optionsMap.get(t.id, [])
    } for t in types]


def getVariantCombinations(productId, startDate, endDate):
    isBulkRequest = isinstance(productId, (list, tuple, set))

    if isBulkRequest:
        productIds = list(productId)
        if not productIds: return {}
        
        # In the original, there was a view 'product_variant_combination_view'
        # Since we are ORM only, we must calculate the price if it's dynamic, 
        # but the model has a price field. We'll use the model price.
        prices = ProductVariantCombination.objects.filter(
            product_id__in=productIds
        ).values('product_id', 'price').order_by('product_id', 'id')
        
        priceMap = {}
        for p in prices:
            if p['price'] is not None:
                priceMap.setdefault(p['product_id'], []).append(p['price'])
        return priceMap

    # Single Product
    # ARRAY_AGG replacement in Django ORM is tricky. We'll fetch and group in Python.
    combinations = ProductVariantCombination.objects.filter(
        product_id=productId
    ).prefetch_related('combination_options__variant_option', 'combination_options__variant_option__variant_type').order_by('id')
    
    if not combinations.exists():
        return [], []

    comb_ids = [c.id for c in combinations]
    
    # Galleries
    galleries = ProductGallery.objects.filter(
        product_variant_combination_id__in=comb_ids
    ).order_by('display_order', 'id')
    
    galMap = {}
    for g in galleries:
        galMap.setdefault(g.product_variant_combination_id, []).append(g.image_url)

    # Stock
    stockMap = calculateAvailableStockForCombinations(productId, comb_ids, startDate, endDate)

    combinationsData = []
    priceValues = []
    
    for c in combinations:
        # Get variants and option IDs
        opts = c.combination_options.all().order_by('variant_option__variant_type__name')
        v_names = [o.variant_option.value for o in opts]
        v_ids = [o.variant_option_id for o in opts]
        
        if c.price is not None:
            priceValues.append(c.price)

        combinationsData.append({
            "idVariantCombination": c.id,
            "stock": stockMap.get(c.id, c.stock),
            "options": v_ids,
            "variants": v_names,
            "price": c.price,
            "gallery": galMap.get(c.id, [])
        })

    return combinationsData, priceValues


def getProductSpecifications(productId):
    return list(ProductSpecification.objects.filter(
        product_id=productId
    ).order_by('id').values_list('specification', flat=True))

def getProductFeatures(productId):
    return list(ProductTag.objects.filter(
        product_id=productId
    ).select_related('tag').annotate(
        name=F('tag__name')
    ).values('name', 'weight'))


def getProductCategoryCandidates(excludedCategoryIds):
    return list(Product.objects.exclude(
        category_id__in=excludedCategoryIds
    ).values('id', 'name', 'photo', 'price', 'price_unit', 'total_stock', 'category_id'))


def getAllProductFeatures(productIds):
    return list(ProductTag.objects.filter(
        product_id__in=productIds
    ).select_related('tag').annotate(
        name=F('tag__name')
    ).values('product_id', 'name', 'weight'))


def getProductCategoryInfo(productIds):
    return list(Product.objects.filter(id__in=productIds).values('id', 'category_id'))


def getCombinationVariantDetails(combinationId):
    return list(ProductVariantCombinationOption.objects.filter(
        product_variant_combination_id=combinationId
    ).select_related('variant_option', 'variant_option__variant_type', 'product_variant_combination').annotate(
        variant_type_id=F('variant_option__variant_type_id'),
        is_upsell_dimension=F('variant_option__variant_type__is_upsell_dimension'),
        price=F('product_variant_combination__price'),
        product_id=F('product_variant_combination__product_id')
    ).values('variant_option_id', 'variant_type_id', 'is_upsell_dimension', 'price', 'product_id'))


def getSimilarCombinationsWithHigherPrice(productId, currentPrice, upsellDimensionTypeId, currentUpsellOptionId, fixedOptionIds):
    # This involves complex subqueries (EXISTS)
    # We'll use filters for the existence checks
    
    # Base Query: Combinations of same product with higher price
    query = ProductVariantCombination.objects.filter(
        product_id=productId,
        price__gt=currentPrice
    )

    # Constraint: Must have a different option in the upsell dimension
    query = query.filter(
        combination_options__variant_option__variant_type_id=upsellDimensionTypeId
    ).exclude(
        combination_options__variant_option_id=currentUpsellOptionId
    )

    # Constraint: Must have all fixed options
    for opt_id in fixedOptionIds:
        query = query.filter(combination_options__variant_option_id=opt_id)

    # Final Select and Format
    results = query.select_related('product').annotate(
        product_name=F('product__name'),
        product_photo=F('product__photo'),
        product_price_unit=F('product__price_unit')
    ).values(
        'id', 'price', 'stock', 'product_name', 'product_photo', 'product_price_unit'
    )

    # Rename for output consistency
    formatted = []
    for r in results:
        formatted.append({
            "id": r['id'],
            "price": r['price'],
            "stock": r['stock'],
            "product_name": r['product_name'],
            "product_photo": r['product_photo'],
            "price_unit": r['product_price_unit']
        })
    return formatted


def validateProductCombination(productId, combinationId):
    return ProductVariantCombination.objects.filter(id=combinationId, product_id=productId).exists()
