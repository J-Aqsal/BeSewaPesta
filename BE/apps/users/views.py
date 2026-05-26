from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.authentication.permissions import IsSuperAdmin
from utils.responses import successResponse, errorResponse
from .services import getAdminListService, createAdminService, deleteAdminService, editAdminService

class AdminManagementAPIView(APIView):
    # Seluruh endpoint manajemen admin ini hanya bisa diakses oleh Super Admin
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        """Ambil daftar semua Admin (Super Admin dikecualikan)"""
        admins = getAdminListService()
        return successResponse(data=admins)

    def post(self, request):
        """Tambah akun Admin baru"""
        username = request.data.get("username")
        password = request.data.get("password")
        fullName = request.data.get("fullName")
        isActive = request.data.get("isActive", True)

        if not all([username, password, fullName]):
            return errorResponse(message="Username, password, and fullName are required.")

        result = createAdminService(username, password, fullName, isActive)
        
        if not result["success"]:
            return errorResponse(message=result["message"])
            
        return successResponse(message=result["message"])

    def patch(self, request):
        """Update detail akun Admin (Username, Nama, Password, Status)"""
        idAdmin = request.data.get("idAdmin")
        username = request.data.get("username")
        fullName = request.data.get("fullName")
        password = request.data.get("password")
        isActive = request.data.get("isActive")

        if not idAdmin:
            return errorResponse(message="idAdmin is required.")

        # Mencegah Super Admin menonaktifkan dirinya sendiri
        if idAdmin == request.user.id and isActive is False:
            return errorResponse(message="You cannot deactivate your own account.")

        result = editAdminService(idAdmin, username, fullName, password, isActive)

        if not result["success"]:
            return errorResponse(message=result["message"])

        return successResponse(message=result["message"])

    def delete(self, request):
        """Hapus akun Admin secara permanen"""
        idAdmin = request.data.get("idAdmin")

        if not idAdmin:
            return errorResponse(message="idAdmin is required.")

        # Mencegah Super Admin menghapus dirinya sendiri
        if idAdmin == request.user.id:
            return errorResponse(message="You cannot delete your own account.")

        result = deleteAdminService(idAdmin)

        if not result["success"]:
            return errorResponse(message=result["message"])

        return successResponse(message=result["message"])
