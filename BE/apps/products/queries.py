from utils.db import dbFetch

def calculateAvailableStock(productId, startDate, endDate):

    query = """
    SELECT EXISTS (
        SELECT 1
        FROM variant_types
        WHERE product_id = %s
    )
    """

    hasVariantResult = dbFetch(query, [productId])
    hasVariant = hasVariantResult["exists"]

    if not hasVariant:
        # PRODUCT HAS NO VARIANTS

        query = """
        SELECT
            total_stock
        FROM products
        WHERE id = %s
        """

        totalStockResult = dbFetch(query, [productId])
        totalStock = totalStockResult["total_stock"] or 0

        query = """
        SELECT
            COALESCE(
                SUM(oi.quantity),
                0
            ) AS used_stock

        FROM order_items oi

        JOIN orders o
            ON o.id = oi.order_id

        JOIN order_statuses os
            ON os.id = o.status_id

        WHERE oi.product_id = %s

        AND o.rental_start < %s

        AND o.rental_end > %s

        AND (
            os.code IN (
                'PENDING',
                'DP',
                'PAID'
            )

            OR (

                os.code = 'COMPLETED'

                AND o.rental_end >= NOW() - INTERVAL '24 HOURS'
            )
        )
        """

        usedStockResult = dbFetch(query, [productId, endDate, startDate])
        usedStock = usedStockResult["used_stock"] or 0

        return int(totalStock - usedStock)

    # PRODUCT HAS VARIANTS

    query = """
    SELECT
        COALESCE(
            SUM(stock),
            0
        ) AS total_stock

    FROM product_variant_combinations

    WHERE product_id = %s
    """

    totalStockResult = dbFetch(query, [productId])
    totalStock = totalStockResult["total_stock"] or 0

    query = """
    SELECT
        COALESCE(
            SUM(oi.quantity),
            0
        ) AS used_stock

    FROM order_items oi

    JOIN orders o
        ON o.id = oi.order_id

    JOIN order_statuses os
        ON os.id = o.status_id

    WHERE oi.product_id = %s

    AND oi.product_variant_combination_id
        IS NOT NULL

    AND o.rental_start < %s

    AND o.rental_end > %s

    AND (
        os.code IN (
            'PENDING',
            'DP',
            'PAID'
        )

        OR (

            os.code = 'COMPLETED'

            AND o.rental_end >= NOW() - INTERVAL '24 HOURS'
        )
    )
    """

    usedStockResult = dbFetch(query,[productId, endDate, startDate])
    usedStock = usedStockResult["used_stock"] or 0

    return int(totalStock - usedStock)


def calculateAvailableStockForCombinations(productId, combinationIds, startDate, endDate):

    combinationIds = list(combinationIds)

    if not combinationIds:
        return {}
    
    # TOTAL STOCK

    query = """
    SELECT
        id,

        stock

    FROM product_variant_combinations

    WHERE product_id = %s

    AND id = ANY(%s)
    """

    totalStockRows = dbFetch(query, [productId, combinationIds], fetchAll=True)

    totalStockMap = {

        row["id"]:
        int(row["stock"] or 0)

        for row in totalStockRows
    }

    # USED STOCK

    query = """
    SELECT
        oi.product_variant_combination_id,

        COALESCE(
            SUM(oi.quantity),
            0
        ) AS used_stock

    FROM order_items oi

    JOIN orders o
        ON o.id = oi.order_id

    JOIN order_statuses os
        ON os.id = o.status_id

    WHERE oi.product_id = %s

    AND oi.product_variant_combination_id
        = ANY(%s)

    AND o.rental_start < %s

    AND o.rental_end > %s

    AND (

        os.code IN (
            'PENDING',
            'DP',
            'PAID'
        )

        OR (

            os.code = 'COMPLETED'

            AND o.rental_end >= NOW() - INTERVAL '24 HOURS'
        )
    )

    GROUP BY
        oi.product_variant_combination_id
    """

    usedStockRows = dbFetch(query,[productId, combinationIds, endDate, startDate], fetchAll=True)

    usedStockMap = {
        row["product_variant_combination_id"]: int(row["used_stock"] or 0)

        for row in usedStockRows
    }

    result = {}

    for combinationId in combinationIds:

        totalStock = totalStockMap.get(combinationId, 0)
        usedStock = usedStockMap.get(combinationId, 0)

        result[combinationId] = (totalStock - usedStock)

    return result


