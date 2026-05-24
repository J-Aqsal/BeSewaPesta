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
            s.name AS status_name
        FROM orders o
        JOIN order_statuses s ON o.status_id = s.id
        ORDER BY o.created_at DESC
    """
    # format json
    orders = dbFetch(query, [], fetchAll=True) or []
    formattedOrders = []
    for order in orders:
        formattedOrders.append({
            "idOrder": order["order_id"],
            "recipientName": order["recipient_name"],
            "rentalStart": order["rental_start"],
            "rentalEnd": order["rental_end"],
            "phoneNumber": order["phone_number"],
            "shippingAddress": order["shipping_address"],
            "totalPrice": int(order["total_price"]),
            "status": order["status_name"]
        })
    return formattedOrders

def updateOrderStatus(orderId, newStatusId):
    query = """
        UPDATE orders
        SET status_id = %s
        WHERE id = %s
    """
    dbExecute(query, [newStatusId, orderId])