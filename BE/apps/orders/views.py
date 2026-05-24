from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from apps.carts.services import getCartDetailByGuestId
from utils.constants import AUTHENTICATION_FAILED_CODE
from .services import calculateShippingCostService, processCheckout, getRentalSummaryService, getAllOrders, getOrderDetail
from utils.responses import authenticationFailedResponse, successResponse, errorResponse
from apps.authentication.utils import decodeJwtToken

class ShippingCostAPIView(APIView):
    def post(self, request):
        guestId = request.data.get("guestId")
        city = request.data.get("city")

        if not guestId or not city:
            return errorResponse(message="guestId and city are required")

        cartData = getCartDetailByGuestId(guestId)
        if not cartData:
            return errorResponse(message="Cart not found")

        shippingCost = calculateShippingCostService(cartData['totalPrice'], city)
        
        return successResponse(data={"shippingCost": shippingCost})


class CheckoutAPIView(APIView):
    def post(self, request):
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


class RentalSummaryAPIView(APIView):
    def post(self, request):
        guestId = request.data.get("guestId")

        if not guestId:
            return errorResponse(message="guestId is required")

        summary = getRentalSummaryService(guestId)

        if not summary:
            return errorResponse(message="Cart is empty or not found")

        return successResponse(data=summary)

class OrderListAPIView(APIView):
    def get(self, request):
        authHeader = request.headers.get('Authorization')
        if not authHeader:
            return authenticationFailedResponse(message="Authorization header missing")
        token = authHeader.split(' ')[1]
        payload = decodeJwtToken(token)
        if not payload:
            return authenticationFailedResponse(message="Invalid token")
        orders = getAllOrders()
        return successResponse(data=orders)
    
@method_decorator(csrf_exempt, name='dispatch')
class OrderDetailAPIView(APIView):
    authentication_classes = [] # mematikan auth bawaan DRF
    permission_classes = [] # mematikan permission bawaan DRF

    def post(self, request):
        authHeader = request.headers.get('Authorization')
        if not authHeader:
            return authenticationFailedResponse(message="Authorization header missing")
        token = authHeader.split(' ')[1]
        payload = decodeJwtToken(token)
        if not payload:
            return authenticationFailedResponse(message="Invalid token")
        orderId = request.data.get("orderId")
        if not orderId:
            return errorResponse(message="orderId is required")
        orderItems = getOrderDetail(orderId)
        return successResponse(data=orderItems)