# routes/users.py
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import logging
from database.queries import UserQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ SCHEMAS ============

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class UserCellUpdate(BaseModel):
    column_name: str
    value: str

# ============ ROUTES ============

@router.get("/", tags=["Users"])
async def get_all_users(authorization: str = Header(None)):
    """GET all users - admin and agronomist see all, farmer sees only themselves"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'users', 'read')
        if user['role'] in ['admin', 'agronomist']:
            users = UserQueries.get_all_users()
            visibility = "all users"
        else:
            users = [UserQueries.get_user_by_id(user_id)]
            visibility = "own profile only"
        logger.info(f"User {user_id} ({user['role']}) retrieved {len(users)} users")
        return {"count": len(users), "user_role": user['role'], "visibility": visibility, "users": users}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@router.get("/{target_id}", tags=["Users"])
async def get_user_by_id(target_id: int, authorization: str = Header(None)):
    """GET user by ID - farmer can only view themselves"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'users', 'read')
        if user['role'] == 'farmer' and user_id != target_id:
            raise HTTPException(status_code=403, detail="Cannot view other users")
        target_user = UserQueries.get_user_by_id(target_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        logger.info(f"User {user_id} retrieved profile of user {target_id}")
        return target_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")


@router.put("/{target_id}", tags=["Users"])
async def update_user(target_id: int, user_data: UserUpdate, authorization: str = Header(None)):
    """UPDATE user - farmer can only update themselves"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'users', 'update')
        if user['role'] == 'farmer' and user_id != target_id:
            raise HTTPException(status_code=403, detail="Cannot update other users")
        target_user = UserQueries.get_user_by_id(target_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        UserQueries.update_user(target_id, name=user_data.name, email=user_data.email)
        updated = UserQueries.get_user_by_id(target_id)
        logger.info(f"User {user_id} updated profile of user {target_id}")
        return {"message": "User updated successfully", "user": updated}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.patch("/{target_id}/cell", tags=["Users"])
async def update_user_cell(target_id: int, update_data: UserCellUpdate, authorization: str = Header(None)):
    """UPDATE single cell in user - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        RoleBasedAccessControl.check_permission(user_id, 'users', 'update')
        target_user = UserQueries.get_user_by_id(target_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        UserQueries.update_user_cell(target_id, update_data.column_name, update_data.value)
        logger.info(f"User {user_id} updated cell {update_data.column_name} of user {target_id}")
        return {
            "message": f"User {update_data.column_name} updated successfully",
            "user_id": target_id,
            "column": update_data.column_name,
            "new_value": update_data.value
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Update user cell error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.delete("/{target_id}", tags=["Users"])
async def delete_user(target_id: int, authorization: str = Header(None)):
    """DELETE user - admin only"""
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Unauthorized")
        user_id = extract_user_id(authorization)
        user = RoleBasedAccessControl.check_permission(user_id, 'users', 'delete')
        if user['role'] != 'admin':
            raise HTTPException(status_code=403, detail="Only admins can delete users")
        target_user = UserQueries.get_user_by_id(target_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        if target_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        UserQueries.delete_user(target_id)
        logger.info(f"User {user_id} deleted user {target_id}")
        return {"message": "User deleted successfully", "deleted_user_id": target_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")