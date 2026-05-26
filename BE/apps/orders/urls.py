from django.urls import path
from .views import (
    OrderListAPIView, 
    OrderDetailAPIView, 
    ShippingCostAPIView, 
    CheckoutAPIView, 
    RentalSummaryAPIView,
    OrderStatusUpdateAPIView
)

urlpatterns = [
    path("list/", OrderListAPIView.as_view()),
    path("detail/", OrderDetailAPIView.as_view()),
    path("update-status/", OrderStatusUpdateAPIView.as_view()),
    path("shipping-cost/", ShippingCostAPIView.as_view()),
    path("checkout/", CheckoutAPIView.as_view()),
    path("summary/", RentalSummaryAPIView.as_view()),
]
