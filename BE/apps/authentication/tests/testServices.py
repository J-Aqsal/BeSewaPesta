from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from apps.authentication.services import AuthService

class AuthServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='123')
        self.refresh = RefreshToken.for_user(self.user)
        self.refreshTokenString = str(self.refresh)

    def testLogoutSuccess(self):
        """
        Input: refresh token valid.
        Skenario: Logout dengan token valid.
        Expected Output: Return True, None.
        """
        success, error = AuthService.logout(self.refreshTokenString)
        self.assertTrue(success)
        self.assertIsNone(error)

    def testLogoutInvalidToken(self):
        """
        Input: refresh token invalid/sudah diblacklist.
        Skenario: Logout dengan token tidak valid.
        Expected Output: Return False, error string.
        """
        # First logout will blacklist the token
        AuthService.logout(self.refreshTokenString)
        
        # Second logout will fail because token is already blacklisted
        success, error = AuthService.logout(self.refreshTokenString)
        self.assertFalse(success)
        self.assertIsNotNone(error)
