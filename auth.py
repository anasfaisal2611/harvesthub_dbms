from jose import jwt
from datetime import timedelta,datetime
from database.database import SessionLocal
from database.database import get_db
from database.queries import UserQueries
import models
from schemas import UserCreate,UserLogin
from fastapi import HTTPException,status
import logging
import bcrypt
import os
logger = logging.getLogger(__name__)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"

def create_access_token(identity: str, additional_claims: dict, expires_delta: timedelta):
    payload = {"sub": identity, "exp": datetime.utcnow() + expires_delta, **additional_claims}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

ROLE_PERMISSIONS={
    'admin':{
        'users':['create','read','update','delete'],
        'regions':['create','read','update','delete'],
        'fields':['create','read','update','delete'],
        'crop_cycles':['create','read','update','delete'],
        'satellites':['create','read','update','delete'],
        'observations':['create','read','update','delete'],
        'band_values':['create','read','update','delete'],
        'weather':['create','read','update','delete'],
        'derived_metrics':['create','read','update','delete'],
        'alerts':['create','read','update','delete'], },
    'agronomist':{
        'users': ['read'],
        'regions': ['read'],
        'fields': ['read', 'update'],
        'crop_cycles': ['create', 'read', 'update'],
        'satellites': ['read'],
        'observations': ['read'],
        'band_values': ['read'],
        'weather': ['read'],
        'derived_metrics': ['read'],
        'alerts': ['create', 'read', 'update'],
    },

    'farmer':{
        'users': ['read'],
        'regions': ['read'],
        'fields': ['read', 'update'],
        'crop_cycles': ['read', 'update'],
        'satellites': ['read'],
        'observations': ['read'],
        'band_values': ['read'],
        'weather': ['read'],
        'derived_metrics': ['read'],
        'alerts': ['read'],
    }
}

class RoleBasedAccessControl:
    @staticmethod
    def check_permission(user_id, resource, action):
        # db = SessionLocal()
        db= get_db()
        try:
            user = UserQueries.get_user_by_id(user_id)  # ✅ fixed: use query class instead of raw session
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            if not user.get("is_active"):
                raise HTTPException(status_code=403, detail="Account disabled")
            user_role = user.get("role")
            if user_role not in ROLE_PERMISSIONS:
                raise HTTPException(status_code=403, detail=f"Unknown role: {user_role}")
            user_perms = ROLE_PERMISSIONS[user_role]
            if resource not in user_perms:
                raise HTTPException(status_code=403, detail=f"Access to {resource} not allowed")
            if action not in user_perms[resource]:
                raise HTTPException(status_code=403, detail=f"Cannot {action} on {resource}")
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authorization error: {str(e)}")
            raise HTTPException(status_code=500, detail="Authorization check failed")
        

    @staticmethod
    def is_admin(user_id):
        db = get_db()
        try:
            user = UserQueries.get_user_by_id(user_id)  # ✅ fixed: use query class instead of raw session
            return user and user.get("role") == "admin"
        except Exception as e:
            logger.error(f"Error checking admin status: {str(e)}")
            raise HTTPException(status_code=500, detail="Error occurred while checking admin status")

    @staticmethod
    def is_agronomist(user_id):
        db = get_db()
        try:
            user = UserQueries.get_user_by_id(user_id)  # ✅ fixed: use query class instead of raw session
            return user and user.get("role") == "agronomist"
        except Exception as e:
            logger.error(f"Error checking agronomist status: {str(e)}")
            raise HTTPException(status_code=500, detail="Error occurred while checking agronomist status")

    @staticmethod 
    def is_farmer(user_id):
        db=get_db()
        try:
            user = UserQueries.get_user_by_id(user_id)  # ✅ fixed: use query class instead of raw session
            return user and user.get("role") == "farmer"
        except Exception as e:
            logger.error(f"Error checking farmer status: {str(e)}")
            raise HTTPException(status_code=500, detail="Error occurred while checking farmer status")
    @staticmethod
    def get_permissions_for_role(role: str) -> dict:
        """Get all permissions for a role"""
        return ROLE_PERMISSIONS.get(role, {})

class AuthService:
    @staticmethod
    def hash_password(password: str):
        try:

            salt = bcrypt.gensalt()
            hashed=bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
            return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
        except Exception as e:
            logger.error(f"Password hashing error: {str(e)}")
            raise 
    @staticmethod
    def verify_password(password, hashed_password):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False

        

    @staticmethod
    def register(user_data: UserCreate):
        db = get_db()
        try:
            existing_user = db.query(models.User).filter_by(email=user_data.email).first()
            if existing_user:
                raise HTTPException(status_code=409, detail=f"Email {user_data.email} already registered")  # ✅ fixed
            valid_roles = ["farmer", "agronomist", "admin"]
            if user_data.role not in valid_roles:
                raise HTTPException(status_code=400, detail="Invalid role")
            user = models.User(
                name=user_data.name,
                email=user_data.email,
                role=user_data.role,
                is_active=True
            )
            user.password_hash = AuthService.hash_password(user_data.password)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"User registered: {user.name}, role: {user.role}")
            return {"user": user}, 201
        except HTTPException:  # ✅ fixed — re-raise instead of swallowing
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(status_code=400, detail="Registration failed")
        finally:
            db.close()

    @staticmethod
    def login(email: str, password: str):
        db = get_db()
        try:
            user = UserQueries.get_user_by_email(email)  # ✅ fixed: use query class instead of raw session
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")  # ✅ fixed: detail not details
            if not user.get("is_active"):
                raise HTTPException(status_code=403, detail="Account disabled")     # ✅ fixed
            if not AuthService.verify_password(password, user.get("password_hash")):
                raise HTTPException(status_code=401, detail="Invalid credentials")  # ✅ fixed
            access_token = create_access_token(
                identity=str(user.get("user_id")),
                additional_claims={"role": user.get("role")},
                expires_delta=timedelta(hours=24)
            )
            logger.info(f"User logged in: {email}, role: {user.get("role")}")
            return {"access_token": access_token, "user": user}, 200
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(status_code=400, detail="Login failed")
     