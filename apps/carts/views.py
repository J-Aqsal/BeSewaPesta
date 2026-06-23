from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .services import (
    getCartDetailByGuestId, 
    addItemToCart, 
    removeItemFromCart,
    updateItemQuantityService
)
from apps.orders.repo import checkPendingOrderRepo
from utils.responses import successResponse, errorResponse
from utils.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE


class CartAPIView(APIView):
    permission_classes = [AllowAny]
    """
    Consolidated Cart API View
    GET: Get cart details
    POST: Add item to cart (Combined Create/Update Cart & Add Item)
    PATCH: Update item quantity
    DELETE: Remove item from cart
    """

    def get(self, request):
        """Get cart details by guestId"""
        guestId = request.query_params.get("guestId")

        if not guestId:
            return errorResponse(
                message="guestId is required",
                code=BAD_REQUEST_CODE
            )

        if checkPendingOrderRepo(guestId):
            return errorResponse(
                message="You have a pending order waiting for payment. Please complete it first.",
                code=BAD_REQUEST_CODE
            )

        cartData = getCartDetailByGuestId(guestId)

        if not cartData:
            return errorResponse(
                message="Cart not found",
                code=NOT_FOUND_CODE
            )

        return successResponse(data=cartData)

    def post(self, request):
        """Add item to cart (Combined with Cart creation/update)"""
        guestId = request.data.get("guestId")
        productId = request.data.get("idProduct")
        combinationId = request.data.get("idVariantCombination")
        quantity = request.data.get("quantity", 1)
        startDate = request.data.get("startDate")
        endDate = request.data.get("endDate")

        if not all([guestId, productId, startDate, endDate]):
            return errorResponse(message="guestId, idProduct, startDate, and endDate are required")

        result = addItemToCart(guestId, productId, combinationId, quantity, startDate, endDate)

        if not result["success"]:
            return errorResponse(message=result["message"])

        return successResponse(message=result["message"], data={"cartId": result["cartId"]})

    def patch(self, request):
        """Update specific cart item quantity"""
        guestId = request.data.get("guestId")
        cartItemId = request.data.get("idCartItem")
        quantity = request.data.get("quantity")

        if not all([guestId, cartItemId, quantity is not None]):
            return errorResponse(message="guestId, idCartItem, and quantity are required")

        result = updateItemQuantityService(guestId, cartItemId, quantity)

        if not result["success"]:
            return errorResponse(message=result["message"])

        return successResponse(message=result["message"])

    def delete(self, request):
        """Remove item from cart"""
        guestId = request.data.get("guestId")
        cartItemId = request.data.get("idCartItem")

        if not guestId or not cartItemId:
            return errorResponse(message="guestId and idCartItem are required")

        result = removeItemFromCart(cartItemId, guestId)

        if not result["success"]:
            return errorResponse(message=result["message"])

        return successResponse(message=result["message"])
