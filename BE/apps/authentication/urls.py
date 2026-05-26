from django.urls import path
from .views import LoginAPIView, RefreshTokenAPIView

urlpatterns = [
    path('login/', LoginAPIView.as_view()),
    path('refresh/', RefreshTokenAPIView.as_view()),
]