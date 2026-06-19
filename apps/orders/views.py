from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from apps.authentication.permissions import IsAdminOrSuperAdmin
from apps.carts.services import getCartDetailByGuestId
from .services import (
    calculateShippingCostService, 
    processCheckout, 
    getRentalSummaryService, 
    getAllOrders, 
    getOrderDetail,
    updateOrderStatusService,
    getOrderStatusesService,
    checkoutDataService
)
from utils.responses import successResponse, errorResponse
from utils.constants import BAD_REQUEST_CODE


class OrderAPIView(APIView):
    """
    Main Order Management
    GET: List all orders
    POST: Checkout (create order)
    PATCH: Update order status
    """
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrSuperAdmin()]

    def get(self, request):
        """Action: List Orders"""
        page = int(request.GET.get("page", 1))
        pageSize = int(request.GET.get("pageSize", 10))
        sortBy = request.GET.get("sortBy", "updated_at")
        sortOrder = request.GET.get("sortOrder", "desc")
        search = request.GET.get("search", "")
        if page < 1 or pageSize < 1:
            return errorResponse(message="page and pageSize must be positive integers")
        
        if sortOrder not in ["asc", "desc"]:
            return errorResponse(message="sortOrder must be asc or desc")
        
        result = getAllOrders(page=page, pageSize=pageSize, sortBy=sortBy, sortOrder=sortOrder, search=search)
        
        if not result["success"]:
            return errorResponse(message=result["message"])

        return successResponse(message=result["message"], data=result["data"])


    def post(self, request):
        """Action: Checkout"""
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
        """Action: Update Status"""
        orderId = request.data.get("orderId")
        statusId = request.data.get("statusId")

        if not orderId or not statusId:
            return errorResponse(message="orderId and statusId are required")
        
        result = updateOrderStatusService(orderId, statusId)
        
        if not result["success"]:
            return errorResponse(message=result["message"])
            
        return successResponse(message=result["message"])


class OrderDetailAPIView(APIView):
    """
    Get specific order details
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def get(self, request):
        orderId = request.query_params.get("orderId")
        
        if not orderId:
            return errorResponse(message="orderId is required", code=BAD_REQUEST_CODE)

        orderData = getOrderDetail(orderId)
        
        if not orderData:
            return errorResponse(message="Order not found")

        return successResponse(data=orderData)


class OrderShippingAPIView(APIView):
    permission_classes = [AllowAny]
    """
    Calculate shipping cost based on city
    """
    def get(self, request):
        guestId = request.query_params.get("guestId")
        city = request.query_params.get("city")

        if not guestId or not city:
            return errorResponse(message="guestId and city are required", code=BAD_REQUEST_CODE)

        cartData = getCartDetailByGuestId(guestId)
        if not cartData:
            return errorResponse(message="Cart not found")
            
        shippingCost = calculateShippingCostService(cartData['totalPrice'], city)
        return successResponse(data={"shippingCost": shippingCost})


class OrderSummaryAPIView(APIView):
    permission_classes = [AllowAny]
    """
    Calculate rental summary (days, total, DP)
    """
    def get(self, request):
        guestId = request.query_params.get("guestId")

        if not guestId:
            return errorResponse(message="guestId is required", code=BAD_REQUEST_CODE)

        summary = getRentalSummaryService(guestId)
        if not summary:
            return errorResponse(message="Cart is empty or not found")
            
        return successResponse(data=summary)


class OrderStatusesAPIView(APIView):
    """
    Get all available order statuses for dropdown/selection
    """
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]

    def get(self, request):
        statuses = getOrderStatusesService()
        return successResponse(data=statuses)

class OrderCheckoutAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        guestId = request.query_params.get("guestId")
        
        if not guestId:
            return errorResponse(message="guestId is required", code=BAD_REQUEST_CODE)

        orderData = checkoutDataService(guestId)
        
        if not orderData:
            return errorResponse(message="Order not found")

        return successResponse(data=orderData)