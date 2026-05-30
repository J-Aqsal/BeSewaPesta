from rest_framework.views import APIView
from .services import (
    getCartDetailByGuestId, 
    upsertCart, 
    addItemToCart, 
    removeItemFromCart,
    updateItemQuantityService
)
from utils.responses import successResponse, errorResponse
from utils.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE


class CartAPIView(APIView):
    """
    Consolidated Cart API View
    GET: Get cart details
    POST: Add item to cart
    PATCH: Upsert cart (rental dates)
    PUT: Update item quantity
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

        cartData = getCartDetailByGuestId(guestId)

        if not cartData:
            return errorResponse(
                message="Cart not found",
                code=NOT_FOUND_CODE
            )

        return successResponse(data=cartData)

    def patch(self, request):
        """Upsert cart (set/update rental dates)"""
        guestId = request.data.get("guestId")
        startDate = request.data.get("startDate")
        endDate = request.data.get("endDate")

        if not guestId:
            return errorResponse(message="guestId is required")

        if not startDate or not endDate:
            return errorResponse(message="startDate and endDate are required")

        result = upsertCart(guestId, startDate, endDate)

        return successResponse(data=result)

    def put(self, request):
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

    def post(self, request):
        """Add item to cart"""
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
