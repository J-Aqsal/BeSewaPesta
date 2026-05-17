from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime
from django.utils import timezone

from .models import Products, VariantOptions
from .serializers import ProductCatalogSerializer, ProductDetailSerializer
from .services import calculate_available_stock, calculate_available_stock_for_variant_option

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
        # Ambil dari body request
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
        
        # Hitung available stock
        available_stock = calculate_available_stock(
            product, 
            start_date, 
            end_date
        )
        
        # Hitung stock untuk setiap variant option
        variant_stock_map = {}
        variant_options = VariantOptions.objects.filter(
            variant_type__product_id=product_id
        )
        for option in variant_options:
            variant_stock_map[option.id] = calculate_available_stock_for_variant_option(
                product_id, option.id, start_date, end_date
            )
        
        # Serialize dengan konteks stock dan variant option stock
        serializer = ProductDetailSerializer(
            product,
            context={
                "stock_map": {product.id: available_stock},
                "variant_stock_map": variant_stock_map,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        
        return Response({
            "code": 200,
            "success": True,
            "data": serializer.data
        })