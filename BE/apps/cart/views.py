from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.dbmirror.models import *
from django.utils import timezone

@api_view(['GET'])
def test(request):

    data = Products.objects.select_related('category')\
        .prefetch_related('productcontexts_set__context')
    print(data.values())
    # for p in data:
    #     print(p.id, p.name, p.category.name)

    #     for pc in p.productcontexts_set.all():
    #         print(pc.context.slug, pc.weight)
    return Response({"message": f"test berhasil"})

@api_view(['POST'])
def touch_cart(request):
    guest_id = request.data.get("guest_id")
    print(f"touch_cart called with guest_id: {guest_id} {timezone.now()}")  # Debug print

    now = timezone.now()

    if not guest_id:
        return Response({"error": "guest_id required"}, status=400)

    cart, created = Carts.objects.get_or_create(
        guest_id=guest_id,
        defaults={"created_at": timezone.now(), "updated_at": timezone.now()}
    )

    if not created:
        cart.updated_at = timezone.now()
        cart.save()

    return Response({
        "message": "cart updated",
        "cart_id": cart.id, 
        "updated_at": timezone.localtime(cart.updated_at)
    })
