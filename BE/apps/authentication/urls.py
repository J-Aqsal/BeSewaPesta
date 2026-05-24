from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import LoginAPIView

urlpatterns = [
    path('login/', csrf_exempt(LoginAPIView.as_view())),
]