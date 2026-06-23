from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get("accessToken")

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception:
            # Jika token tidak valid/expired, biarkan request berlanjut sebagai Anonymous.
            # 401 akan diberikan oleh Permission class jika endpoint tersebut memang butuh login.
            return None