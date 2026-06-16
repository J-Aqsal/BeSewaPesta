from apps.products.repo import (
    calculateAvailableStock, 
    calculateAvailableStockForCombinations,
    validateProductCombination
)
from .repo import (
    getCartByGuestId, 
    getCartItemsByCartId, 
    getVariantCombinationDetail, 
    updateCartRentalDates, 
    createCart,
    getCartItem,
    addCartItem,
    getCartItemById,
    updateCartItemQuantity,
    validateCartItemOwnership,
    deleteCartItem,
    updateCartActivity,
    getExistingCategoriesRepo,
    expireCartsRepo
)
from apps.orders.repo import checkPendingOrderRepo
from utils.dates import parse_datetime, to_local_time

def areDatesEqual(dbVal, inputVal):
    if not dbVal or not inputVal:
        return False
    
    dt1 = parse_datetime(dbVal)
    dt2 = parse_datetime(inputVal)
    
    if not dt1 or not dt2:
        return str(dbVal) == str(inputVal)
        
    return dt1.replace(microsecond=0) == dt2.replace(microsecond=0)


def getCartDetailByGuestId(guestId):
    cart = getCartByGuestId(guestId)

    if not cart:
        return None

    updateCartActivity(cart["id"])

    cartId = cart["id"]
    rentalStart = to_local_time(cart["rental_start"])
    rentalEnd = to_local_time(cart["rental_end"])
    cartItems = getCartItemsByCartId(cartId)
    totalPrice = 0    
    items = []

    for item in cartItems:
        productId = item["product_id"]
        combinationId = item["product_variant_combination_id"]
        quantity = item["quantity"]

        if combinationId:
            stockMap = calculateAvailableStockForCombinations(productId, [combinationId], rentalStart, rentalEnd)
            availableStock = stockMap.get(combinationId, 0)
            pricePerItem = item["combination_price"] or 0
        else:
            availableStock = calculateAvailableStock(productId, rentalStart, rentalEnd)
            pricePerItem = item["product_price"] or 0

        subtotalPrice = int(pricePerItem) * int(quantity)
        totalPrice += subtotalPrice
        variantCombination = None

        if combinationId:
            variants = getVariantCombinationDetail(combinationId)
            variantCombination = {
                "idVariantCombination": combinationId,
                "variants": variants
            }

        items.append({
            "idCartItem": item["id"],
            "idProduct": productId,
            "productName": item["product_name"],
            "category": item["category_name"],
            "thumbnail": item["thumbnail"],
            "quantity": quantity,
            "availableStock": availableStock,
            "unitPrice": item["price_unit"],
            "pricePerItem": int(pricePerItem),
            "subtotalPrice": subtotalPrice,
            "variantCombination": variantCombination
        })

    # Gunakan format ISO tanpa timezone (+07) untuk memudahkan FE
    # Jika ingin mengembalikan format full dengan timezone, gunakan: rentalStart.isoformat()
    formattedStart = rentalStart.strftime('%Y-%m-%dT%H:%M:%S') if rentalStart else None
    formattedEnd = rentalEnd.strftime('%Y-%m-%dT%H:%M:%S') if rentalEnd else None

    return {
        "cartId": cartId,
        "totalPrice": totalPrice,
        "rentalStart": formattedStart,
        "rentalEnd": formattedEnd,
        "items": items
    }


