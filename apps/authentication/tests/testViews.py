from rest_framework.test import APITestCase
from django.contrib.auth.models import User, Group
from rest_framework_simplejwt.tokens import RefreshToken
from utils.constants import SUCCESS_CODE, BAD_REQUEST_CODE

class AuthAPIViewTest(APITestCase):
    def setUp(self):
        self.superAdminGroup = Group.objects.create(name='Super Admin')
        self.user = User.objects.create_user(username='admin', password='123', first_name='Admin', last_name='Satu')
        self.user.groups.add(self.superAdminGroup)

    def testLoginSuccess(self):
        """
        Input: POST request ke /api/auth/login/ dengan username dan password yang benar.
        Skenario: User melakukan login.
        Expected Output: Status 200 OK, accessToken dan refreshToken tersimpan di cookie.
        """
        payload = {
            "username": "admin",
            "password": "123"
        }
        response = self.client.post("/api/auth/login/", payload, format='json')
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertIn("accessToken", response.cookies)
        self.assertIn("refreshToken", response.cookies)

    def testLoginFailed(self):
        """
        Input: POST request ke /api/auth/login/ dengan password salah.
        Skenario: User gagal login karena password salah.
        Expected Output: Status 401 Unauthorized (karena SimpleJWT TokenObtainPairView default).
        """
        payload = {
            "username": "admin",
            "password": "wrongpassword"
        }
        response = self.client.post("/api/auth/login/", payload, format='json')
        self.assertEqual(response.status_code, 401)

    def testLoginFailedWrongUsername(self):
        """
        Input: POST request ke /api/auth/login/ dengan username yang tidak terdaftar.
        Skenario: User gagal login karena username salah/tidak ditemukan.
        Expected Output: Status 401 Unauthorized.
        """
        payload = {
            "username": "admin_tidak_ada",
            "password": "123"
        }
        response = self.client.post("/api/auth/login/", payload, format='json')
        self.assertEqual(response.status_code, 401)

    def testRefreshTokenSuccess(self):
        """
        Input: POST request ke /api/auth/refresh/ dengan refreshToken di cookie.
        Skenario: User meremajakan token akses yang kadaluarsa.
        Expected Output: Status 200 OK, accessToken baru di set di cookie.
        """
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["refreshToken"] = str(refresh)
        
        response = self.client.post("/api/auth/refresh/")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertIn("accessToken", response.cookies)

    def testRefreshTokenMissing(self):
        """
        Input: POST request ke /api/auth/refresh/ tanpa refreshToken di cookie.
        Skenario: User mencoba meremajakan token tanpa menyertakan cookie refreshToken.
        Expected Output: Status 401 Unauthorized.
        """
        response = self.client.post("/api/auth/refresh/")
        self.assertEqual(response.status_code, 401)

    def testLogoutSuccess(self):
        """
        Input: POST request ke /api/auth/logout/ dengan refreshToken di cookie.
        Skenario: User logout dan menghapus sesi.
        Expected Output: Status 200 OK, cookies dihapus.
        """
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["refreshToken"] = str(refresh)
        self.client.cookies["accessToken"] = str(refresh.access_token)

        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertEqual(response.cookies["refreshToken"].value, "")
        self.assertEqual(response.cookies["accessToken"].value, "")

    def testLogoutMissingToken(self):
        """
        Input: POST request ke /api/auth/logout/ tanpa refreshToken.
        Skenario: User mencoba logout tanpa token yang valid.
        Expected Output: Status 400 Bad Request.
        """
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)

    def testMeSuccess(self):
        """
        Input: GET request ke /api/auth/me/ dengan authentication header yang valid.
        Skenario: Mendapatkan data user yang sedang login.
        Expected Output: Status 200 OK, mengembalikan data user (id, username, fullName, groups).
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        
        data = response.json()["data"]
        self.assertEqual(data["username"], "admin")
        self.assertEqual(data["fullName"], "Admin Satu")
        self.assertIn("Super Admin", data["groups"])

    def testMeUnauthenticated(self):
        """
        Input: GET request ke /api/auth/me/ tanpa authentication header.
        Skenario: Mengambil data diri saat tidak login.
        Expected Output: Status 401 Unauthorized.
        """
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)
