import math
from datetime import datetime, timedelta
from django.db import transaction
from apps.carts.services import getCartDetailByGuestId
from apps.carts.repo import clearCart
from .repo import (
    insertOrder, 
    insertOrderItem, 
    getOrders, 
    getOrderByOrderId, 
    getOrderItemsByOrderId, 
    getCombinationNameByOrderId, 
    updateOrderStatus,
    getOrderStatusesRepo
)
def calculateDurationDays(startDate, endDate):
    if not startDate or not endDate:
        return 1
    
    if isinstance(startDate, str):
        startDate = datetime.strptime(startDate, '%Y-%m-%d %H:%M:%S')
    if isinstance(endDate, str):
        endDate = datetime.strptime(endDate, '%Y-%m-%d %H:%M:%S')
        
    diff = endDate - startDate
    seconds = diff.total_seconds()
    
    # Calculate days, rounding up (e.g., 24h 1s = 2 days)
    days = math.ceil(seconds / 86400)
    
    return max(days, 1)


def calculateShippingCostService(subtotal, city):
    if not city:
        return 0
    
    city = city.lower().strip()

    # City normalization mapping
    if "jakarta" in city:
        city = "jakarta"
    elif "tangerang" in city:
        city = "tangerang"
    elif "bekasi" in city:
        city = "bekasi"
    elif "bogor" in city:
        city = "bogor"
    elif "depok" in city:
        city = "depok"
    
    if subtotal < 500000:
        if city in ["jakarta", "bekasi"]:
            return 500000
        elif city == "depok":
            return 500000
        elif city in ["bogor", "tangerang"]:
            return 1000000
        else:
            return 0
    elif 500000 <= subtotal < 1000000:
        if city in ["jakarta", "bekasi"]:
            return 300000
        elif city == "depok":
            return 400000
        elif city in ["bogor", "tangerang"]:
            return 500000
        else:
            return 0
    else:  # subtotal >= 1000000
        if city in ["jakarta", "bekasi"]:
            return 200000
        elif city == "depok":
            return 300000
        elif city in ["bogor", "tangerang"]:
            return 500000
        else:
            return 0


def getRentalSummaryService(guestId):
    cartData = getCartDetailByGuestId(guestId)
    
    if not cartData or not cartData['items']:
        return None
    
    totalQuantity = sum(item['quantity'] for item in cartData['items'])
    totalPricePerDay = cartData['totalPrice']
    totalDays = calculateDurationDays(cartData['rentalStart'], cartData['rentalEnd'])
    totalRentalAmount = totalPricePerDay * totalDays
    downPayment = totalRentalAmount // 2
    
    return {
        "totalQuantity": totalQuantity,
        "totalPricePerDay": totalPricePerDay,
        "totalDays": totalDays,
        "totalRentalAmount": totalRentalAmount,
        "downPayment": downPayment
    }