def addItemToCart(guestId, productId, combinationId, quantity, startDate=None, endDate=None):
    # Check for pending orders within the last 24 hours
    has_pending = checkPendingOrderRepo(guestId)
    if has_pending:
        return {
            "success": False, 
            "message": "You have a pending order waiting for payment. Please complete it before adding more items to your cart."
        }

    cart = getCartByGuestId(guestId)
    
    if cart:
        cartId = cart['id']
        if startDate and endDate:
            cartItems = getCartItemsByCartId(cartId)
            
            if cartItems:
                if not areDatesEqual(cart['rental_start'], startDate) or not areDatesEqual(cart['rental_end'], endDate):
                    return {"success": False, "message": "Please complete your current cart before changing rental dates."}
            
            updateCartRentalDates(cartId, startDate, endDate)
            effectiveStartDate = startDate
            effectiveEndDate = endDate
        else:
            effectiveStartDate = cart['rental_start']
            effectiveEndDate = cart['rental_end']
    else:
        if not startDate or not endDate:
            return {"success": False, "message": "Rental dates (startDate, endDate) are required for the first item."}
        
        result = createCart(guestId, startDate, endDate)
        cartId = result['id']
        effectiveStartDate = startDate
        effectiveEndDate = endDate


    if combinationId:
        isValid = validateProductCombination(productId, combinationId)
        if not isValid:
            return {"success": False, "message": "Invalid variant combination for this product."}
        
        if effectiveStartDate and effectiveEndDate:
            stockMap = calculateAvailableStockForCombinations(productId, [combinationId], effectiveStartDate, effectiveEndDate)
            availableStock = stockMap.get(combinationId, 0)
        else:
            return {"success": False, "message": "Rental dates (startDate, endDate) are required."}
    else:
        if effectiveStartDate and effectiveEndDate:
            availableStock = calculateAvailableStock(productId, effectiveStartDate, effectiveEndDate)
        else:
            return {"success": False, "message": "Rental dates (startDate, endDate) are required."}

    existingItem = getCartItem(cartId, productId, combinationId)
    
    if existingItem:
        newQuantity = existingItem['quantity'] + int(quantity)
        if newQuantity > availableStock:
            return {"success": False, "message": f"Requested quantity exceeds available stock. Available: {availableStock}"}
        
        updateCartItemQuantity(existingItem['id'], newQuantity)
        updateCartActivity(cartId)
        return {"success": True, "message": "Item quantity updated in cart.", "cartId": cartId}
    else:
        if int(quantity) > availableStock:
            return {"success": False, "message": f"Requested quantity exceeds available stock. Available: {availableStock}"}
            
        addCartItem(cartId, productId, combinationId, quantity)
        updateCartActivity(cartId)
        return {"success": True, "message": "Item added to cart.", "cartId": cartId}


def removeItemFromCart(cartItemId, guestId):
    isValid = validateCartItemOwnership(cartItemId, guestId)
    
    if not isValid:
        return {"success": False, "message": "Item not found or does not belong to your cart."}
    
    cart = getCartByGuestId(guestId)
    if cart:
        updateCartActivity(cart['id'])
        
    deleteCartItem(cartItemId)
    return {"success": True, "message": "Item removed from cart."}


def updateItemQuantityService(guestId, cartItemId, quantity):
    isValid = validateCartItemOwnership(cartItemId, guestId)
    
    if not isValid:
        return {"success": False, "message": "Item not found or does not belong to your cart."}
    
    cart = getCartByGuestId(guestId)
    if cart:
        updateCartActivity(cart['id'])
        
    if int(quantity) <= 0:
        deleteCartItem(cartItemId)
        return {"success": True, "message": "Item removed from cart due to zero quantity."}

    itemDetail = getCartItemById(cartItemId)
    productId = itemDetail['product_id']
    combinationId = itemDetail['product_variant_combination_id']
    startDate = cart['rental_start']
    endDate = cart['rental_end']

    if combinationId:
        stockMap = calculateAvailableStockForCombinations(productId, [combinationId], startDate, endDate)
        availableStock = stockMap.get(combinationId, 0)
    else:
        availableStock = calculateAvailableStock(productId, startDate, endDate)

    if int(quantity) > availableStock:
        return {"success": False, "message": f"Requested quantity exceeds available stock. Available: {availableStock}"}
        
    updateCartItemQuantity(cartItemId, quantity)
    return {"success": True, "message": "Item quantity updated."}


def getExistingCategoriesService(guestId):
    cart = getCartByGuestId(guestId)
    if not cart:
        return []
    
    updateCartActivity(cart['id'])
    return getExistingCategoriesRepo(cart['id'])


def expireInactiveCartsService(hoursThreshold=24):
    count = expireCartsRepo(hoursThreshold)
    return {"success": True, "message": f"Expired {count} inactive carts."}
