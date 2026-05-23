import math
from datetime import datetime, timedelta
from django.db import transaction
from apps.carts.services import getCartDetailByGuestId
from apps.carts.queries import clearCart
from .queries import insertOrder, insertOrderItem

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
