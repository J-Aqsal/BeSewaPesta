from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import LoginSerializer


class LoginAPIView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]


class RefreshTokenAPIView(TokenRefreshView):
    permission_classes = [AllowAny]