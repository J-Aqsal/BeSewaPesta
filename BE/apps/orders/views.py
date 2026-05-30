from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.carts.services import getCartDetailByGuestId
from .services import (
    calculateShippingCostService, 
    processCheckout, 
    getRentalSummaryService, 
    getAllOrders, 
    getOrderDetail,
    updateOrderStatusService
)
from utils.responses import successResponse, errorResponse
from utils.constants import BAD_REQUEST_CODE

class OrderAPIView(APIView):
    """
    Consolidated Order API
    GET: List all orders or Get detail (if orderId provided)
    POST: Checkout (create order)
    PATCH: Update order status
    """
    
    def get_permissions(self):
        # Checkout (POST) can be accessed by guests, other methods require authentication
        if self.request.method == 'POST':
            return []
        return [IsAuthenticated()]

    def get(self, request):
        orderId = request.query_params.get("orderId")
        
        if orderId:
            # Action: Get Detail
            orderData = getOrderDetail(orderId)
            return successResponse(data=orderData)
        
        # Action: List Orders
        orders = getAllOrders()
        return successResponse(data=orders)

    def post(self, request):
        # Action: Checkout
        guestId = request.data.get("guestId")
        recipientName = request.data.get("recipientName")
        phoneNumber = request.data.get("phoneNumber")
        shippingAddress = request.data.get("shippingAddress")
        city = request.data.get("city")

        if not all([guestId, recipientName, phoneNumber, shippingAddress, city]):
            return errorResponse(message="Missing required checkout information")

        result = processCheckout(guestId, recipientName, phoneNumber, shippingAddress, city)

        if not result["success"]:
            return errorResponse(message=result["message"])

        return successResponse(message=result["message"], data=result["data"])

    def patch(self, request):
        # Action: Update Status
        orderId = request.data.get("orderId")
        statusId = request.data.get("statusId")

        if not orderId or not statusId:
            return errorResponse(message="orderId and statusId are required")
        
        result = updateOrderStatusService(orderId, statusId)
        
        if not result["success"]:
            return errorResponse(message=result["message"])
            
        return successResponse(message=result["message"])


class OrderUtilityAPIView(APIView):
    """
    Utility endpoints for calculations before order creation
    GET: Handles 'shipping' and 'summary' types
    """
    
    def get(self, request):
        calcType = request.query_params.get("type")
        guestId = request.query_params.get("guestId")

        if not calcType or not guestId:
            return errorResponse(message="type and guestId are required", code=BAD_REQUEST_CODE)

        if calcType == "shipping":
            city = request.query_params.get("city")
            if not city:
                return errorResponse(message="city is required for shipping calculation")
            
            cartData = getCartDetailByGuestId(guestId)
            if not cartData:
                return errorResponse(message="Cart not found")
                
            shippingCost = calculateShippingCostService(cartData['totalPrice'], city)
            return successResponse(data={"shippingCost": shippingCost})

        elif calcType == "summary":
            summary = getRentalSummaryService(guestId)
            if not summary:
                return errorResponse(message="Cart is empty or not found")
            return successResponse(data=summary)

        return errorResponse(message="Invalid utility type. Use 'shipping' or 'summary'.")
