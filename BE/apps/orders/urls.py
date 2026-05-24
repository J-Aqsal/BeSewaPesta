from django.urls import path
from .views import OrderListAPIView, ShippingCostAPIView, CheckoutAPIView, RentalSummaryAPIView

urlpatterns = [
    path("list/", OrderListAPIView.as_view()),
    path("shipping-cost/", ShippingCostAPIView.as_view()),
    path("checkout/", CheckoutAPIView.as_view()),
    path("summary/", RentalSummaryAPIView.as_view()),
]
