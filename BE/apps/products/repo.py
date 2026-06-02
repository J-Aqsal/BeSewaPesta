from utils.db import dbFetch


def getProducts():
    query = """
        SELECT
            id,
            name,
            photo,
            price,
            price_unit,
            total_stock
        FROM products
        ORDER BY id
    """
    result = dbFetch(query, fetchAll=True)

    return result or []


def getProductById(productId):
    query ="""
        SELECT
            id,
            name,
            photo,
            description,
            price,
            price_unit,
            total_stock
        FROM products
        WHERE id = %s
    """
    result = dbFetch(query, [productId])

    if not result:
        return None

    return result

def calculatePriceRange(productPrice, pricesList):
    if pricesList:
        minPrice = min(pricesList)
        maxPrice = max(pricesList)
        return {
            "min": minPrice,
            "max": maxPrice,
        }
    
    return {
        "min": productPrice,
        "max": productPrice,
    }


def calculateAvailableStock(productIds, startDate, endDate):
    # Untuk cek buat detail atau catalog
    isSingleProduct = not isinstance(productIds, (list, tuple, set))
    productIds = [productIds] if isSingleProduct else list(productIds)
    if not productIds:
        if isSingleProduct:
            return 0
        else:
            return {}
        
    # VARIANT COMBINATIONS CHECK
    query =  """
        SELECT DISTINCT pvc.product_id
        FROM product_variant_combinations pvc
        WHERE pvc.product_id = ANY(%s)
        """
    
    variantRows = dbFetch(query, [productIds], fetchAll=True) or []
    productsWithVariant = {
        row["product_id"] 
        for row in variantRows
    }
    # TOTAL STOCK
    query = """
        SELECT
            p.id AS product_id,
            COALESCE(p.total_stock, 0) AS product_total_stock,
            COALESCE(SUM(pvc.stock), 0) AS variant_total_stock
        FROM products p
        LEFT JOIN product_variant_combinations pvc
            ON pvc.product_id = p.id
        WHERE p.id = ANY(%s)
        GROUP BY p.id
        """
    
    totalStockRows = dbFetch(query, [productIds], fetchAll=True) or []
    
    totalStockMap = {
        row["product_id"]: {
            "productTotalStock": int(row["product_total_stock"] or 0),
            "variantTotalStock": int(row["variant_total_stock"] or 0),
        }
        for row in totalStockRows
    }
    
    # USED STOCK
    query = """
        SELECT
            oi.product_id,
            COALESCE(SUM(oi.quantity), 0) AS used_stock_all,
            COALESCE(
                SUM(
                    CASE
                        WHEN oi.product_variant_combination_id IS NOT NULL THEN oi.quantity
                        ELSE 0
                    END
                ),
                0
            ) AS used_stock_variant
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        JOIN order_statuses os ON os.id = o.status_id
        WHERE oi.product_id = ANY(%s)
        AND o.rental_start < %s
        AND (
            (os.code IN ('PENDING', 'DP', 'PAID') AND o.rental_end > %s)
            OR (os.code = 'COMPLETED' AND (o.rental_end + INTERVAL '24 HOURS') > %s)
        )
        GROUP BY oi.product_id
        """
    
    usedStockRows = dbFetch(query, [productIds, endDate, startDate, startDate], fetchAll=True) or []
    
    usedStockMap = {
        row["product_id"]: {
            "usedStockAll": int(row["used_stock_all"] or 0),
            "usedStockVariant": int(row["used_stock_variant"] or 0),
        }
        for row in usedStockRows
    }

    result = {}
    for productId in productIds:
        stock = totalStockMap.get(productId, {"productTotalStock": 0, "variantTotalStock": 0})
        used = usedStockMap.get(productId, {"usedStockAll": 0, "usedStockVariant": 0})
        hasVariant = productId in productsWithVariant

        if hasVariant:
            available = stock["variantTotalStock"] - used["usedStockVariant"]
        else:
            available = stock["productTotalStock"] - used["usedStockAll"]

        result[productId] = available

    if isSingleProduct:
        return result.get(productIds[0], 0)
    return result


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
        COALESCE(SUM(oi.quantity), 0) AS used_stock
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id
    JOIN order_statuses os ON os.id = o.status_id
    WHERE oi.product_id = %s
    AND oi.product_variant_combination_id = ANY(%s)
    AND o.rental_start < %s
    AND (
        (os.code IN ('PENDING', 'DP', 'PAID') AND o.rental_end > %s)
        OR (os.code = 'COMPLETED' AND (o.rental_end + INTERVAL '24 HOURS') > %s)
    )
    GROUP BY oi.product_variant_combination_id
    """

    usedStockRows = dbFetch(query, [productId, combinationIds, endDate, startDate, startDate], fetchAll=True) or []

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



def getProductGalleries(productId):
    query = """
        SELECT
            image_url
        FROM product_galleries
        WHERE product_id = %s
        AND product_variant_combination_id IS NULL
        ORDER BY display_order, id
        """
    
    rows = dbFetch(query, [productId], fetchAll=True)

    return [row["image_url"] for row in rows]


def getVariantTypes(productId):
    query = """
        SELECT
            id,
            name,
            is_required
        FROM variant_types
        WHERE product_id = %s
        ORDER BY id
        """
    
    variantTypes = dbFetch(query, [productId], fetchAll=True) or []

    if not variantTypes:
        return []

    variantTypeIds = [row["id"] for row in variantTypes]
    query = """
        SELECT
            id,
            variant_type_id,
            value
        FROM variant_options
        WHERE variant_type_id = ANY(%s)
        ORDER BY id
        """
    variantOptions = dbFetch(query, [variantTypeIds], fetchAll=True) or []

    optionsMap = {}
    for row in variantOptions:
        optionsMap.setdefault(row["variant_type_id"], []).append(
            {
                "idOption": row["id"],
                "valueOption": row["value"],
            }
        )

    return [
        {
            "idVariant": row["id"],
            "variantName": row["name"],
            "isRequired": bool(row["is_required"]),
            "options": optionsMap.get(row["id"], []),
        }
        for row in variantTypes
    ]


def getVariantCombinations(productId, startDate, endDate):
    # Cek kalau request untuk catalog (bulk) atau detail (single)
    isBulkRequest = isinstance(productId, (list, tuple, set))

    if isBulkRequest:
        productIds = list(productId)
        if not productIds:
            return {}

        rows = dbFetch(
            """
            SELECT
                pvc.product_id,
                pvcv.price
            FROM product_variant_combinations pvc
            LEFT JOIN product_variant_combination_view pvcv
                ON pvcv.combination_id = pvc.id
            WHERE pvc.product_id = ANY(%s)
            ORDER BY pvc.product_id, pvc.id
            """,
            [productIds],
            fetchAll=True,
        ) or []

        priceValuesMap = {}
        for row in rows:
            price = row["price"]
            if price is None:
                continue

            priceValuesMap.setdefault(row["product_id"], []).append(price)

        return priceValuesMap

    query = """
        SELECT
            pvc.id AS combination_id,
            p.id AS product_id,
            p.name AS product_name,
            pvc.stock,
            pvcv.price,
            ARRAY_AGG(vo.value ORDER BY vt.name) AS variants,
            ARRAY_AGG(vo.id ORDER BY vt.name) AS variant_option_ids
        FROM product_variant_combinations pvc
        JOIN products p
            ON p.id = pvc.product_id
        JOIN product_variant_combination_options pvco
            ON pvco.product_variant_combination_id = pvc.id
        JOIN variant_options vo
            ON vo.id = pvco.variant_option_id
        JOIN variant_types vt
            ON vt.id = vo.variant_type_id
        LEFT JOIN product_variant_combination_view pvcv
            ON pvcv.combination_id = pvc.id
        WHERE pvc.product_id = %s
        GROUP BY pvc.id, p.id, p.name, pvc.stock, pvcv.price
        ORDER BY pvc.id
        """
    
    combinations = dbFetch(query, [productId], fetchAll=True) or []

    if not combinations:
        return [], []

    combinationIds = [row["combination_id"] for row in combinations]

    priceValues = []
    for row in combinations:
        normalizedPrice = row["price"]
        if normalizedPrice is not None:
            priceValues.append(normalizedPrice)

    query = """
        SELECT
            product_variant_combination_id,
            image_url
        FROM product_galleries
        WHERE product_variant_combination_id = ANY(%s)
        ORDER BY display_order, id
        """
    
    galleryRows = dbFetch(query, [combinationIds], fetchAll=True) or []

    galleryMap = {}
    for row in galleryRows:
        galleryMap.setdefault(row["product_variant_combination_id"], []).append(
            row["image_url"]
        )

    stockMap = calculateAvailableStockForCombinations(
        productId,
        combinationIds,
        startDate,
        endDate,
    )

    combinationsData = [
        {
            "idVariantCombination": row["combination_id"],
            "stock": stockMap.get(row["combination_id"], int(row["stock"] or 0)),
            "options": row["variant_option_ids"] or [],
            "variants": row["variants"] or [],
            "price": row["price"],
            "gallery": galleryMap.get(row["combination_id"], []),
        }
        for row in combinations
    ]

    return combinationsData, priceValues


def getProductSpecifications(productId):
    query = """
        SELECT
            specification
        FROM product_specifications
        WHERE product_id = %s
        ORDER BY id
        """
    
    rows = dbFetch(query, [productId], fetchAll=True) or []

    return [row["specification"] for row in rows]

def getProductFeatures(productId):
    query = """
        SELECT t.name, pt.weight
        FROM product_tags pt
        JOIN tags t ON t.id = pt.tag_id
        WHERE pt.product_id = %s
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
        SELECT pt.product_id, t.name, pt.weight
        FROM product_tags pt
        JOIN tags t ON t.id = pt.tag_id
        WHERE pt.product_id = ANY(%s)
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
    for optionId in fixedOptionIds:
        query += f"""
        AND EXISTS (
            SELECT 1 FROM product_variant_combination_options pvco_{optionId}
            WHERE pvco_{optionId}.product_variant_combination_id = pvc.id
            AND pvco_{optionId}.variant_option_id = %s
        )
        """
        params.append(optionId)

    return dbFetch(query, params, fetchAll=True)


def validateProductCombination(productId, combinationId):
    query = """
        SELECT 1 FROM product_variant_combinations
        WHERE id = %s AND product_id = %s
    """
    result = dbFetch(query, [combinationId, productId])
    return result is not None
