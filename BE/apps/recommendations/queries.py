from utils.db import dbFetch

def getProductUpsellRelations(productId):
    query = """
        SELECT 
            pur.id,
            pur.target_product_id,
            p.name as product_name,
            p.photo as product_photo,
            p.price as product_price,
            p.price_unit,
            p.total_stock
        FROM product_upsell_relations pur
        JOIN products p ON p.id = pur.target_product_id
        WHERE pur.source_product_id = %s
    """
    return dbFetch(query, [productId], fetchAll=True)
