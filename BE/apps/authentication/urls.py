from django.urls import path
from .views import LoginAPIView, RefreshTokenAPIView, LogoutAPIView

urlpatterns = [
    path('login/', LoginAPIView.as_view()),
    path('refresh/', RefreshTokenAPIView.as_view()),
    path('logout/', LogoutAPIView.as_view()),
]
