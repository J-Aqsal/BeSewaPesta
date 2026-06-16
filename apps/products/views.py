from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from utils.responses import successResponse, errorResponse
from utils.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE

from .services import (
    getProductCatalogData,
    getProductDetailData,
)

class ProductListAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        start_date = request.data.get("startDate")
        end_date = request.data.get("endDate")

        products = getProductCatalogData(start_date, end_date)

        if not products:
            return errorResponse(
                message="Products not found",
                code=NOT_FOUND_CODE
            )

        return successResponse(data=products)
    
class ProductDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        product_id = request.data.get("idProduct")
        start_date = request.data.get("startDate")
        end_date = request.data.get("endDate")
        
        if not product_id:
            return errorResponse(
                message="idProduct required",
                code=BAD_REQUEST_CODE
            )

        product = getProductDetailData(product_id, start_date, end_date)

        if not product:
            return errorResponse(
                message="Product not found",
                code=NOT_FOUND_CODE
            )

        return successResponse(data=product)