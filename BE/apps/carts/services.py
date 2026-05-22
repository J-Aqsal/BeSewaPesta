from apps.products.queries import calculateAvailableStock, calculateAvailableStockForCombinations

from .queries import getCartByGuestId, getCartItemsByCartId, getVariantCombinationDetail



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

            product = {
                "id": productId,
                "total_stock": item["total_stock"]
            }

            availableStock = calculateAvailableStock(product["id"], rentalStart, rentalEnd)
            

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