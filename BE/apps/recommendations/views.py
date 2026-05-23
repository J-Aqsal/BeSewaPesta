from rest_framework.views import APIView
from .services import getUpsellingRecommendations, getCrossSellRecommendations
from utils.responses import successResponse, errorResponse
from utils.constants import BAD_REQUEST_CODE


class UpSellAPIView(APIView):

    def post(self, request):

        productId = request.data.get("idProduct")
        variantId = request.data.get("idVariantCombination")
        startDate = request.data.get("startDate")
        endDate = request.data.get("endDate")
        quantity = request.data.get("quantity", 1)

        if not productId:
            return errorResponse(
                message="idProduct is required",
                code=BAD_REQUEST_CODE
            )

        # variantId can be None if the source product has no variants selected
        
        recommendations = getUpsellingRecommendations(
            productId, 
            variantId, 
            startDate, 
            endDate,
            quantity
        )

        return successResponse(data=recommendations)


class CrossSellAPIView(APIView):

    def post(self, request):
        guestId = request.data.get("guestId")

        if not guestId:
            return errorResponse(
                message="guestId is required",
                code=BAD_REQUEST_CODE
            )

        recommendations = getCrossSellRecommendations(guestId)

        return successResponse(data=recommendations)
