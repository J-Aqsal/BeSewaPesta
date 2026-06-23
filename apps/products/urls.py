from django.urls import path

from .views import ProductListAPIView, ProductDetailAPIView


urlpatterns = [
    path("", ProductListAPIView.as_view()),
    path("detail/", ProductDetailAPIView.as_view()),
]