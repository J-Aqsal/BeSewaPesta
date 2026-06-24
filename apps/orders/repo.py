from .models import Order, OrderItem, OrderStatus
from django.db.models import F, Q, OuterRef, Subquery
from django.utils import timezone
from datetime import timedelta

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


def insertOrderItem(orderId, productId, quantity, price, combinationId=None, notes=None):
    OrderItem.objects.create(
        order_id=orderId,
        product_id=productId,
        quantity=quantity,
        price=price,
        product_variant_combination_id=combinationId,
        notes=notes
    )


def getOrders(search=""):
    statusMap = {
        "belum bayar": "Pending Payment",
        "bayar 50%": "Down Payment 50%",
        "bayar lunas": "Fully Paid",
        "selesai": "Completed",
        "dibatalkan": "Cancelled",
    }
    orders = Order.objects.select_related('status').annotate(
        order_id=F('id'),
        status_name=F('status__name')
    )
    if search:
        searchStatus = statusMap.get(search.lower(), search)
        orders = orders.filter(
            Q(id__icontains=search) |
            Q(recipient_name__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(status__name__icontains=searchStatus)
        )
    orders = orders.values(
        'order_id', 'guest_id', 'total_price', 'rental_start', 'rental_end',
        'recipient_name', 'phone_number', 'shipping_address', 'city',
        'shipping_cost', 'created_at', 'status_name', 'updated_at'
    ).order_by('-updated_at')
    
    return list(orders)


def getOrderByOrderId(orderId):
    order = Order.objects.select_related('status').filter(id=orderId).annotate(
        order_id=F('id'),
        status_name=F('status__name')
    ).values(
        'order_id', 'guest_id', 'total_price', 'rental_start', 'rental_end',
        'recipient_name', 'phone_number', 'shipping_address', 'city',
        'shipping_cost', 'created_at', 'status_name', 'updated_at'
    )
    
    return list(order)


def getOrderItemsByOrderId(orderId):
    from apps.products.models import ProductGallery

    first_gallery = ProductGallery.objects.filter(
        product_id=OuterRef('product_id')
    ).order_by('display_order', 'id')

    items = OrderItem.objects.filter(order_id=orderId).select_related('product', 'product__category').annotate(
        order_item_id=F('id'),
        product_name=F('product__name'),
        category_name=F('product__category__name'),
        thumbnail=Subquery(first_gallery.values('image_url')[:1])
    ).values(
        'order_item_id', 'product_id', 'product_name', 'quantity', 'price',
        'product_variant_combination_id', 'category_name', 'thumbnail', 'notes'
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
    Order.objects.filter(id=orderId).update(
        status_id=newStatusId,
        updated_at=timezone.now()
    )


def getOrderStatusesRepo():
    return list(OrderStatus.objects.all().values('id', 'name').order_by('id'))


def checkPendingOrderRepo(guestId):
    twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
    return Order.objects.filter(
        guest_id=guestId,
        status_id=1,  # Pending Payment
        created_at__gte=twenty_four_hours_ago
    ).exists()


def cancelExpiredOrdersRepo(hoursThreshold=24):
    from apps.carts.models import Cart, CartItem
    cutoff_time = timezone.now() - timedelta(hours=hoursThreshold)
    
    expired_orders = Order.objects.filter(
        status_id=1,  # Pending Payment
        created_at__lte=cutoff_time
    )
    
    count = 0
    for order in expired_orders:
        cart, created = Cart.objects.get_or_create(
            guest_id=order.guest_id,
            defaults={
                'rental_start': order.rental_start,
                'rental_end': order.rental_end
            }
        )
        
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            cart_item, ci_created = CartItem.objects.get_or_create(
                cart=cart,
                product=item.product,
                product_variant_combination=item.product_variant_combination,
                defaults={
                    'quantity': item.quantity,
                    'notes': item.notes
                }
            )
            if not ci_created:
                cart_item.quantity += item.quantity
                cart_item.save()

        order.status_id = 5  # Cancelled
        order.updated_at = timezone.now()
        order.save()
        count += 1
        
    return count

def getOrderByGuestId(guestId):
    order = Order.objects.select_related('status').filter(guest_id=guestId).annotate(
        order_id=F('id'),
        status_name=F('status__name')
    ).values(
        'order_id', 'guest_id', 'total_price', 'rental_start', 'rental_end',
        'recipient_name', 'phone_number', 'shipping_address', 'city',
        'shipping_cost', 'created_at', 'status_name', 'updated_at'
    )
    
    return list(order)

