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
    updateCartItemQuantity,
    validateCartItemOwnership,
    deleteCartItem,
    updateCartActivity,
    getExistingCategoriesRepo,
    expireCartsRepo
)

def getCartDetailByGuestId(guestId):
    cart = getCartByGuestId(guestId)

    if not cart:
        return None

    # Update activity on view
    updateCartActivity(cart["id"])

    cartId = cart["id"]
    rentalStart = cart["rental_start"]
    rentalEnd = cart["rental_end"]
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

    return {
        "cartId": cartId,
        "totalPrice": totalPrice,
        "rentalStart": rentalStart,
        "rentalEnd": rentalEnd,
        "items": items
    }


def addItemToCart(guestId, productId, combinationId, quantity, startDate, endDate):
    cart = getCartByGuestId(guestId)
    
    # Helper to parse and compare dates flexibly
    def areDatesEqual(dbVal, inputVal):
        if not dbVal or not inputVal:
            return False
        try:
            from datetime import datetime
            formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']
            inputDt = None
            for fmt in formats:
                try:
                    inputDt = datetime.strptime(inputVal.split('.')[0], fmt)
                    break
                except:
                    continue

            if not inputDt:
                return str(dbVal) == str(inputVal)

            dbDt = dbVal if isinstance(dbVal, datetime) else None
            if dbDt:
                return dbDt.replace(microsecond=0) == inputDt

            return str(dbVal) == str(inputDt)
        except:
            return str(dbVal) == str(inputVal)

    if cart:
        cartId = cart['id']
        cartItems = getCartItemsByCartId(cartId)

        if cartItems:
            if not areDatesEqual(cart['rental_start'], startDate) or not areDatesEqual(cart['rental_end'], endDate):
                return {"success": False, "message": "Please complete your current cart before changing rental dates."}

        updateCartRentalDates(cartId, startDate, endDate)
    else:
        result = createCart(guestId, startDate, endDate)
        cartId = result['id']


    if combinationId:
        isValid = validateProductCombination(productId, combinationId)
        if not isValid:
            return {"success": False, "message": "Invalid variant combination for this product."}

    existingItem = getCartItem(cartId, productId, combinationId)
    
    if existingItem:
        newQuantity = existingItem['quantity'] + int(quantity)
        updateCartItemQuantity(existingItem['id'], newQuantity)
        updateCartActivity(cartId)
        return {"success": True, "message": "Item quantity updated in cart.", "cartId": cartId}
    else:
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