def calculatePriceRange(basePrice, pricesList):

    if pricesList:

        minPrice = min(pricesList)
        maxPrice = max(pricesList)

        return {
            "min": minPrice,
            "max": maxPrice
        }

    basePrice = basePrice or 0

    return {
        "min": basePrice,
        "max": basePrice
    }


def getProductFeatures(productId):
    query = """
        SELECT c.slug, pc.weight
        FROM product_contexts pc
        JOIN contexts c ON c.id = pc.context_id
        WHERE pc.product_id = %s
    """
    return dbFetch(query, [productId], fetchAll=True)


def getProductCategoryCandidates(excludedCategoryIds):
    query = """
        SELECT 
            p.id, p.name, p.photo, p.price, p.price_unit, p.total_stock, p.category_id
        FROM products p
        WHERE p.category_id != ALL(%s)
    """
    return dbFetch(query, [excludedCategoryIds], fetchAll=True)


def getAllProductFeatures(productIds):
    query = """
        SELECT pc.product_id, c.slug, pc.weight
        FROM product_contexts pc
        JOIN contexts c ON c.id = pc.context_id
        WHERE pc.product_id = ANY(%s)
    """
    return dbFetch(query, [productIds], fetchAll=True)


def getProductCategoryInfo(productIds):
    query = """
        SELECT id, category_id 
        FROM products 
        WHERE id = ANY(%s)
    """
    return dbFetch(query, [productIds], fetchAll=True)


def getCombinationVariantDetails(combinationId):
    query = """
        SELECT 
            pvco.variant_option_id,
            vt.id as variant_type_id,
            vt.is_upsell_dimension,
            pvc.price,
            pvc.product_id
        FROM product_variant_combination_options pvco
        JOIN variant_options vo ON vo.id = pvco.variant_option_id
        JOIN variant_types vt ON vt.id = vo.variant_type_id
        JOIN product_variant_combinations pvc ON pvc.id = pvco.product_variant_combination_id
        WHERE pvco.product_variant_combination_id = %s
    """
    return dbFetch(query, [combinationId], fetchAll=True)


def getSimilarCombinationsWithHigherPrice(productId, currentPrice, upsellDimensionTypeId, currentUpsellOptionId, fixedOptionIds):
    query = """
        SELECT 
            pvc.id,
            pvc.price,
            pvc.stock,
            p.name as product_name,
            p.photo as product_photo,
            p.price_unit
        FROM product_variant_combinations pvc
        JOIN products p ON p.id = pvc.product_id
        WHERE pvc.product_id = %s
        AND pvc.price > %s
        AND EXISTS (
            SELECT 1 FROM product_variant_combination_options pvco_u
            WHERE pvco_u.product_variant_combination_id = pvc.id
            AND pvco_u.variant_option_id != %s
            AND EXISTS (
                SELECT 1 FROM variant_options vo_u
                WHERE vo_u.id = pvco_u.variant_option_id
                AND vo_u.variant_type_id = %s
            )
        )
    """

    params = [productId, currentPrice, currentUpsellOptionId, upsellDimensionTypeId]
    for option_id in fixedOptionIds:
        query += f"""
        AND EXISTS (
            SELECT 1 FROM product_variant_combination_options pvco_{option_id}
            WHERE pvco_{option_id}.product_variant_combination_id = pvc.id
            AND pvco_{option_id}.variant_option_id = %s
        )
        """
        params.append(option_id)

    return dbFetch(query, params, fetchAll=True)


def validateProductCombination(productId, combinationId):
    query = """
        SELECT 1 FROM product_variant_combinations
        WHERE id = %s AND product_id = %s
    """
    result = dbFetch(query, [combinationId, productId])
    return result is not None
