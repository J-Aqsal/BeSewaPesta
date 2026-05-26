from django.urls import path
from .views import AdminManagementAPIView

urlpatterns = [
    path('manage-admin/', AdminManagementAPIView.as_view()),
]
