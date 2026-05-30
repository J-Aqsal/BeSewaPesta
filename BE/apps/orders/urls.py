from django.urls import path
from .views import OrderAPIView, OrderUtilityAPIView

urlpatterns = [
    path("", OrderAPIView.as_view()),
    path("utility/", OrderUtilityAPIView.as_view()),
]
