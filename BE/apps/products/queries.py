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


def getProductById(product_id):
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
    result = dbFetch(query, [product_id])

    if not result:
        return None

    return result

def calculatePriceRange(product_price, prices_list):
    if prices_list:
        min_price = min(prices_list)
        max_price = max(prices_list)
        return {
            "min": min_price,
            "max": max_price,
        }
    
    return {
        "min": product_price,
        "max": product_price,
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
            "product_total_stock": int(row["product_total_stock"] or 0),
            "variant_total_stock": int(row["variant_total_stock"] or 0),
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

        JOIN orders o
            ON o.id = oi.order_id

        JOIN order_statuses os
            ON os.id = o.status_id

        WHERE oi.product_id = ANY(%s)
        AND o.rental_start < %s
        AND o.rental_end > %s
        AND (
            os.code IN ('PENDING', 'DP', 'PAID')
            OR (
                os.code = 'COMPLETED'
                AND o.rental_end >= NOW() - INTERVAL '24 HOURS'
            )
        )

        GROUP BY oi.product_id
        """
    
    usedStockRows = dbFetch(query, [productIds, endDate, startDate], fetchAll=True) or []
    usedStockMap = {
        row["product_id"]: {
            "used_stock_all": int(row["used_stock_all"] or 0),
            "used_stock_variant": int(row["used_stock_variant"] or 0),
        }
        for row in usedStockRows
    }

    result = {}
    for productId in productIds:
        stock = totalStockMap.get(productId, {"product_total_stock": 0, "variant_total_stock": 0})
        used = usedStockMap.get(productId, {"used_stock_all": 0, "used_stock_variant": 0})
        hasVariant = productId in productsWithVariant

        if hasVariant:
            available = stock["variant_total_stock"] - used["used_stock_variant"]
        else:
            available = stock["product_total_stock"] - used["used_stock_all"]

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



def getProductGalleries(product_id):
    query = """
        SELECT
            image_url
        FROM product_galleries
        WHERE product_id = %s
        AND product_variant_combination_id IS NULL
        ORDER BY display_order, id
        """
    
    rows = dbFetch(query, [product_id], fetchAll=True)

    return [row["image_url"] for row in rows]


def getVariantTypes(product_id):
    query = """
        SELECT
            id,
            name,
            is_required
        FROM variant_types
        WHERE product_id = %s
        ORDER BY id
        """
    
    variant_types = dbFetch(query, [product_id], fetchAll=True) or []

    if not variant_types:
        return []

    variant_type_ids = [row["id"] for row in variant_types]
    query = """
        SELECT
            id,
            variant_type_id,
            value
        FROM variant_options
        WHERE variant_type_id = ANY(%s)
        ORDER BY id
        """
    variant_options = dbFetch(query, [variant_type_ids], fetchAll=True) or []

    options_map = {}
    for row in variant_options:
        options_map.setdefault(row["variant_type_id"], []).append(
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
            "options": options_map.get(row["id"], []),
        }
        for row in variant_types
    ]


def getVariantCombinations(product_id, start_date, end_date):
    # Cek kalau request untuk catalog (bulk) atau detail (single)
    isBulkRequest = isinstance(product_id, (list, tuple, set))

    if isBulkRequest:
        product_ids = list(product_id)
        if not product_ids:
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
            [product_ids],
            fetchAll=True,
        ) or []

        price_values_map = {}
        for row in rows:
            price = row["price"]
            if price is None:
                continue

            price_values_map.setdefault(row["product_id"], []).append(price)

        return price_values_map

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
    
    combinations = dbFetch(query, [product_id], fetchAll=True) or []

    if not combinations:
        return [], []

    combination_ids = [row["combination_id"] for row in combinations]

    price_values = []
    for row in combinations:
        normalized_price = row["price"]
        if normalized_price is not None:
            price_values.append(normalized_price)

    query = """
        SELECT
            product_variant_combination_id,
            image_url
        FROM product_galleries
        WHERE product_variant_combination_id = ANY(%s)
        ORDER BY display_order, id
        """
    
    gallery_rows = dbFetch(query, [combination_ids], fetchAll=True) or []

    gallery_map = {}
    for row in gallery_rows:
        gallery_map.setdefault(row["product_variant_combination_id"], []).append(
            row["image_url"]
        )

    stock_map = calculateAvailableStockForCombinations(
        product_id,
        combination_ids,
        start_date,
        end_date,
    )

    combinations_data = [
        {
            "idVariantCombination": row["combination_id"],
            "stock": stock_map.get(row["combination_id"], int(row["stock"] or 0)),
            "options": row["variant_option_ids"] or [],
            "variants": row["variants"] or [],
            "price": row["price"],
            "gallery": gallery_map.get(row["combination_id"], []),
        }
        for row in combinations
    ]

    return combinations_data, price_values


def getProductSpecifications(product_id):
    query = """
        SELECT
            specification
        FROM product_specifications
        WHERE product_id = %s
        ORDER BY id
        """
    
    rows = dbFetch(query, [product_id], fetchAll=True) or []

    return [row["specification"] for row in rows]