from .repo import (
    calculateAvailableStock,
    calculatePriceRange,
    getProductById,
    getProductGalleries,
    getProductSpecifications,
    getProducts,
    getVariantCombinations,
    getVariantTypes,
)

def getProductCatalogData(start_date, end_date):
    catalog = []
    products = getProducts()
    if not products:
        return catalog

    stockMap = calculateAvailableStock(
        [product["id"] for product in products],
        start_date,
        end_date,
    )

    priceValuesMap = getVariantCombinations(
        [product["id"] for product in products],
        start_date,
        end_date,
    )

    for product in products:
        priceRange = calculatePriceRange(product["price"], priceValuesMap.get(product["id"], []))
        stock = stockMap.get(product["id"], 0)
        catalog.append(
            {
                "id": product["id"],
                "name": product["name"],
                "category": product["category_name"],
                "image": product["photo"],
                "isAvailable": stock > 0,
                "minPrice": priceRange["min"],
                "maxPrice": priceRange["max"],
                "priceUnit": product["price_unit"],
                "stock": stock,
            }
        )

    return catalog


def getProductDetailData(product_id, start_date, end_date):
    product = getProductById(product_id)

    if not product:
        return None

    variantTypes = getVariantTypes(product_id)
    variantCombinations, priceValues = getVariantCombinations(
        product_id,
        start_date,
        end_date,
    )

    return {
        "idProduct": product["id"],
        "productName": product["name"],
        "category": product["category_name"],
        "productDescription": product["description"],
        "priceRange": calculatePriceRange(product["price"], priceValues),
        "unitPrice": product["price_unit"],
        "availableStock": calculateAvailableStock(
            product_id,
            start_date,
            end_date,
        ),
        "thumbnail": product["photo"],
        "gallery": getProductGalleries(product_id),
        "variantTypes": variantTypes,
        "variantCombinations": variantCombinations,
        "specifications": getProductSpecifications(product_id),
    }