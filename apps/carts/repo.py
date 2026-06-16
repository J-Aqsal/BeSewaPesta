from .models import Cart, CartItem
from apps.products.models import Product, ProductVariantCombination, VariantOption
from django.db.models import F
import uuid


def getCartByGuestId(guestId):
    cart = Cart.objects.filter(guest_id=guestId).order_by('-created_at').first()

    if not cart:
        return None
    
    return {
        "id": cart.id,
        "guest_id": cart.guest_id,
        "rental_start": cart.rental_start,
        "rental_end": cart.rental_end,
        "created_at": cart.created_at
    }


def getCartItemsByCartId(cartId):
    items = CartItem.objects.filter(cart_id=cartId).select_related(
        'product', 'product__category', 'product_variant_combination'
    ).annotate(
        product_name=F('product__name'),
        photo=F('product__photo'),
        product_price=F('product__price'),
        price_unit=F('product__price_unit'),
        total_stock=F('product__total_stock'),
        category_name=F('product__category__name'),
        combination_price=F('product_variant_combination__price')
    ).values(
        'id', 'product_id', 'quantity', 'product_variant_combination_id',
        'product_name', 'photo', 'product_price', 'price_unit',
        'total_stock', 'category_name', 'combination_price'
    ).order_by('id')

    results = []
    for item in items:
        results.append({
            "id": item['id'],
            "product_id": item['product_id'],
            "quantity": item['quantity'],
            "product_variant_combination_id": item['product_variant_combination_id'],
            "product_name": item['product_name'],
            "thumbnail": item['photo'],
            "product_price": item['product_price'],
            "price_unit": item['price_unit'],
            "total_stock": item['total_stock'],
            "category_name": item['category_name'],
            "combination_price": item['combination_price']
        })

    return results


def getVariantCombinationDetail(combinationId):
    values = VariantOption.objects.filter(
        productvariantcombinationoption__product_variant_combination_id=combinationId
    ).order_by('variant_type_id').values_list('value', flat=True)

    return list(values)


def createCart(guestId, rentalStart, rentalEnd):
    cart = Cart.objects.create(
        guest_id=guestId,
        rental_start=rentalStart,
        rental_end=rentalEnd
    )
    return {"id": cart.id}


def updateCartRentalDates(cartId, rentalStart, rentalEnd):
    Cart.objects.filter(id=cartId).update(
        rental_start=rentalStart, 
        rental_end=rentalEnd,
        updated_at=F('updated_at')
    )
    from django.utils import timezone
    Cart.objects.filter(id=cartId).update(updated_at=timezone.now())


def getCartItem(cartId, productId, combinationId=None):
    query = CartItem.objects.filter(cart_id=cartId, product_id=productId)
    
    if combinationId:
        query = query.filter(product_variant_combination_id=combinationId)
    else:
        query = query.filter(product_variant_combination_id__isnull=True)
    
    item = query.values('id', 'quantity').first()
    return item


def addCartItem(cartId, productId, combinationId, quantity):
    CartItem.objects.create(
        cart_id=cartId,
        product_id=productId,
        product_variant_combination_id=combinationId,
        quantity=quantity
    )


def getCartItemById(cartItemId):
    item = CartItem.objects.filter(id=cartItemId).values(
        'id', 'product_id', 'product_variant_combination_id', 'quantity'
    ).first()
    return item


def updateCartItemQuantity(cartItemId, newQuantity):
    CartItem.objects.filter(id=cartItemId).update(quantity=newQuantity)


def validateCartItemOwnership(cartItemId, guestId):
    return CartItem.objects.filter(id=cartItemId, cart__guest_id=guestId).exists()


def deleteCartItem(cartItemId):
    CartItem.objects.filter(id=cartItemId).delete()


def clearCart(cartId):
    CartItem.objects.filter(cart_id=cartId).delete()
    Cart.objects.filter(id=cartId).delete()


def updateCartActivity(cartId):
    from django.utils import timezone
    Cart.objects.filter(id=cartId).update(updated_at=timezone.now())


def getExistingCategoriesRepo(cartId):
    categories = CartItem.objects.filter(cart_id=cartId).values_list(
        'product__category__name', flat=True
    ).distinct()
    return list(categories)


def expireCartsRepo(hoursThreshold=24):
    from django.utils import timezone
    from datetime import timedelta
    
    threshold_date = timezone.now() - timedelta(hours=hoursThreshold)
    
    inactive_carts = Cart.objects.filter(updated_at__lt=threshold_date)
    count = inactive_carts.count()
    
    if count > 0:
        cart_ids = list(inactive_carts.values_list('id', flat=True))
        CartItem.objects.filter(cart_id__in=cart_ids).delete()
        inactive_carts.delete()
        
    return count
