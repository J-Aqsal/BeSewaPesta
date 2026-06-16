from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User, Group
from utils.constants import BAD_REQUEST_CODE, SUCCESS_CODE

class AdminManagementAPIViewTest(APITestCase):
    def setUp(self):
        # Create groups
        self.superAdminGroup = Group.objects.create(name='Super Admin')
        self.adminGroup = Group.objects.create(name='Admin')
        
        # Create Super Admin
        self.superAdmin = User.objects.create_user(username='superadmin', password='123', first_name='Super Admin')
        self.superAdmin.groups.add(self.superAdminGroup)
        
        # Create Admin
        self.admin = User.objects.create_user(username='admin1', password='123', first_name='Admin Satu')
        self.admin.groups.add(self.adminGroup)
        
        # Force authentication for Super Admin
        self.client.force_authenticate(user=self.superAdmin)

    def testGetAdmins(self):
        """
        Input: GET request ke /api/users/admins/
        Skenario: Super Admin mengambil daftar semua admin.
        Expected Output: Status 200 OK, daftar admin kembali.
        """
        response = self.client.get("/api/users/manage-admin/")
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        
        data = response.json()['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['username'], 'admin1')

    def testCreateAdminSuccess(self):
        """
        Input: POST request ke /api/users/manage-admin/ dengan username, password, fullName.
        Skenario: Super Admin menambahkan admin baru.
        Expected Output: Status 200 OK.
        """
        payload = {
            "username": "admin2",
            "password": "123",
            "fullName": "Admin Dua"
        }
        response = self.client.post("/api/users/manage-admin/", payload, format='json')
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        self.assertTrue(User.objects.filter(username="admin2").exists())

    def testCreateAdminMissingFields(self):
        """
        Input: POST request ke /api/users/manage-admin/ tanpa password.
        Skenario: Super Admin menambahkan admin baru tapi input tidak lengkap.
        Expected Output: Status 400 Bad Request.
        """
        payload = {
            "username": "admin2",
            "fullName": "Admin Dua"
        }
        response = self.client.post("/api/users/manage-admin/", payload, format='json')
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)
        self.assertFalse(response.json()['success'])

    def testUpdateAdminSuccess(self):
        """
        Input: PATCH request ke /api/users/manage-admin/ membawa idAdmin dan fullName baru.
        Skenario: Super Admin mengubah data admin1.
        Expected Output: Status 200 OK.
        """
        payload = {
            "idAdmin": self.admin.id,
            "fullName": "Admin Satu Updated"
        }
        response = self.client.patch("/api/users/manage-admin/", payload, format='json')
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, "Admin Satu Updated")

    def testUpdateAdminSelfDeactivation(self):
        """
        Input: PATCH request ke /api/users/manage-admin/ membawa idAdmin = id Super Admin, isActive = False.
        Skenario: Super Admin mencoba menonaktifkan dirinya sendiri.
        Expected Output: Status 400 Bad Request.
        """
        payload = {
            "idAdmin": self.superAdmin.id,
            "isActive": False
        }
        response = self.client.patch("/api/users/manage-admin/", payload, format='json')
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)
        self.assertFalse(response.json()['success'])

    def testDeleteAdminSuccess(self):
        """
        Input: DELETE request ke /api/users/manage-admin/ membawa idAdmin.
        Skenario: Super Admin menghapus akun admin1.
        Expected Output: Status 200 OK.
        """
        # In Django TEST client, delete() cannot send JSON body directly like post() unless using specific content_type or passing as data
        response = self.client.delete("/api/users/manage-admin/", {"idAdmin": self.admin.id}, format='json')
        self.assertEqual(response.status_code, SUCCESS_CODE)
        self.assertTrue(response.json()['success'])
        self.assertFalse(User.objects.filter(id=self.admin.id).exists())

    def testDeleteAdminSelfDeletion(self):
        """
        Input: DELETE request ke /api/users/manage-admin/ membawa idAdmin = id Super Admin.
        Skenario: Super Admin mencoba menghapus dirinya sendiri.
        Expected Output: Status 400 Bad Request.
        """
        response = self.client.delete("/api/users/manage-admin/", {"idAdmin": self.superAdmin.id}, format='json')
        self.assertEqual(response.status_code, BAD_REQUEST_CODE)
        self.assertFalse(response.json()['success'])
