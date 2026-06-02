from rest_framework.views import APIView
from .services import getUpsellingRecommendations, getCrossSellRecommendations
from utils.responses import successResponse, errorResponse
from utils.constants import BAD_REQUEST_CODE


class UpSellAPIView(APIView):

    def get(self, request):
        """
        Get up-selling recommendations for a product
        """
        productId = request.query_params.get("idProduct")
        variantId = request.query_params.get("idVariantCombination")
        startDate = request.query_params.get("startDate")
        endDate = request.query_params.get("endDate")
        quantity = request.query_params.get("quantity", 1)
        isFromRecommendation = request.query_params.get("isFromRecommendation", "false").lower() == "true"

        if not productId:
            return errorResponse(
                message="idProduct is required",
                code=BAD_REQUEST_CODE
            )

        recommendations = getUpsellingRecommendations(
            productId, 
            variantId, 
            startDate, 
            endDate,
            quantity,
            isFromRecommendation
        )

        return successResponse(data=recommendations)


class CrossSellAPIView(APIView):

    def get(self, request):
        """
        Get cross-selling recommendations based on cart content
        """
        guestId = request.query_params.get("guestId")

        if not guestId:
            return errorResponse(
                message="guestId is required",
                code=BAD_REQUEST_CODE
            )

        recommendations = getCrossSellRecommendations(guestId)

        return successResponse(data=recommendations)
