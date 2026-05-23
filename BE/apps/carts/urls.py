from django.urls import path

from .views import CartDetailAPIView, CartUpsertAPIView, CartAddItemAPIView


urlpatterns = [
    path("detail/", CartDetailAPIView.as_view()),
    path("upsert/", CartUpsertAPIView.as_view()),
    path("add/", CartAddItemAPIView.as_view()),
]
