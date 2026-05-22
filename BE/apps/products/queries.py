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