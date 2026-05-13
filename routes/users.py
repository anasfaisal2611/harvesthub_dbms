# routes/users.py
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
import logging

from database.queries import UserQueries
from auth import RoleBasedAccessControl
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

AVATAR_DIR = Path(__file__).resolve().parents[1] / "uploads" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
MAX_AVATAR_BYTES = 5 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


# ============ SCHEMAS ============

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


class UserCellUpdate(BaseModel):
    column_name: str
    value: str


def _ensure_authorized_user(authorization: str, action: str = "read"):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = extract_user_id(authorization)
    user = RoleBasedAccessControl.check_permission(user_id, "users", action)
    return user_id, user


def _ensure_self_or_admin(current_user_id: int, current_user: dict, target_id: int):
    if current_user["role"] != "admin" and current_user_id != target_id:
        raise HTTPException(status_code=403, detail="You can only manage your own profile")


def _build_avatar_url(filename: str) -> str:
    return f"/media/avatars/{filename}"


def _delete_avatar_file(avatar_url: Optional[str]):
    if not avatar_url or not avatar_url.startswith("/media/avatars/"):
        return
    file_path = AVATAR_DIR / avatar_url.split("/media/avatars/", 1)[1]
    try:
        if file_path.exists():
            file_path.unlink()
    except OSError as exc:
        logger.warning(f"Could not remove avatar file {file_path.name}: {exc}")


# ============ ROUTES ============

@router.get("/", tags=["Users"])
async def get_all_users(authorization: str = Header(None)):
    """GET all users - admin and agronomist see all, farmer sees only themselves"""
    try:
        user_id, user = _ensure_authorized_user(authorization, "read")
        if user["role"] in ["admin", "agronomist"]:
            users = UserQueries.get_all_users()
            visibility = "all users"
        else:
            users = [UserQueries.get_user_by_id(user_id)]
            visibility = "own profile only"
        logger.info(f"User {user_id} ({user['role']}) retrieved {len(users)} users")
        return {"count": len(users), "user_role": user["role"], "visibility": visibility, "users": users}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@router.get("/me", tags=["Users"])
async def get_my_profile(authorization: str = Header(None)):
    """GET current user's profile"""
    try:
        user_id, _ = _ensure_authorized_user(authorization, "read")
        profile = UserQueries.get_user_by_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get my profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")


@router.post("/me/avatar", tags=["Users"])
async def upload_my_avatar(avatar: UploadFile = File(...), authorization: str = Header(None)):
    """Upload or replace current user's avatar"""
    try:
        user_id, _ = _ensure_authorized_user(authorization, "update")
        user = UserQueries.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        content_type = (avatar.content_type or "").lower()
        ext = ALLOWED_AVATAR_TYPES.get(content_type)
        if not ext:
            raise HTTPException(status_code=400, detail="Only JPG, PNG, WEBP, and GIF images are allowed")

        data = await avatar.read()
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if len(data) > MAX_AVATAR_BYTES:
            raise HTTPException(status_code=400, detail="Avatar image must be 5MB or smaller")

        filename = f"user_{user_id}_{uuid4().hex}{ext}"
        avatar_path = AVATAR_DIR / filename
        avatar_path.write_bytes(data)

        _delete_avatar_file(user.get("avatar_url"))
        avatar_url = _build_avatar_url(filename)
        UserQueries.set_user_avatar(user_id, avatar_url)
        updated = UserQueries.get_user_by_id(user_id)

        logger.info(f"User {user_id} uploaded a new avatar")
        return {"message": "Avatar uploaded successfully", "user": updated}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload avatar")


@router.delete("/me/avatar", tags=["Users"])
async def delete_my_avatar(authorization: str = Header(None)):
    """Remove current user's avatar"""
    try:
        user_id, _ = _ensure_authorized_user(authorization, "update")
        user = UserQueries.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        _delete_avatar_file(user.get("avatar_url"))
        UserQueries.set_user_avatar(user_id, None)
        updated = UserQueries.get_user_by_id(user_id)

        logger.info(f"User {user_id} removed their avatar")
        return {"message": "Avatar removed successfully", "user": updated}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar remove error: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove avatar")


@router.get("/{target_id}", tags=["Users"])
async def get_user_by_id(target_id: int, authorization: str = Header(None)):
    """GET user by ID - farmer can only view themselves"""
    try:
        user_id, user = _ensure_authorized_user(authorization, "read")
        if user["role"] == "farmer" and user_id != target_id:
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
    """UPDATE user - admin can update any user, others can only update themselves"""
    try:
        user_id, user = _ensure_authorized_user(authorization, "update")
        _ensure_self_or_admin(user_id, user, target_id)

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
        user_id, user = _ensure_authorized_user(authorization, "update")
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can edit user cells")

        target_user = UserQueries.get_user_by_id(target_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        UserQueries.update_user_cell(target_id, update_data.column_name, update_data.value)
        logger.info(f"User {user_id} updated cell {update_data.column_name} of user {target_id}")
        return {
            "message": f"User {update_data.column_name} updated successfully",
            "user_id": target_id,
            "column": update_data.column_name,
            "new_value": update_data.value,
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
        user_id, user = _ensure_authorized_user(authorization, "delete")
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only admins can delete users")
        target_user = UserQueries.get_user_by_id(target_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        if target_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")

        _delete_avatar_file(target_user.get("avatar_url"))
        UserQueries.delete_user(target_id)
        logger.info(f"User {user_id} deleted user {target_id}")
        return {"message": "User deleted successfully", "deleted_user_id": target_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")