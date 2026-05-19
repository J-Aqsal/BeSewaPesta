from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Products
from .serializers import (
    ProductCatalogSerializer,
    ProductDetailSerializer,
)
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
    
class ProductDetailAPIView(APIView):
    def post(self, request):
        product_id = request.data.get("idProduct")
        start_date = request.data.get("startDate")
        end_date = request.data.get("endDate")
        
        if not product_id:
            return Response({
                "code": 400,
                "success": False,
                "error": "idProduct wajib diisi"
            }, status=400)
        
        # Ambil 1 produk berdasarkan id
        product = Products.objects.filter(id=product_id).first()

        if product is None:
            return Response({
                "code": 404,
                "success": False,
                "error": "Produk tidak ditemukan"
            }, status=404)

        # Stock product level
        available_stock = calculate_available_stock(
            product,
            start_date,
            end_date,
        )

        serializer = ProductDetailSerializer(
            product,
            context={
                "stock_map": {product.id: available_stock},
                "start_date": start_date,
                "end_date": end_date,
            },
        )

        return Response({"code": 200, "success": True, "data": serializer.data})