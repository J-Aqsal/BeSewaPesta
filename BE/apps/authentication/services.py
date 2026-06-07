from .repo import blacklistToken

class AuthService:
    @staticmethod
    def logout(refreshTokenString):
        try:
            blacklistToken(refreshTokenString)
            return True, None
        except Exception as e:
            return False, str(e)
