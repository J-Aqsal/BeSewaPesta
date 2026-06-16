from rest_framework_simplejwt.tokens import RefreshToken

def blacklistToken(refreshTokenString):
    token = RefreshToken(refreshTokenString)
    token.blacklist()
