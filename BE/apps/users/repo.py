from utils.db import dbFetch

def getAdminListRepo():
    query = """
        SELECT 
            u.id, 
            u.username, 
            u.first_name as full_name,
            u.is_active,
            g.name as role
        FROM auth_user u
        JOIN auth_user_groups ug ON u.id = ug.user_id
        JOIN auth_group g ON ug.group_id = g.id
        WHERE g.name = 'Admin'
        ORDER BY u.id DESC
    """
    return dbFetch(query, fetchAll=True)

def deleteAdminRepo(userId):
    from utils.db import dbExecute
    query = "DELETE FROM auth_user WHERE id = %s"
    dbExecute(query, [userId])
