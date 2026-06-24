from django.contrib.auth.models import User, Group
from .repo import getAdminListRepo

def getAdminListService():
    admins = getAdminListRepo()
    formattedAdmins = []
    for admin in admins:
        formattedAdmins.append({
            "id": admin["id"],
            "username": admin["username"],
            "fullName": admin["full_name"],
            "role": admin["role"],
            "isActive": bool(admin["is_active"])
        })
    return formattedAdmins

def createAdminService(username, password, fullName, isActive=True):
    if ' ' in username:
        return {"success": False, "message": "Username cannot contain spaces."}
        
    if User.objects.filter(username=username).exists():
        return {"success": False, "message": "Username already exists."}
    
    try:
        user = User.objects.create_user(
            username=username, 
            password=password,
            first_name=fullName
        )
        
        user.is_active = isActive
        user.save()
        
        group, _ = Group.objects.get_or_create(name='Admin')
        user.groups.add(group)
        
        return {"success": True, "message": "Admin account created successfully."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def deleteAdminService(userId):
    try:
        user = User.objects.get(id=userId)
        
        if user.groups.filter(name='Super Admin').exists():
            return {"success": False, "message": "Cannot delete a Super Admin account."}
            
        user.delete()
        return {"success": True, "message": "Admin account deleted successfully."}
    except User.DoesNotExist:
        return {"success": False, "message": "User not found."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def editAdminService(userId, username=None, fullName=None, password=None, isActive=None):
    try:
        user = User.objects.get(id=userId)
        
        if username:
            if ' ' in username:
                return {"success": False, "message": "Username cannot contain spaces."}
            if User.objects.filter(username=username).exclude(id=userId).exists():
                return {"success": False, "message": "Username already taken by another account."}
            user.username = username
        
        if fullName:
            user.first_name = fullName
            
        if password:
            user.set_password(password)
            
        if isActive is not None:
            user.is_active = isActive
            
        user.save()
        return {"success": True, "message": "Admin account updated successfully."}
    except User.DoesNotExist:
        return {"success": False, "message": "User not found."}
    except Exception as e:
        return {"success": False, "message": str(e)}
