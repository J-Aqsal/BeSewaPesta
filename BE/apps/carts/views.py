from rest_framework.views import APIView
from .services import getCartDetailByGuestId, upsertCart, addItemToCart
from utils.responses import successResponse, errorResponse
from utils.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE


class CartDetailAPIView(APIView):

    def post(self, request):

        guestId = request.data.get(
            "guestId"
        )

        if not guestId:
            return errorResponse(
                message="guestId is required",
                code=BAD_REQUEST_CODE
            )

        cartData = getCartDetailByGuestId(guestId)

        if not cartData:
            return errorResponse(
                message="Cart not found",
                code=NOT_FOUND_CODE
            )

        return successResponse(data=cartData)


class CartUpsertAPIView(APIView):

    def post(self, request):

        guestId = request.data.get("guestId")
        startDate = request.data.get("startDate")
        endDate = request.data.get("endDate")

        if not guestId:
            return errorResponse(message="guestId is required")

        if not startDate or not endDate:
            return errorResponse(message="startDate and endDate are required")

        result = upsertCart(guestId, startDate, endDate)

        return successResponse(data=result)


class CartAddItemAPIView(APIView):

    def post(self, request):
        guestId = request.data.get("guestId")
        productId = request.data.get("idProduct")
        combinationId = request.data.get("idVariantCombination")
        quantity = request.data.get("quantity", 1)

        if not guestId or not productId:
            return errorResponse(message="guestId and idProduct are required")

        result = addItemToCart(guestId, productId, combinationId, quantity)

        if not result["success"]:
            return errorResponse(message=result["message"])

        return successResponse(message=result["message"], data={"cartId": result["cartId"]})
