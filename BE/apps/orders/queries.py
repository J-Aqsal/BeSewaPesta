from utils.db import dbExecute

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