def processCheckout(guestId, recipientName, phoneNumber, shippingAddress, city):
    cartData = getCartDetailByGuestId(guestId)
    if not cartData or not cartData['items']:
        return {"success": False, "message": "Cart is empty or not found."}

    summary = getRentalSummaryService(guestId)
    if not summary:
        return {"success": False, "message": "Failed to generate rental summary."}

    subtotalPerDay = cartData['totalPrice']
    shippingCost = calculateShippingCostService(subtotalPerDay, city)
    finalTotalPrice = summary['totalRentalAmount'] + shippingCost

    try:
        with transaction.atomic():
            # 1. Create Order
            order = insertOrder(
                guestId=guestId,
                totalPrice=finalTotalPrice,
                statusId=1, # PENDING
                rentalStart=cartData['rentalStart'],
                rentalEnd=cartData['rentalEnd'],
                recipientName=recipientName,
                phoneNumber=phoneNumber,
                shippingAddress=shippingAddress,
                city=city,
                shippingCost=shippingCost
            )
            orderId = order['id']

            # 2. Move items to Order Items
            for item in cartData['items']:
                combinationId = None
                if item['variantCombination']:
                    combinationId = item['variantCombination']['idVariantCombination']
                
                insertOrderItem(
                    orderId=orderId,
                    productId=item['idProduct'],
                    quantity=item['quantity'],
                    price=item['pricePerItem'],
                    combinationId=combinationId
                )

            # 3. Clear Cart
            clearCart(cartData['cartId'])

        return {
            "success": True, 
            "message": "Checkout successful.", 
            "data": {
                "orderId": orderId,
                "totalPrice": finalTotalPrice,
                "shippingCost": shippingCost,
                "totalDays": summary['totalDays'],
                "totalRentalAmount": summary['totalRentalAmount'],
                "paymentDeadline": (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

def updateOrderStatusService(orderId, newStatusId):
    # Basic validation
    order = getOrderByOrderId(orderId)
    if not order:
        return {"success": False, "message": "Order not found."}
    
    # Check if status ID exists in DB
    statuses = getOrderStatusesRepo()
    validStatusIds = [s['id'] for s in statuses]

    if newStatusId not in validStatusIds:
        return {"success": False, "message": "Invalid status ID."}
        
    try:
        updateOrderStatus(orderId, newStatusId)
        return {"success": True, "message": "Order status updated successfully."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def getOrderStatusesService():
    return getOrderStatusesRepo()

def getAllOrders():
    orders = getOrders()
    formattedOrders = []
    for order in orders:
        formattedOrders.append({
            "idOrder": order["order_id"],
            "recipientName": order["recipient_name"],
            "rentalStart": order["rental_start"],
            "rentalEnd": order["rental_end"],
            "phoneNumber": order["phone_number"],
            "shippingAddress": order["shipping_address"],
            "city": order["city"],
            "totalPrice": int(order["total_price"]),
            "status": order["status_name"],
            "createdAt": order["created_at"].strftime('%Y-%m-%d %H:%M:%S') if order["created_at"] else None
        })
    return formattedOrders

def getOrderDetail(orderId):
    orderRows = getOrderByOrderId(orderId)
    if not orderRows:
        return None

    order = orderRows[0]

    orderItems = getOrderItemsByOrderId(orderId)
    combinationRows = getCombinationNameByOrderId(orderId)
    combinationNamesByItemId = {}

    for combinationRow in combinationRows:
        orderItemId = combinationRow["order_item_id"]
        val = combinationRow["combination_name"]
        if orderItemId not in combinationNamesByItemId:
            combinationNamesByItemId[orderItemId] = []
        
        if val is not None:
            combinationNamesByItemId[orderItemId].append(val)

    formattedItems = []                 
    for item in orderItems:
        combinationId = item.get("product_variant_combination_id")
        variantCombination = None
        
        if combinationId:
            variantCombination = {
                "idVariantCombination": combinationId,
                "variants": combinationNamesByItemId.get(item["order_item_id"], [])
            }

        formattedItems.append({
            "idProduct": item["product_id"],
            "productName": item["product_name"],
            "variantCombination": variantCombination,
            "quantity": item["quantity"],
            "pricePerItem": int(item["price"]),
            "subtotal": int(item["price"] * item["quantity"]),
        })
    
    totalPrice = int(order["total_price"])
    totalDays = calculateDurationDays(order['rental_start'], order['rental_end'])
    productTotal = sum(item["price"] * item["quantity"] for item in orderItems)
    subtotalBeforeShipping = sum(item["price"] * item["quantity"] for item in orderItems) * totalDays
    subtotalBeforeShippingDP = subtotalBeforeShipping // 2
    shippingCost = int(order["shipping_cost"])
    totalDP = subtotalBeforeShippingDP + shippingCost
    remainingPayment = subtotalBeforeShippingDP

    return {
        "idOrder": order["order_id"],
        "recipientName": order["recipient_name"],
        "rentalStart": order["rental_start"],
        "rentalEnd": order["rental_end"],
        "phoneNumber": order["phone_number"],
        "shippingAddress": order["shipping_address"],
        "city": order["city"],
        "productTotal": int(productTotal),
        "shippingCost": shippingCost,
        "totalPrice": totalPrice,
        "subtotalBeforeShipping": int(subtotalBeforeShipping),
        "subtotalBeforeShippingDP": int(subtotalBeforeShippingDP),
        "totalDP": int(totalDP),
        "remainingPayment": int(remainingPayment),
        "status": order["status_name"],
        "createdAt": order["created_at"].strftime('%Y-%m-%d %H:%M:%S') if order["created_at"] else None,
        "items": formattedItems,
    }