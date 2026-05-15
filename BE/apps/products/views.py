from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Products
from .serializers import ProductCatalogSerializer
from .services import calculate_available_stock


class ProductListAPIView(APIView):

    def post(self, request):

        start_date = request.data.get(
            "startDate"
        )

        end_date = request.data.get(
            "endDate"
        )

        products = Products.objects.all()

        stock_map = {}

        for product in products:

            stock_map[product.id] = (
                calculate_available_stock(
                    product,
                    start_date,
                    end_date
                )
            )

        serializer = ProductCatalogSerializer(
            products,
            many=True,
            context={
                "stock_map": stock_map
            }
        )

        return Response({
            "code": 200,
            "success": True,
            "data": serializer.data
        })