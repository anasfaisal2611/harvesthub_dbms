# routes/auth.py
# Authentication routes with raw DML queries and RBAC

import email

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from database.queries import UserQueries
from auth import AuthService, RoleBasedAccessControl,create_access_token
from routes.helpers import extract_user_id

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ PYDANTIC SCHEMAS ============

class UserRegister(BaseModel):
    """User registration schema"""
    name: str
    email: str
    password: str
    role: str  # farmer, agronomist, admin

class UserLogin(BaseModel):
    """User login schema"""
    email: str
    password: str

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str
    user_id: int
    email: str
    role: str

class UserResponse(BaseModel):
    """User response schema"""
    user_id: int
    name: str
    email: str
    role: str
    is_active: bool

# ============ AUTHENTICATION ROUTES ============

@router.post("/register", status_code=201, tags=["Authentication"])
async def register(user_data: UserRegister):
    """
    Register new user - INSERT operation
    
    Args:
        user_data: User registration data
    
    Returns:
        User details with status 201
    """
    try:
        if not user_data.name or len(user_data.name) < 2:
            raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
        if not user_data.email or "@" not in user_data.email:
            raise HTTPException(status_code=400, detail="Invalid email format")
        if not user_data.password or len(user_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        valid_roles = ['farmer', 'agronomist', 'admin']
        if user_data.role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Role must be one of: {', '.join(valid_roles)}")

        existing_user = UserQueries.get_user_by_email(user_data.email)
        if existing_user:
            logger.warning(f"Registration failed: Email {user_data.email} already registered")
            raise HTTPException(
                status_code=409,
                detail=f"User with email {user_data.email} already exists"
            )

        password_hash = AuthService.hash_password(user_data.password)

        result = UserQueries.create_user(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,
            role=user_data.role
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create user")

        logger.info(f"User registered: {user_data.email} (role: {user_data.role})")

        return {
            "message": "User registered successfully",
            "user": {
                "user_id": result["user_id"],
                "email": result["email"],
                "role": result["role"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

@router.post("/login", tags=["Authentication"])
async def login(login_data: UserLogin):
    """
    Login user - SELECT operation
    
    Args:
        login_data: Email and password
    
    Returns:
        JWT token with user details
    """
    try:
        if not login_data.email:
            raise HTTPException(status_code=400, detail="Email is required")
        if not login_data.password:
            raise HTTPException(status_code=400, detail="Password is required")

        user = UserQueries.get_user_by_email(login_data.email)

        if not user:
            logger.warning(f"Login failed: User {login_data.email} not found")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not user.get('is_active'):
            logger.warning(f"Login failed: User {login_data.email} is inactive")
            raise HTTPException(status_code=403, detail="Account is disabled")

        if not AuthService.verify_password(login_data.password, user['password_hash']):
            logger.warning(f"Login failed: Invalid password for {login_data.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        from datetime import timedelta
        access_token = create_access_token(
            identity=str(user['user_id']),
            additional_claims={"role": user['role']},
            expires_delta=timedelta(hours=24)
        )

        logger.info(f"User logged in: {login_data.email}, role: {user.get('role')}")
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "user": {
                "user_id": user['user_id'],
                "name": user.get('name'),
                "email": user['email'],
                "role": user['role'],
                "avatar_url": user.get('avatar_url')
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=400, detail="Login failed")

@router.get("/me", tags=["Authentication"])
async def get_current_user(authorization: str = None):
    """
    Get current user details using token extraction helper
    
    Args:
        authorization: JWT token in header
    
    Returns:
        User details
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        user_id = extract_user_id(authorization)
        user = UserQueries.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "user": {
                "user_id": user['user_id'],
                "name": user['name'],
                "email": user['email'],
                "role": user['role'],
                "is_active": user['is_active'],
                "avatar_url": user.get('avatar_url')
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")

@router.post("/validate-token", tags=["Authentication"])
async def validate_token(token: str):
    """
    Validate JWT token using extraction helper
    
    Args:
        token: JWT token
    
    Returns:
        Token validity and claims
    """
    try:
        user_id = extract_user_id(f"Bearer {token}")
        return {"valid": True, "user_id": user_id}
    except HTTPException:
        raise

@router.get("/permissions/{role}", tags=["Authentication"])
async def get_role_permissions(role: str):
    """
    Get permissions for a role
    
    Args:
        role: Role name (farmer, agronomist, admin)
    
    Returns:
        Role permissions
    """
    try:
        permissions = RoleBasedAccessControl.get_permissions_for_role(role)

        if not permissions:
            raise HTTPException(status_code=404, detail="Role not found")

        return {"role": role, "permissions": permissions}
    except HTTPException:
        raise

@router.get("/test", tags=["Authentication"])
async def test_auth():
    """Test authentication endpoint"""
    return {
        "message": "Authentication routes working!",
        "endpoints": {
            "register": "POST /api/auth/register",
            "login": "POST /api/auth/login",
            "me": "GET /api/auth/me",
            "validate_token": "POST /api/auth/validate-token",
            "permissions": "GET /api/auth/permissions/{role}",
            "test": "GET /api/auth/test"
        }
    }