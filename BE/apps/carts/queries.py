from utils.db import dbFetch, dbExecute


def getCartByGuestId(guestId):

    query = """
        SELECT
            id,
            guest_id,
            rental_start,
            rental_end,
            created_at
        FROM carts
        WHERE guest_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """

    result = dbFetch(query, [guestId])

    if not result:
        return None
    
    return {
        "id": result['id'],
        "guest_id": result['guest_id'],
        "rental_start": result['rental_start'],
        "rental_end": result['rental_end'],
        "created_at": result['created_at']
    }


def getCartItemsByCartId(cartId):

    query = """
        SELECT
            ci.id,
            ci.product_id,
            ci.quantity,
            ci.product_variant_combination_id,

            p.name,
            p.photo,
            p.price,
            p.price_unit,
            p.total_stock,

            c.name,

            pvc.price

        FROM cart_items ci

        JOIN products p
            ON p.id = ci.product_id

        LEFT JOIN categories c
            ON c.id = p.category_id

        LEFT JOIN product_variant_combinations pvc
            ON pvc.id = ci.product_variant_combination_id

        WHERE ci.cart_id = %s

        ORDER BY ci.id ASC
    """

    results = dbFetch(query, [cartId], fetchAll=True)

    items = []

    for row in results:

        items.append({
            "id": row['id'],
            "product_id": row['product_id'],
            "quantity": row['quantity'],
            "product_variant_combination_id": row['product_variant_combination_id'],
            "product_name": row['name'],
            "thumbnail": row['photo'],
            "product_price": row['price'],
            "price_unit": row['price_unit'],
            "total_stock": row['total_stock'],
            "category_name": row['name'],
            "combination_price": row['price']
        })

    return items


def getVariantCombinationDetail(combinationId):

    query = """
        SELECT
            vt.name,
            vo.value

        FROM product_variant_combination_options pvco

        JOIN variant_options vo
            ON vo.id = pvco.variant_option_id

        JOIN variant_types vt
            ON vt.id = vo.variant_type_id

        WHERE pvco.product_variant_combination_id = %s

        ORDER BY vt.id ASC
    """

    results = dbFetch(query, [combinationId], fetchAll=True)

    variants = []

    for row in results:

        variants.append({
            "variantName": row['name'],
            "valueOption": row['value']
        })

    return variants


def createCart(guestId, rentalStart, rentalEnd):
    query = """
        INSERT INTO carts (guest_id, rental_start, rental_end, created_at, updated_at)
        VALUES (%s, %s, %s, NOW(), NOW())
        RETURNING id
    """
    return dbExecute(query, [guestId, rentalStart, rentalEnd], returning=True)


def updateCartRentalDates(cartId, rentalStart, rentalEnd):
    query = """
        UPDATE carts 
        SET rental_start = %s, rental_end = %s, updated_at = NOW()
        WHERE id = %s
    """
    dbExecute(query, [rentalStart, rentalEnd, cartId])


def getCartItem(cartId, productId, combinationId=None):
    if combinationId:
        query = """
            SELECT id, quantity FROM cart_items
            WHERE cart_id = %s AND product_id = %s AND product_variant_combination_id = %s
        """
        return dbFetch(query, [cartId, productId, combinationId])
    else:
        query = """
            SELECT id, quantity FROM cart_items
            WHERE cart_id = %s AND product_id = %s AND product_variant_combination_id IS NULL
        """
        return dbFetch(query, [cartId, productId])


def addCartItem(cartId, productId, combinationId, quantity):
    query = """
        INSERT INTO cart_items (cart_id, product_id, product_variant_combination_id, quantity, created_at)
        VALUES (%s, %s, %s, %s, NOW())
    """
    dbExecute(query, [cartId, productId, combinationId, quantity])


def updateCartItemQuantity(cartItemId, newQuantity):
    query = """
        UPDATE cart_items SET quantity = %s WHERE id = %s
    """
    dbExecute(query, [newQuantity, cartItemId])


def validateCartItemOwnership(cartItemId, guestId):
    query = """
        SELECT 1 FROM cart_items ci
        JOIN carts c ON c.id = ci.cart_id
        WHERE ci.id = %s AND c.guest_id = %s
    """
    result = dbFetch(query, [cartItemId, guestId])
    return result is not None


def deleteCartItem(cartItemId):
    query = """
        DELETE FROM cart_items WHERE id = %s
    """
    dbExecute(query, [cartItemId])
