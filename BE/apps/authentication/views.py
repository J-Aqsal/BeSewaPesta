from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from utils.responses import successResponse, errorResponse
from .serializers import LoginSerializer
from .services import AuthService


class LoginAPIView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        access_token = serializer.validated_data.get("access")
        refresh_token = serializer.validated_data.get("refresh")
        user = serializer.validated_data.get("user")

        response = successResponse(
            message="Login berhasil"
        )

        response.set_cookie(
            key="accessToken",
            value=access_token,
            httponly=True,
            secure=False,  # True kalau sudah HTTPS
            samesite="Lax",
        )

        response.set_cookie(
            key="refreshToken",
            value=refresh_token,
            httponly=True,
            secure=False,  # True kalau sudah HTTPS
            samesite="Lax",
        )

        return response


class RefreshTokenAPIView(TokenRefreshView):
    permission_classes = [AllowAny]


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return errorResponse("Refresh token is required", code=400)
        
        success, error = AuthService.logout(refresh_token)
        if success:
            return successResponse(message="Successfully logged out")
        else:
            return errorResponse(error, code=400)
