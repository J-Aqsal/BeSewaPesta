from utils.db import dbExecute, dbFetch

def insertOrder(guestId, totalPrice, statusId, rentalStart, rentalEnd, recipientName, phoneNumber, shippingAddress, city, shippingCost):
    query = """
        INSERT INTO orders (
            guest_id, total_price, status_id, rental_start, rental_end, 
            recipient_name, phone_number, shipping_address, city, shipping_cost, 
            created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING id
    """
    return dbExecute(query, [
        guestId, totalPrice, statusId, rentalStart, rentalEnd, 
        recipientName, phoneNumber, shippingAddress, city, shippingCost
    ], returning=True)


def insertOrderItem(orderId, productId, quantity, price, combinationId=None):
    query = """
        INSERT INTO order_items (order_id, product_id, quantity, price, product_variant_combination_id)
        VALUES (%s, %s, %s, %s, %s)
    """
    dbExecute(query, [orderId, productId, quantity, price, combinationId])

def getOrders():
    query = """
        SELECT 
            o.id AS order_id,
            o.guest_id,
            o.total_price,
            o.rental_start,
            o.rental_end,
            o.recipient_name,
            o.phone_number,
            o.shipping_address,
            o.city,
            o.shipping_cost,
            o.created_at,
            s.name AS status_name
        FROM orders o
        JOIN order_statuses s ON o.status_id = s.id
        ORDER BY o.created_at DESC
    """
    orders = dbFetch(query, [], fetchAll=True) or []

    return orders

def getOrderByOrderId(orderId):
    query = """
        SELECT 
            o.id AS order_id,
            o.guest_id,
            o.total_price,
            o.rental_start,
            o.rental_end,
            o.recipient_name,
            o.phone_number,
            o.shipping_address,
            o.city,
            o.shipping_cost,
            o.created_at,
            s.name AS status_name
        FROM orders o
        JOIN order_statuses s ON o.status_id = s.id
        WHERE o.id = %s
    """
    orders = dbFetch(query, [orderId], fetchAll=True) or []

    return orders

def getOrderItemsByOrderId(orderId):
    query = """
        SELECT 
            oi.id AS order_item_id,
            oi.product_id,
            p.name AS product_name,
            oi.quantity,
            oi.price,
            oi.product_variant_combination_id,
            c.name AS category_name,
            p.photo AS thumbnail
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        WHERE oi.order_id = %s
    """
    return dbFetch(query, [orderId], fetchAll=True) or []


def getCombinationNameByOrderId(orderId):
    query = """
        SELECT 
            oi.id AS order_item_id,
            vo.value AS combination_name
        FROM order_items oi
        LEFT JOIN product_variant_combination_options pvco
            ON pvco.product_variant_combination_id = oi.product_variant_combination_id
        LEFT JOIN variant_options vo
            ON vo.id = pvco.variant_option_id
        WHERE oi.order_id = %s
        GROUP BY oi.id, vo.value
        ORDER BY oi.id
    """
    return dbFetch(query, [orderId], fetchAll=True) or []

def updateOrderStatus(orderId, newStatusId):
    query = """
        UPDATE orders
        SET status_id = %s
        WHERE id = %s
    """
    dbExecute(query, [newStatusId, orderId])


def getOrderStatusesRepo():
    query = "SELECT id, name FROM order_statuses ORDER BY id ASC"
    return dbFetch(query, fetchAll=True)