"""
JWT Authentication & Authorization Middleware
Handles user authentication, token generation, and permission checks
"""

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List
import os
from pydantic import BaseModel

from apps.api.rbac import User, Permission, Role, DEMO_USERS


# ============================================
# Configuration
# ============================================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "nexus_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# ============================================
# Models
# ============================================

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    roles: List[str] = []


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


# ============================================
# Password Hashing
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


# ============================================
# User Database (Demo - Replace with real DB)
# ============================================

# Demo password hashes (all passwords are "password123")
DEMO_PASSWORD_HASH = get_password_hash("password123")

USER_DB = {
    "admin": {
        "username": "admin",
        "email": "admin@nexus.com",
        "hashed_password": DEMO_PASSWORD_HASH,
        "roles": ["admin"],
        "active": True,
    },
    "engineer": {
        "username": "engineer",
        "email": "engineer@nexus.com",
        "hashed_password": DEMO_PASSWORD_HASH,
        "roles": ["data_engineer"],
        "active": True,
    },
    "scientist": {
        "username": "scientist",
        "email": "scientist@nexus.com",
        "hashed_password": DEMO_PASSWORD_HASH,
        "roles": ["data_scientist"],
        "active": True,
    },
    "analyst": {
        "username": "analyst",
        "email": "analyst@nexus.com",
        "hashed_password": DEMO_PASSWORD_HASH,
        "roles": ["analyst"],
        "active": True,
    },
    "viewer": {
        "username": "viewer",
        "email": "viewer@nexus.com",
        "hashed_password": DEMO_PASSWORD_HASH,
        "roles": ["viewer"],
        "active": True,
    },
    "api_client": {
        "username": "api_client",
        "email": "client@external.com",
        "hashed_password": DEMO_PASSWORD_HASH,
        "roles": ["api_client"],
        "active": True,
    },
}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user with username and password"""
    user = USER_DB.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user


def get_user(username: str) -> Optional[User]:
    """Get user by username"""
    user_dict = USER_DB.get(username)
    if not user_dict:
        return None
    
    return User(
        username=user_dict["username"],
        email=user_dict["email"],
        roles=[Role(role) for role in user_dict["roles"]],
        active=user_dict["active"],
    )


# ============================================
# JWT Token Functions
# ============================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        roles: List[str] = payload.get("roles", [])
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(username=username, roles=roles)
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================
# Authentication Dependencies
# ============================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    user = get_user(token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


# ============================================
# Permission-Based Dependencies
# ============================================

class PermissionChecker:
    """Dependency to check if user has required permissions"""
    
    def __init__(self, required_permissions: List[Permission]):
        self.required_permissions = required_permissions
    
    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        """Check if user has required permissions"""
        for permission in self.required_permissions:
            if not user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission.value}"
                )
        return user


class RoleChecker:
    """Dependency to check if user has required roles"""
    
    def __init__(self, required_roles: List[Role]):
        self.required_roles = required_roles
    
    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        """Check if user has required roles"""
        user_roles = set(user.roles)
        required_roles = set(self.required_roles)
        
        if not user_roles.intersection(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role. Required one of: {[r.value for r in self.required_roles]}"
            )
        return user


# ============================================
# Convenience Functions
# ============================================

def require_permissions(*permissions: Permission):
    """Decorator to require specific permissions"""
    return Depends(PermissionChecker(list(permissions)))


def require_roles(*roles: Role):
    """Decorator to require specific roles"""
    return Depends(RoleChecker(list(roles)))


# ============================================
# Login Endpoint Handler
# ============================================

async def login_for_access_token(login_data: LoginRequest) -> Token:
    """Authenticate user and return JWT token"""
    user = authenticate_user(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "roles": user["roles"],
            "email": user["email"],
        },
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# ============================================
# Audit Logging
# ============================================

class AuditLog(BaseModel):
    """Audit log entry"""
    timestamp: datetime
    username: str
    action: str
    resource: str
    success: bool
    ip_address: Optional[str] = None


def log_audit_event(
    user: User,
    action: str,
    resource: str,
    success: bool = True,
    ip_address: Optional[str] = None
):
    """Log an audit event (implement with database/logging system)"""
    audit_entry = AuditLog(
        timestamp=datetime.utcnow(),
        username=user.username,
        action=action,
        resource=resource,
        success=success,
        ip_address=ip_address
    )
    
    # TODO: Store in audit log database/Kafka topic
    # For now, just log to console
    import logging
    logger = logging.getLogger("audit")
    logger.info(f"AUDIT: {audit_entry.model_dump_json()}")
