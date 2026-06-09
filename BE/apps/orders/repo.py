from .models import Order, OrderItem, OrderStatus
from django.db.models import F


def insertOrder(guestId, totalPrice, statusId, rentalStart, rentalEnd, recipientName, phoneNumber, shippingAddress, city, shippingCost):
    order = Order.objects.create(
        guest_id=guestId,
        total_price=totalPrice,
        status_id=statusId,
        rental_start=rentalStart,
        rental_end=rentalEnd,
        recipient_name=recipientName,
        phone_number=phoneNumber,
        shipping_address=shippingAddress,
        city=city,
        shipping_cost=shippingCost
    )
    return {"id": order.id}


def insertOrderItem(orderId, productId, quantity, price, combinationId=None):
    OrderItem.objects.create(
        order_id=orderId,
        product_id=productId,
        quantity=quantity,
        price=price,
        product_variant_combination_id=combinationId
    )


def getOrders():
    orders = Order.objects.select_related('status').annotate(
        order_id=F('id'),
        status_name=F('status__name')
    ).values(
        'order_id', 'guest_id', 'total_price', 'rental_start', 'rental_end',
        'recipient_name', 'phone_number', 'shipping_address', 'city',
        'shipping_cost', 'created_at', 'status_name'
    ).order_by('-created_at')
    
    return list(orders)


def getOrderByOrderId(orderId):
    order = Order.objects.select_related('status').filter(id=orderId).annotate(
        order_id=F('id'),
        status_name=F('status__name')
    ).values(
        'order_id', 'guest_id', 'total_price', 'rental_start', 'rental_end',
        'recipient_name', 'phone_number', 'shipping_address', 'city',
        'shipping_cost', 'created_at', 'status_name'
    )
    
    return list(order)


def getOrderItemsByOrderId(orderId):
    items = OrderItem.objects.filter(order_id=orderId).select_related('product', 'product__category').annotate(
        order_item_id=F('id'),
        product_name=F('product__name'),
        category_name=F('product__category__name'),
        thumbnail=F('product__photo')
    ).values(
        'order_item_id', 'product_id', 'product_name', 'quantity', 'price',
        'product_variant_combination_id', 'category_name', 'thumbnail'
    )
    
    return list(items)


def getCombinationNameByOrderId(orderId):
    from apps.products.models import ProductVariantCombinationOption
    
    options = ProductVariantCombinationOption.objects.filter(
        product_variant_combination__orderitem__order_id=orderId
    ).annotate(
        order_item_id=F('product_variant_combination__orderitem__id'),
        combination_name=F('variant_option__value')
    ).values('order_item_id', 'combination_name').order_by('order_item_id')

    return list(options)


def updateOrderStatus(orderId, newStatusId):
    Order.objects.filter(id=orderId).update(status_id=newStatusId)


def getOrderStatusesRepo():
    return list(OrderStatus.objects.all().values('id', 'name').order_by('id'))
