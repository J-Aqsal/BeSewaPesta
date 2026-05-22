from django.urls import path

from .views import CartAPIView


urlpatterns = [
    path("", CartAPIView.as_view()),
]