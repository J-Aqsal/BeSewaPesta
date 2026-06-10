from django.urls import path
from .views import (
    OrderAPIView, 
    OrderDetailAPIView, 
    OrderShippingAPIView, 
    OrderSummaryAPIView, 
    OrderStatusesAPIView,
    OrderCheckoutAPIView
)

urlpatterns = [
    path("", OrderAPIView.as_view()),
    path("detail/", OrderDetailAPIView.as_view()),
    path("shipping/", OrderShippingAPIView.as_view()),
    path("summary/", OrderSummaryAPIView.as_view()),
    path("statuses/", OrderStatusesAPIView.as_view()),
    path("checkout-data/", OrderCheckoutAPIView.as_view()),
]
