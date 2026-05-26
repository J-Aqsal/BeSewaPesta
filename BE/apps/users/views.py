from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.authentication.permissions import IsSuperAdmin
from utils.responses import successResponse, errorResponse
from .services import getAdminListService, createAdminService, deleteAdminService, editAdminService

class AdminManagementAPIView(APIView):
    # All admin management endpoints can only be accessed by Super Admin
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        """Get a list of all Admins (Super Admin excluded)"""
        admins = getAdminListService()
        return successResponse(data=admins)

    def post(self, request):
        """Add a new Admin account"""
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
        """Update Admin account details (Username, Name, Password, Status)"""
        idAdmin = request.data.get("idAdmin")
        username = request.data.get("username")
        fullName = request.data.get("fullName")
        password = request.data.get("password")
        isActive = request.data.get("isActive")

        if not idAdmin:
            return errorResponse(message="idAdmin is required.")

        # Prevent Super Admin from deactivating their own account
        if idAdmin == request.user.id and isActive is False:
            return errorResponse(message="You cannot deactivate your own account.")

        result = editAdminService(idAdmin, username, fullName, password, isActive)

        if not result["success"]:
            return errorResponse(message=result["message"])

        return successResponse(message=result["message"])

    def delete(self, request):
        """Delete an Admin account permanently"""
        idAdmin = request.data.get("idAdmin")

        if not idAdmin:
            return errorResponse(message="idAdmin is required.")

        # Prevent Super Admin from deleting their own account
        if idAdmin == request.user.id:
            return errorResponse(message="You cannot delete your own account.")

        result = deleteAdminService(idAdmin)

        if not result["success"]:
            return errorResponse(message=result["message"])

        return successResponse(message=result["message"])
