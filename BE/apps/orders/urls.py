from django.urls import path
from .views import ShippingCostAPIView, CheckoutAPIView, RentalSummaryAPIView

urlpatterns = [
    path("shipping-cost/", ShippingCostAPIView.as_view()),
    path("checkout/", CheckoutAPIView.as_view()),
    path("summary/", RentalSummaryAPIView.as_view()),
]
