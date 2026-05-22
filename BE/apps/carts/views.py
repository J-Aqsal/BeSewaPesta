from rest_framework.views import APIView
from .services import getCartDetailByGuestId
from utils.responses import successResponse, errorResponse
from utils.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE


class CartAPIView(APIView):

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
    