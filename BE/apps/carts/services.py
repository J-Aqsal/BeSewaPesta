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
    deleteCartItem
)

def getCartDetailByGuestId(guestId):
    cart = getCartByGuestId(guestId)

    if not cart:
        return None

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


def upsertCart(guestId, rentalStart, rentalEnd):
    cart = getCartByGuestId(guestId)

    if cart:
        updateCartRentalDates(cart['id'], rentalStart, rentalEnd)
        return {"id": cart['id'], "action": "updated"}
    else:
        new_cart = createCart(guestId, rentalStart, rentalEnd)
        return {"id": new_cart['id'], "action": "created"}


def addItemToCart(guestId, productId, combinationId, quantity):
    cart = getCartByGuestId(guestId)
    if not cart:
        return {"success": False, "message": "Cart not found. Please set rental dates first."}

    if combinationId:
        isValid = validateProductCombination(productId, combinationId)
        if not isValid:
            return {"success": False, "message": "Invalid variant combination for this product."}

    existingItem = getCartItem(cart['id'], productId, combinationId)
    
    if existingItem:
        newQuantity = existingItem['quantity'] + int(quantity)
        updateCartItemQuantity(existingItem['id'], newQuantity)
        return {"success": True, "message": "Item quantity updated in cart.", "cartId": cart['id']}
    else:
        addCartItem(cart['id'], productId, combinationId, quantity)
        return {"success": True, "message": "Item added to cart.", "cartId": cart['id']}


def removeItemFromCart(cartItemId, guestId):
    isValid = validateCartItemOwnership(cartItemId, guestId)
    
    if not isValid:
        return {"success": False, "message": "Item not found or does not belong to your cart."}
    
    deleteCartItem(cartItemId)
    return {"success": True, "message": "Item removed from cart."}
