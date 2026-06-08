from apps.products.repo import (
    calculateAvailableStock, 
    calculateAvailableStockForCombinations,
    getAllProductFeatures,
    getProductCategoryCandidates,
    getProductCategoryInfo,
    getCombinationVariantDetails,
    getSimilarCombinationsWithHigherPrice
)
from apps.carts.repo import getCartItemsByCartId, getCartByGuestId
from .repo import getProductUpsellRelations

def getUpsellingRecommendations(productId, variantId=None, startDate=None, endDate=None, quantity=1, isFromRecommendation=False):
    if isFromRecommendation:
        return []

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        quantity = 1

    if variantId:

        variantDetails = getCombinationVariantDetails(variantId)
        if not variantDetails:
            return []
            
        currentPrice = variantDetails[0]['price']
        actualProductId = variantDetails[0]['product_id']
        
        upsellDimensionTypeId = None
        currentUpsellOptionId = None
        fixedOptionIds = []
        
        for detail in variantDetails:
            if detail['is_upsell_dimension']:
                upsellDimensionTypeId = detail['variant_type_id']
                currentUpsellOptionId = detail['variant_option_id']
            else:
                fixedOptionIds.append(detail['variant_option_id'])
        
        if not upsellDimensionTypeId:
            return []
            
        upsellCombinations = getSimilarCombinationsWithHigherPrice(
            actualProductId, 
            currentPrice, 
            upsellDimensionTypeId, 
            currentUpsellOptionId,
            fixedOptionIds
        )
        
        recommendations = []
        for combo in upsellCombinations:
            stockMap = calculateAvailableStockForCombinations(actualProductId, [combo['id']], startDate, endDate)
            availableStock = stockMap.get(combo['id'], 0)
            
            if availableStock >= quantity:
                recommendations.append({
                    "idUpsell": combo['id'],
                    "idProduct": actualProductId,
                    "productName": combo['product_name'],
                    "thumbnail": combo['product_photo'],
                    "price": int(combo['price']) if combo['price'] is not None else 0,
                    "priceUnit": combo['price_unit'],
                    "availableStock": availableStock,
                    "idVariantCombination": combo['id']
                })
        return recommendations

    else:        
        return _get_product_upsell_recursive(productId, startDate, endDate, quantity, visited=set())

def _get_product_upsell_recursive(productId, startDate, endDate, quantity, visited):
    if productId in visited:
        return []
    visited.add(productId)

    relations = getProductUpsellRelations(productId)
    recommendations = []

    for rel in relations:
        targetProductId = rel['target_product_id']
        availableStock = calculateAvailableStock(targetProductId, startDate, endDate)
        
        if availableStock >= quantity:
            recommendations.append({
                "idUpsell": rel['id'],
                "idProduct": targetProductId,
                "productName": rel['product_name'],
                "thumbnail": rel['product_photo'],
                "price": int(rel['product_price']) if rel['product_price'] is not None else 0,
                "priceUnit": rel['price_unit'],
                "availableStock": availableStock,
                "idVariantCombination": None
            })
        else:
            fallback_recs = _get_product_upsell_recursive(targetProductId, startDate, endDate, quantity, visited)
            recommendations.extend(fallback_recs)

    return recommendations


def calculateWeightedJaccard(features1, features2):
    keys = set(features1) | set(features2)
    if not keys:
        return 0.0

    intersection = sum(
        min(features1.get(k, 0), features2.get(k, 0))
        for k in keys
    )
    union = sum(
        max(features1.get(k, 0), features2.get(k, 0))
        for k in keys
    )

    return intersection / union if union else 0.0


def getCrossSellRecommendations(guestId):
    
    cart = getCartByGuestId(guestId)
    if not cart:
        return []
    
    cartId = cart['id']
    startDate = cart['rental_start']
    endDate = cart['rental_end']

    cartItems = getCartItemsByCartId(cartId)
    if not cartItems:
        return []

    cartProductIds = [item['product_id'] for item in cartItems]
    cartProducts = getProductCategoryInfo(cartProductIds)
    cartCategoryIds = list(set([p['category_id'] for p in cartProducts]))

    cartFeatures = {}
    rawCartFeatures = getAllProductFeatures(cartProductIds)
    for row in rawCartFeatures:
        name = row['name']
        weight = float(row['weight'])
        cartFeatures[name] = max(cartFeatures.get(name, 0), weight)

    candidates = getProductCategoryCandidates(cartCategoryIds)
    candidateIds = [c['id'] for c in candidates]
    
    if not candidateIds:
        return []

    allCandidateFeatures = getAllProductFeatures(candidateIds)
    candidateFeaturesMap = {}
    for row in allCandidateFeatures:
        p_id = row['product_id']
        if p_id not in candidateFeaturesMap:
            candidateFeaturesMap[p_id] = {}
        candidateFeaturesMap[p_id][row['name']] = float(row['weight'])

    scoredCandidates = []
    for candidate in candidates:
        p_id = candidate['id']
        features = candidateFeaturesMap.get(p_id, {})
        score = calculateWeightedJaccard(cartFeatures, features)
        
        if score > 0:
            scoredCandidates.append({
                "score": score,
                "product": candidate
            })

    scoredCandidates.sort(key=lambda x: x['score'], reverse=True)

    recommendations = []
    for item in scoredCandidates:
        if len(recommendations) >= 5:
            break
            
        prod = item['product']
        availableStock = calculateAvailableStock(prod['id'], startDate, endDate)
        
        # Only add to recommendations if stock is available
        if availableStock > 0:
            recommendations.append({
                "id": prod['id'],
                "name": prod['name'],
                "image": prod['photo'],
                "price": int(prod['price']) if prod['price'] is not None else 0,
                "priceUnit": prod['price_unit'],
                "stock": availableStock
            })

    return recommendations
