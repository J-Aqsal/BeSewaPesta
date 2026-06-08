from django.contrib.auth.models import User, Group


def getAdminListRepo():
    # Fetch users in 'Admin' group
    admins = User.objects.filter(groups__name='Admin').order_by('-id')
    
    results = []
    for admin in admins:
        results.append({
            "id": admin.id,
            "username": admin.username,
            "full_name": admin.first_name,
            "is_active": admin.is_active,
            "role": "Admin" # Since we filtered by group 'Admin'
        })
    return results


def deleteAdminRepo(userId):
    User.objects.filter(id=userId).delete()
