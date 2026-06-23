from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from utils.responses import successResponse, errorResponse
from .services import AuthService


class LoginAPIView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response_data = super().post(request, *args, **kwargs)

        access_token = response_data.data.get("access")
        refresh_token = response_data.data.get("refresh")

        response = successResponse(
            message="Login berhasil"
        )

        response.set_cookie(
            key="accessToken",
            value=access_token,
            httponly=True,
            secure=False,  # True kalau sudah HTTPS
            samesite="Lax",
            path="/",
        )

        response.set_cookie(
            key="refreshToken",
            value=refresh_token,
            httponly=True,
            secure=False,  # True kalau sudah HTTPS
            samesite="Lax",
            path="/",
        )

        return response


class RefreshTokenAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get("refreshToken")

        if not refresh_token:
            return errorResponse(
                "Refresh token is required",
                code=401
            )

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            response = successResponse(
                message="Token refreshed"
            )

            response.set_cookie(
                key="accessToken",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
            )

            return response


        except Exception:
            return errorResponse(
                "Invalid refresh token",
                code=401
            )

class LogoutAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get("refreshToken")

        if not refresh_token:
            return errorResponse("Refresh token is required", code=400)

        success, error = AuthService.logout(refresh_token)

        if success:
            response = successResponse(message="Successfully logged out")

            response.delete_cookie("accessToken")
            response.delete_cookie("refreshToken")

            return response

        return errorResponse(error, code=400)
    
class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return successResponse(
            data={
                "id": user.id,
                "username": user.username,
                "fullName": user.first_name + " " + user.last_name,
                "groups": [
                    group.name for group in user.groups.all()
                ],
            },
            message="Data user berhasil diambil"
        )
