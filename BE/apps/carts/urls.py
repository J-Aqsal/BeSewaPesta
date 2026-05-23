from django.urls import path

from .views import CartDetailAPIView, CartUpsertAPIView, CartAddItemAPIView, CartDeleteItemAPIView


urlpatterns = [
    path("detail/", CartDetailAPIView.as_view()),
    path("upsert/", CartUpsertAPIView.as_view()),
    path("add/", CartAddItemAPIView.as_view()),
    path("delete/", CartDeleteItemAPIView.as_view()),
]
