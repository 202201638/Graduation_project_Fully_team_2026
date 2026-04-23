from datetime import UTC, datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

# Security configuration
DEFAULT_DEVELOPMENT_SECRET = "your-secret-key-here-change-in-production"
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_DEVELOPMENT_SECRET)
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


ACCESS_TOKEN_EXPIRE_MINUTES = _int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 30)

if APP_ENV in {"prod", "production"} and (
    not SECRET_KEY or SECRET_KEY == DEFAULT_DEVELOPMENT_SECRET or len(SECRET_KEY) < 32
):
    raise RuntimeError(
        "SECRET_KEY must be set to a strong unique value when APP_ENV=production."
    )

# Use bcrypt directly for better compatibility
def hash_password(password: str) -> str:
    """Hash password using bcrypt directly"""
    # Truncate password to 72 bytes if longer (bcrypt limitation)
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        # Truncate plain password to 72 bytes if longer
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
        
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

# Keep passlib as fallback
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return hash_password(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def generate_user_id() -> str:
    """Generate a unique user ID"""
    import uuid
    return f"USR_{uuid.uuid4().hex[:12].upper()}"

def generate_patient_id() -> str:
    """Generate a unique patient ID"""
    import uuid
    return f"PAT_{uuid.uuid4().hex[:12].upper()}"

def generate_analysis_id() -> str:
    """Generate a unique analysis ID"""
    import uuid
    return f"ANA_{uuid.uuid4().hex[:12].upper()}"
