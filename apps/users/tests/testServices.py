from django.test import TestCase
from django.contrib.auth.models import User, Group
from apps.users.services import (
    getAdminListService, createAdminService, deleteAdminService, editAdminService
)

class UserServicesTest(TestCase):
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

    def testGetAdminListService(self):
        """
        Input: -
        Skenario: Meminta daftar admin (hanya role Admin, bukan Super Admin).
        Expected Output: Daftar dengan panjang 1 (admin1).
        """
        admins = getAdminListService()
        self.assertEqual(len(admins), 1)
        self.assertEqual(admins[0]['username'], 'admin1')
        self.assertEqual(admins[0]['role'], 'Admin')

    def testCreateAdminServiceSuccess(self):
        """
        Input: username baru, password, fullName.
        Skenario: Membuat admin baru.
        Expected Output: success True, user baru ada di database dan masuk grup 'Admin' serta password di-hash.
        """
        result = createAdminService('admin2', '123', 'Admin Dua', True)
        self.assertTrue(result['success'])
        
        user = User.objects.get(username='admin2')
        self.assertEqual(user.first_name, 'Admin Dua')
        self.assertTrue(user.groups.filter(name='Admin').exists())
        
        # Test: Pastikan password di-hash (tidak tersimpan sebagai plaintext)
        self.assertNotEqual(user.password, '123')
        self.assertTrue(user.check_password('123'))

    def testCreateAdminServiceDuplicateUsername(self):
        """
        Input: username yang sudah ada ('admin1').
        Skenario: Membuat admin dengan username yang duplikat.
        Expected Output: success False.
        """
        result = createAdminService('admin1', '123', 'Admin Dua', True)
        self.assertFalse(result['success'])
        self.assertIn('Username already exists', result['message'])

    def testDeleteAdminServiceSuccess(self):
        """
        Input: id dari admin1.
        Skenario: Menghapus akun admin.
        Expected Output: success True, admin terhapus dari database.
        """
        result = deleteAdminService(self.admin.id)
        self.assertTrue(result['success'])
        self.assertFalse(User.objects.filter(id=self.admin.id).exists())

    def testDeleteAdminServiceSuperAdmin(self):
        """
        Input: id dari superadmin.
        Skenario: Mencoba menghapus Super Admin.
        Expected Output: success False.
        """
        result = deleteAdminService(self.superAdmin.id)
        self.assertFalse(result['success'])
        self.assertIn('Cannot delete a Super Admin', result['message'])

    def testEditAdminServiceSuccess(self):
        """
        Input: id dari admin1, fullName baru.
        Skenario: Mengubah nama lengkap admin1.
        Expected Output: success True, nama admin1 di database berubah.
        """
        result = editAdminService(self.admin.id, fullName='Admin Satu Edit')
        self.assertTrue(result['success'])
        
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, 'Admin Satu Edit')

    def testEditAdminServiceDuplicateUsername(self):
        """
        Input: id dari admin1, username diubah menjadi 'superadmin'.
        Skenario: Mengubah username admin menjadi username yang sudah terpakai.
        Expected Output: success False.
        """
        result = editAdminService(self.admin.id, username='superadmin')
        self.assertFalse(result['success'])
        self.assertIn('already taken', result['message'])
